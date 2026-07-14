#!/usr/bin/env python3
"""
fetch_bots.py - Fetch live metadata from telegram.me preview pages.

Strictly per SPEC:
- Only use https://telegram.me/<username> (never t.me)
- Polite: default sleep 2s, --sleep >=1 enforced
- 429 -> backoff 30s + retry
- Network errors retry 3x with 2/4/8s
- Parse fields from real DOM positions as documented
- Idempotent: do not bump fetched_at if core data unchanged
- Update only fetch.* ; never touch artificial fields
- --dry-run : print only, no write
- For M2: support --id to test small sample
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "bots.json"
PREVIEW_BASE = "https://telegram.me"
DEFAULT_SLEEP = 2.0
MIN_SLEEP = 1.0
RETRY_BACKOFF = [2, 4, 8]
RETRY_429 = 30

# Headers to be polite and avoid simple blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def normalize_id(raw: str) -> str:
    """Turn @foo, Foo, https://telegram.me/foo into clean id."""
    s = raw.strip().lower()
    s = re.sub(r"^https?://(telegram\.me|t\.me)/", "", s)
    s = s.lstrip("@")
    return s


def parse_number(raw: str) -> Optional[int]:
    """Remove spaces, commas, &nbsp; etc and int()."""
    if not raw:
        return None
    cleaned = re.sub(r"[\s,\u00a0\u202f]+", "", raw)
    try:
        return int(cleaned)
    except ValueError:
        return None


def parse_extra(raw: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Parse tgme_page_extra text.
    Returns (type, monthly_users)
    bot -> 'monthly users'
    channel -> 'subscribers'
    group -> 'members'
    """
    if not raw:
        return None, None
    text = raw.strip().lower()

    m = re.search(r"([\d\s,\u00a0\u202f]+)\s*(monthly users|subscribers|members)", text)
    if not m:
        return None, None

    num_str, kind = m.groups()
    num = parse_number(num_str)
    if "monthly" in kind:
        return "bot", num
    elif "subscriber" in kind:
        return "channel", num
    elif "member" in kind:
        return "group", num
    return None, num


def clean_description(desc_html: str) -> str:
    """Turn description HTML into plain-ish text (br -> \n, drop links markup).
    Preserves newlines from <br>, collapses only horizontal whitespace.
    Must be passed inner HTML (no outer <div>).
    """
    if not desc_html:
        return ""
    # Replace common breaks
    text = re.sub(r"<br\s*/?>", "\n", desc_html, flags=re.I)
    text = re.sub(r"</?a[^>]*>", "", text, flags=re.I)  # drop link tags, keep text
    # Collapse runs of spaces/tabs but preserve \n for multi-line descriptions
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def parse_preview(html: str) -> Dict[str, Any]:
    """
    Extract fields per §1.1 of SPEC.
    Returns partial fetch dict (without status/http/fetched_at).
    """
    soup = BeautifulSoup(html, "html.parser")

    title_div = soup.find("div", class_="tgme_page_title")
    if not title_div:
        # Likely dead / error page
        return {"status_hint": "dead"}

    # verified
    is_verified = bool(title_div.find("i", class_="verified-icon"))

    # title text (display name)
    title = title_div.get_text(strip=True)
    # remove the checkmark char if present in text
    title = re.sub(r"\s*✔\s*$", "", title).strip()

    desc_div = soup.find("div", class_="tgme_page_description")
    if desc_div:
        # Use inner HTML only (strip outer <div class="tgme_page_description">...</div>)
        # decode_contents gives children HTML without the wrapper tag.
        inner_html = desc_div.decode_contents()
        description = clean_description(inner_html)
    else:
        description = ""

    # telegram.me preview pages contain TWO tgme_page_extra divs:
    # [0] is the deep link banner e.g. "@username"
    # [1] (or the matching one) contains the real "299 956 monthly users" / subscribers / members
    extras = soup.find_all("div", class_="tgme_page_extra")
    extra_raw = None
    matched_extra = None
    for e in extras:
        txt = e.get_text(strip=True)
        if re.search(r"[\d\s,\u00a0\u202f]+\s*(monthly users|subscribers|members)", txt, re.I):
            matched_extra = txt
            break
    if matched_extra:
        extra_raw = matched_extra
    else:
        # No monthly/sub/members text found: extra_raw=None (per spec guidance)
        # (first extra text kept only for debug; not stored in extra_raw)
        extra_raw = None

    typ, monthly = parse_extra(extra_raw or "")

    photo_url = None
    img = soup.find("img", class_="tgme_page_photo_image")
    if img and img.get("src"):
        photo_url = img["src"]

    # If no extra but title exists -> probably a user or bot without public count
    if not typ and title_div:
        # default to bot when we see a bot-looking page (heuristic: has start button area or just title)
        # We keep "unknown" if we cannot tell
        typ = "unknown"

    return {
        "title": title or None,
        "description": description or None,
        "extra_raw": extra_raw,
        "monthly_users": monthly,
        "type": typ,
        "is_verified": is_verified,
        "photo_url": photo_url,
        "status_hint": "ok",
    }


def fetch_one(username: str, sleep_sec: float) -> Dict[str, Any]:
    """
    Fetch single bot preview page. Returns fetch sub-object ready to merge.
    """
    url = f"{PREVIEW_BASE}/{username}"
    result = {
        "status": "error",
        "http_code": None,
        "fetched_at": None,
        "title": None,
        "description": None,
        "extra_raw": None,
        "monthly_users": None,
        "type": None,
        "is_verified": None,
        "photo_url": None,
        "error_msg": None,
    }

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            result["http_code"] = resp.status_code

            if resp.status_code == 200:
                parsed = parse_preview(resp.text)
                if parsed.get("status_hint") == "dead":
                    result["status"] = "dead"
                else:
                    result["status"] = "ok"
                    result.update({k: parsed.get(k) for k in ("title", "description", "extra_raw", "monthly_users", "type", "is_verified", "photo_url")})
                result["fetched_at"] = datetime.now(timezone.utc).isoformat()
                time.sleep(sleep_sec)
                return result

            elif resp.status_code == 404:
                result["status"] = "dead"
                result["fetched_at"] = datetime.now(timezone.utc).isoformat()
                time.sleep(sleep_sec)
                return result

            elif resp.status_code == 429:
                print(f"  [429] rate limited, sleeping {RETRY_429}s ...")
                time.sleep(RETRY_429)
                continue

            else:
                # Other 4xx/5xx -> error, keep old data later
                result["error_msg"] = f"http {resp.status_code}"
                time.sleep(sleep_sec)
                return result

        except requests.RequestException as e:
            result["error_msg"] = str(e)
            if attempt < 2:
                back = RETRY_BACKOFF[attempt]
                print(f"  [retry {attempt+1}/3] network error, sleep {back}s: {e}")
                time.sleep(back)
            else:
                time.sleep(sleep_sec)
                return result

    # exhausted
    return result


def load_data() -> Dict[str, Any]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: Dict[str, Any]) -> None:
    # Pretty but stable: indent 2, ensure trailing newline
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fetch_fields_equal(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """Compare meaningful fetch fields for idempotency (ignore time and http_code sometimes)."""
    keys = ("status", "title", "description", "extra_raw", "monthly_users", "type", "is_verified", "photo_url")
    for k in keys:
        if a.get(k) != b.get(k):
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Fetch telegram.me metadata into data/bots.json")
    parser.add_argument("--id", help="Only fetch this single id/username (for M2 sample)")
    parser.add_argument("--dry-run", action="store_true", help="Print results, do not write file")
    parser.add_argument("--force", action="store_true", help="Ignore existing ok/pending, re-fetch everything selected")
    parser.add_argument("--sleep", type=float, default=DEFAULT_SLEEP, help="Seconds between requests (min 1.0)")
    args = parser.parse_args()

    sleep_sec = max(args.sleep, MIN_SLEEP)

    data = load_data()
    bots = data.get("bots", [])
    now_iso = datetime.now(timezone.utc).isoformat()

    targets = []
    if args.id:
        target_id = normalize_id(args.id)
        for b in bots:
            if b["id"] == target_id or normalize_id(b["username"]) == target_id:
                targets.append(b)
                break
        if not targets:
            print(f"ERROR: id '{args.id}' not found in bots.json")
            sys.exit(2)
    else:
        # Default: pending or force or old ones. For M2/M3 we start with pending.
        for b in bots:
            f = b.get("fetch", {})
            if args.force or f.get("status") in (None, "pending", "error"):
                targets.append(b)

    print(f"Will fetch {len(targets)} bot(s). sleep={sleep_sec}s dry_run={args.dry_run}")

    updated_count = 0
    ok_count = 0
    dead_count = 0
    err_count = 0
    last_success = data.get("last_fetched_at")

    for i, bot in enumerate(targets):
        uname = bot["username"].lstrip("@")
        print(f"[{i+1}/{len(targets)}] fetching {bot['id']} ({uname}) ...")
        new_fetch = fetch_one(uname, sleep_sec)

        old_fetch = bot.get("fetch", {})
        core_changed = not fetch_fields_equal(old_fetch, new_fetch)

        # Always write status/http_code/error; only bump fetched_at on change or first time
        merged = dict(old_fetch)  # start from old to preserve fetched_at when possible
        merged.update({k: new_fetch.get(k) for k in ("status", "http_code", "title", "description", "extra_raw", "monthly_users", "type", "is_verified", "photo_url", "error_msg")})

        if new_fetch.get("fetched_at"):
            if core_changed or old_fetch.get("status") != new_fetch.get("status") or not old_fetch.get("fetched_at"):
                merged["fetched_at"] = new_fetch["fetched_at"]
            # else keep old fetched_at for idempotency

        bot["fetch"] = merged

        status = merged.get("status")
        if status == "ok":
            ok_count += 1
            mu = merged.get("monthly_users")
            mu_str = f"{mu:,}" if mu else "?"
            print(f"  [ok] {bot['id']:<18} {mu_str} users  title={merged.get('title')}")
            last_success = merged["fetched_at"]
        elif status == "dead":
            dead_count += 1
            print(f"  [dead] {bot['id']}")
        else:
            err_count += 1
            print(f"  [err] {bot['id']} {merged.get('error_msg') or merged.get('http_code')}")

        updated_count += 1

    # Global timestamps
    if last_success:
        data["last_fetched_at"] = last_success
    # last_verified_label left to human or render step

    print(f"\nSummary: ok={ok_count} dead={dead_count} err={err_count} total_processed={updated_count}")

    if args.dry_run:
        print("DRY-RUN: no file written.")
        return

    if updated_count > 0:
        save_data(data)
        print(f"Wrote {DATA_FILE}")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()

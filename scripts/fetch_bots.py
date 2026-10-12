#!/usr/bin/env python3
"""
fetch_bots.py - Fetch live metadata from t.me preview pages.

Strictly per SPEC:
- Use https://t.me/<username> preview pages
- Polite: default sleep 2s, --sleep >=1 enforced
- 429 -> backoff 30s + retry
- Network errors retry 3x with 2/4/8s
- Parse fields from real DOM positions as documented
- Idempotent: do not bump fetched_at if core data unchanged
- Update only fetch.* ; never touch artificial fields
- --dry-run : print only, no write
- --id : fetch a single entry
- Default: re-fetch EVERY entry (ok / dead / error / pending) each run
- Dead detection is conservative:
    * only the generic "Telegram: Contact @x" page (no tgme_page_title) or
      HTTP 404 counts as a dead observation; any other title-less page is an
      "error" (ambiguous / blocked / interstitial)
    * fetch.dead_streak counts consecutive dead observations; status only
      becomes "dead" once dead_streak >= DEAD_CONFIRM; render steps hide the
      entry from README/site once dead_streak >= HIDE_AFTER
    * any ok observation resets dead_streak to 0
- On error the previously stored fields are kept untouched (only error_msg
  is recorded)
- Page kind from the action button: "Start Bot" -> bot; "Send Message" ->
  user; "View in Telegram"/"Join ..." -> channel/group. fetch.not_bot is
  true when a live page is not a bot.
- After a successful run, last_fetched_at / last_verified_label are updated
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
PREVIEW_BASE = "https://t.me"
DEFAULT_SLEEP = 2.0
MIN_SLEEP = 1.0
RETRY_BACKOFF = [2, 4, 8]
RETRY_429 = 30
DEAD_CONFIRM = 2   # consecutive dead observations before status becomes "dead"
HIDE_AFTER = 3     # consecutive dead observations before hidden from README/site
MAX_ERROR_RATIO = 0.5  # above this, the run is treated as failed (nothing written)

# Headers to be polite and avoid simple blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def normalize_id(raw: str) -> str:
    """Turn @foo, Foo, https://t.me/foo into clean id."""
    s = raw.strip().lower()
    s = re.sub(r"^https?://(t\.me|telegram\.me)/", "", s)
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


def detect_page_kind(soup: BeautifulSoup, typ: Optional[str]) -> str:
    """Classify the preview page by its action button / extra text.

    "Start Bot" -> bot; "Send Message" -> user; "View in Telegram" / "Join ..." /
    "View Channel" -> channel or group (from extra text). Unknown otherwise.
    """
    btn = soup.find("a", class_="tgme_action_button_new")
    label = btn.get_text(strip=True).lower() if btn else ""
    if "start bot" in label:
        return "bot"
    if typ in ("channel", "group"):
        return typ
    if "send message" in label:
        return "user"
    if "join" in label or "view" in label:
        return "channel"
    return "unknown"


def is_generic_contact_page(soup: BeautifulSoup, username: Optional[str]) -> bool:
    """True for Telegram's generic 'Telegram: Contact @x' page (username not taken)."""
    html_title = soup.title.get_text(strip=True) if soup.title else ""
    if not html_title.lower().startswith("telegram: contact @"):
        return False
    desc = soup.find("div", class_="tgme_page_description")
    desc_text = desc.get_text(" ", strip=True).lower() if desc else ""
    if "you can contact" not in desc_text:
        return False
    if username:
        if html_title.lower() != f"telegram: contact @{username.lower()}":
            return False
    return True


def parse_preview(html: str, username: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract fields per §1.1 of SPEC.
    Returns partial fetch dict (without status/http/fetched_at).
    status_hint: "ok" | "dead" (generic contact page) | "ambiguous" (anything else w/o title)
    """
    soup = BeautifulSoup(html, "html.parser")

    title_div = soup.find("div", class_="tgme_page_title")
    if not title_div:
        if is_generic_contact_page(soup, username):
            return {"status_hint": "dead"}
        return {"status_hint": "ambiguous"}

    # verified
    is_verified = bool(title_div.find("i", class_="verified-icon"))

    # title text (display name)
    title = title_div.get_text(strip=True)
    # remove the checkmark char if present in text
    title = re.sub(r"\s*✔\s*$", "", title).strip()

    desc_div = soup.find("div", class_="tgme_page_description")
    if desc_div:
        # Use inner HTML only (strip outer <div class="tgme_page_description">...</div>)
        inner_html = desc_div.decode_contents()
        description = clean_description(inner_html)
    else:
        description = ""

    # t.me preview pages contain TWO tgme_page_extra divs:
    # [0] is the deep link banner e.g. "@username"
    # [1] (or the matching one) contains the real "299 956 monthly users" / subscribers / members
    extras = soup.find_all("div", class_="tgme_page_extra")
    extra_raw = None
    for e in extras:
        txt = e.get_text(strip=True)
        if re.search(r"[\d\s,\u00a0\u202f]+\s*(monthly users|subscribers|members)", txt, re.I):
            extra_raw = txt
            break

    typ, monthly = parse_extra(extra_raw or "")

    photo_url = None
    img = soup.find("img", class_="tgme_page_photo_image")
    if img and img.get("src"):
        photo_url = img["src"]

    page_kind = detect_page_kind(soup, typ)
    if not typ:
        typ = "bot" if page_kind == "bot" else (page_kind if page_kind != "unknown" else "unknown")

    return {
        "title": title or None,
        "description": description or None,
        "extra_raw": extra_raw,
        "monthly_users": monthly,
        "type": typ,
        "is_verified": is_verified,
        "photo_url": photo_url,
        "page_kind": page_kind,
        "not_bot": page_kind != "bot",
        "status_hint": "ok",
    }


DATA_KEYS = ("title", "description", "extra_raw", "monthly_users", "type",
             "is_verified", "photo_url", "page_kind", "not_bot")


def fetch_one(username: str, sleep_sec: float) -> Dict[str, Any]:
    """
    Fetch single bot preview page. Returns an observation:
      {"obs": "ok"|"dead"|"error", "http_code", "fetched_at", "error_msg", **DATA_KEYS}
    """
    url = f"{PREVIEW_BASE}/{username}"
    result: Dict[str, Any] = {"obs": "error", "http_code": None, "fetched_at": None, "error_msg": None}

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            result["http_code"] = resp.status_code

            if resp.status_code == 200:
                parsed = parse_preview(resp.text, username)
                hint = parsed.get("status_hint")
                if hint == "ok":
                    result["obs"] = "ok"
                    result.update({k: parsed.get(k) for k in DATA_KEYS})
                    result["fetched_at"] = datetime.now(timezone.utc).isoformat()
                elif hint == "dead":
                    result["obs"] = "dead"
                    result["fetched_at"] = datetime.now(timezone.utc).isoformat()
                else:
                    result["obs"] = "error"
                    result["error_msg"] = "ambiguous page (no tgme_page_title and not the generic contact page)"
                time.sleep(sleep_sec)
                return result

            elif resp.status_code == 404:
                result["obs"] = "dead"
                result["fetched_at"] = datetime.now(timezone.utc).isoformat()
                time.sleep(sleep_sec)
                return result

            elif resp.status_code == 429:
                print(f"  [429] rate limited, sleeping {RETRY_429}s ...")
                result["error_msg"] = "http 429"
                time.sleep(RETRY_429)
                continue

            else:
                # Other 4xx/5xx -> error, keep old data
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


def merge_observation(old: Dict[str, Any], obs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge one observation into the stored fetch object.

    - ok    : overwrite data fields, status=ok, dead_streak=0
    - dead  : dead_streak += 1; status=dead once streak >= DEAD_CONFIRM,
              otherwise previous status/fields are kept
    - error : keep every previous field; record error_msg only
              (status becomes "error" only if there was no previous result)
    fetched_at only moves when status or data fields actually change.
    """
    merged = dict(old)
    kind = obs["obs"]
    prev_status = old.get("status")

    if kind == "ok":
        merged["status"] = "ok"
        merged["http_code"] = obs.get("http_code")
        for k in DATA_KEYS:
            merged[k] = obs.get(k)
        merged["dead_streak"] = 0
        merged["error_msg"] = None
    elif kind == "dead":
        streak = int(old.get("dead_streak") or 0) + 1
        # migrate legacy entries already confirmed dead without a counter
        if prev_status == "dead" and not old.get("dead_streak"):
            streak = DEAD_CONFIRM
        merged["dead_streak"] = streak
        merged["error_msg"] = None
        if streak >= DEAD_CONFIRM:
            merged["status"] = "dead"
            merged["http_code"] = obs.get("http_code")
            for k in DATA_KEYS:
                merged[k] = None
        elif prev_status in (None, "pending", "error"):
            merged["status"] = "pending"
    else:  # error
        merged["error_msg"] = obs.get("error_msg") or (f"http {obs.get('http_code')}" if obs.get("http_code") else "error")
        if prev_status in (None, "pending"):
            merged["status"] = "error"
            merged["http_code"] = obs.get("http_code")

    merged.setdefault("dead_streak", 0)

    changed = merged.get("status") != prev_status or any(merged.get(k) != old.get(k) for k in DATA_KEYS)
    if obs.get("fetched_at") and (changed or not old.get("fetched_at")):
        merged["fetched_at"] = obs["fetched_at"]

    # stable key order
    order = ["status", "http_code", "fetched_at", "title", "description", "extra_raw",
             "monthly_users", "type", "is_verified", "photo_url", "page_kind", "not_bot",
             "dead_streak", "error_msg"]
    out = {k: merged.get(k) for k in order}
    for k, v in merged.items():
        if k not in out:
            out[k] = v
    return out


def main():
    parser = argparse.ArgumentParser(description="Fetch t.me metadata into data/bots.json")
    parser.add_argument("--id", help="Only fetch this single id/username")
    parser.add_argument("--dry-run", action="store_true", help="Print results, do not write file")
    parser.add_argument("--only-pending", action="store_true", help="Only fetch pending/error/new entries")
    parser.add_argument("--force", action="store_true", help="(kept for compatibility; full re-fetch is now the default)")
    parser.add_argument("--sleep", type=float, default=DEFAULT_SLEEP, help="Seconds between requests (min 1.0)")
    args = parser.parse_args()

    sleep_sec = max(args.sleep, MIN_SLEEP)

    data = load_data()
    bots = data.get("bots", [])

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
        for b in bots:
            if not b.get("url") or not b.get("username"):
                continue  # url=null prose placeholders
            f = b.get("fetch", {}) or {}
            if args.only_pending and f.get("status") not in (None, "pending", "error"):
                continue
            targets.append(b)

    print(f"Will fetch {len(targets)} bot(s). sleep={sleep_sec}s dry_run={args.dry_run}")

    counts = {"ok": 0, "dead": 0, "error": 0}
    not_bot_ids = []
    for i, bot in enumerate(targets):
        uname = bot["username"].lstrip("@")
        print(f"[{i+1}/{len(targets)}] fetching {bot['id']} ({uname}) ...")
        obs = fetch_one(uname, sleep_sec)
        counts[obs["obs"]] += 1

        old_fetch = bot.get("fetch", {}) or {}
        merged = merge_observation(old_fetch, obs)
        bot["fetch"] = merged

        if obs["obs"] == "ok":
            mu = merged.get("monthly_users")
            mu_str = f"{mu:,}" if mu else "?"
            flag = f"  NOT_BOT({merged.get('page_kind')})" if merged.get("not_bot") else ""
            print(f"  [ok] {bot['id']:<18} {mu_str} users  title={merged.get('title')}{flag}")
            if merged.get("not_bot"):
                not_bot_ids.append(bot["id"])
        elif obs["obs"] == "dead":
            print(f"  [dead obs] {bot['id']} streak={merged.get('dead_streak')} status={merged.get('status')}")
        else:
            print(f"  [err] {bot['id']} {merged.get('error_msg')} (previous data kept)")

    total = len(targets)
    print(f"\nSummary: ok={counts['ok']} dead={counts['dead']} err={counts['error']} total_processed={total}")
    if not_bot_ids:
        print(f"WARNING: live pages that are not bots: {', '.join(not_bot_ids)}")

    if total and counts["error"] / total > MAX_ERROR_RATIO:
        print(f"ERROR: {counts['error']}/{total} fetches failed (> {MAX_ERROR_RATIO:.0%}); "
              "treating run as failed, nothing written.")
        sys.exit(3)

    # Global timestamps: only a full (non --id, non --only-pending) successful run
    # counts as a verification of the whole list.
    if not args.id and not args.only_pending and counts["ok"] > 0:
        now = datetime.now(timezone.utc)
        data["last_fetched_at"] = now.isoformat()
        data["last_verified_label"] = now.strftime("%Y-%m")

    if args.dry_run:
        print("DRY-RUN: no file written.")
        return

    if total > 0:
        save_data(data)
        print(f"Wrote {DATA_FILE}")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()

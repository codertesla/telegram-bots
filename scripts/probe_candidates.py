#!/usr/bin/env python3
"""Ad-hoc probe: live metadata for candidate usernames (one-off research tool).

Reads usernames from argv or --file, fetches t.me preview pages with the same
parser as fetch_bots.py, prints TSV. Does not touch data/bots.json.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_bots import HEADERS, normalize_id, parse_preview  # noqa: E402

import requests

SLEEP = 1.2


def probe(username: str) -> dict:
    uid = normalize_id(username)
    url = f"https://t.me/{uid}"
    out = {"id": uid, "http": None, "kind": "", "mau": "", "verified": "", "title": "", "desc": ""}
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        out["http"] = r.status_code
        if r.status_code == 404:
            out["kind"] = "DEAD404"
            return out
        p = parse_preview(r.text, uid)
        hint = p.get("status_hint")
        if hint == "dead":
            out["kind"] = "DEAD"
            return out
        if hint == "ambiguous":
            out["kind"] = "AMBIG"
            return out
        out["kind"] = p.get("page_kind", "")
        out["mau"] = p.get("extra_raw") or ""
        out["verified"] = "V" if p.get("is_verified") else ""
        out["title"] = (p.get("title") or "").replace("\t", " ")[:60]
        out["desc"] = (p.get("description") or "").replace("\n", " ").replace("\t", " ")[:160]
    except Exception as exc:  # noqa: BLE001
        out["kind"] = "ERR"
        out["desc"] = str(exc)[:80]
    return out


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    usernames = args
    for a in sys.argv[1:]:
        if a.startswith("--file="):
            usernames += [l.strip() for l in Path(a.split("=", 1)[1]).read_text().splitlines() if l.strip() and not l.startswith("#")]
    print("id\thttp\tkind\tmau\tverified\ttitle\tdesc")
    for u in usernames:
        row = probe(u)
        print("\t".join(str(row[k]) for k in ("id", "http", "kind", "mau", "verified", "title", "desc")), flush=True)
        time.sleep(SLEEP)


if __name__ == "__main__":
    main()

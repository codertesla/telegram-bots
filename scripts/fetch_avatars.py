#!/usr/bin/env python3
"""
fetch_avatars.py - 把每个 bot 的 Telegram 头像一次性抓取到本地。

背景：data/bots.json 里 fetch.photo_url 指向 cdn*.telesco.pe 临时文件链接，
过期后大面积 404。改用 t.me 稳定头像端点按用户名实时取图，保存为静态文件：
    https://t.me/i/userpic/160/<username>.jpg
- 200 + image/jpeg : 真实头像，写入 docs/avatars/<username>.jpg
- 404（返回 42 字节 1x1 GIF 占位）: 无头像，跳过，构建时回退文字头像
- 网络错误：重试 3 次（2/4/8 秒退避）

规则：
- 只接受 JPEG 魔数（\\xff\\xd8）内容，杜绝把占位 GIF 当头像保存
- 幂等：内容不变不重写文件
- 默认清理 docs/avatars/ 中已不在 bots.json 内的孤儿文件
- 构建侧：build_site.py 检测到本地文件时优先输出 avatars/<username>.jpg

用法：
    .venv/bin/python scripts/fetch_avatars.py [--sleep 1] [--force]
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "bots.json"
AVATAR_DIR = ROOT / "docs" / "avatars"

USERPIC_URL = "https://t.me/i/userpic/160/{username}.jpg"
JPEG_MAGIC = b"\xff\xd8"
RETRY_DELAYS = (2, 4, 8)


def log(msg):
    print(msg, flush=True)


def fetch_avatar(username: str) -> bytes | None | str:
    """下载头像；有头像返回字节，确认无头像返回 None，网络失败返回 "error"。"""
    url = USERPIC_URL.format(username=username)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; telegram-bots-site)"})
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read()
            if body.startswith(JPEG_MAGIC):
                return body
            return None  # 404 占位 GIF / 非 JPEG：账号无自定义头像
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # 账号无自定义头像（t.me 返回占位 GIF）
            if attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
        except Exception:
            if attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
    return "error"


def main():
    parser = argparse.ArgumentParser(description="Fetch Telegram avatars into docs/avatars/")
    parser.add_argument("--sleep", type=float, default=1.0, help="每张之间的间隔秒数（礼貌抓取）")
    parser.add_argument("--force", action="store_true", help="内容相同也重写文件")
    args = parser.parse_args()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    bots = [b for b in data.get("bots", []) if b.get("username")]
    usernames = {str(b["username"]).lstrip("@") for b in bots}

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    saved = kept = skipped = failed = 0
    for bot in bots:
        username = str(bot["username"]).lstrip("@")
        body = fetch_avatar(username)
        out_file = AVATAR_DIR / f"{username}.jpg"
        if body == "error":
            failed += 1
            log(f"  !! network failure: {username}")
        elif body is None:
            out_file.unlink(missing_ok=True)  # 旧头像对应账号已无头像
            skipped += 1
        elif out_file.is_file() and not args.force and out_file.read_bytes() == body:
            kept += 1
        else:
            out_file.write_bytes(body)
            saved += 1
        time.sleep(args.sleep)

    pruned = 0
    for stale in AVATAR_DIR.glob("*.jpg"):
        if stale.stem not in usernames:
            stale.unlink()
            pruned += 1

    log(f"Avatars: {saved} saved, {kept} unchanged, {skipped} without avatar, {failed} failed, {pruned} pruned")
    log(f"  -> {AVATAR_DIR} ({sum(f.stat().st_size for f in AVATAR_DIR.glob('*.jpg')):,} bytes total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

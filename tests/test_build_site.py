import json
import re
import unittest
from pathlib import Path

from scripts.build_site import AVATAR_DIR, DATA_FILE, OUT_FILE, ROOT, bot_view, build_html, photo_url


class BuildSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        cls.html = build_html(cls.data)

    def test_build_is_deterministic(self):
        self.assertEqual(self.html, build_html(self.data))

    def test_page_references_external_assets(self):
        self.assertIn('<link rel="stylesheet" href="assets/style.css">', self.html)
        self.assertIn('<script src="assets/search.js"></script>', self.html)
        self.assertNotIn("<style>", self.html)
        self.assertTrue((ROOT / "docs" / "assets" / "style.css").is_file())
        self.assertTrue((ROOT / "docs" / "assets" / "search.js").is_file())

    def test_committed_page_is_up_to_date(self):
        self.assertEqual(OUT_FILE.read_text(encoding="utf-8"), self.html)


class AvatarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        cls.html = build_html(cls.data)

    def test_bot_view_prefers_local_avatar_snapshot(self):
        # docs/avatars/ 已由 fetch_avatars.py 生成；有快照时必须用相对本地路径
        snapshots = sorted(AVATAR_DIR.glob("*.jpg")) if AVATAR_DIR.is_dir() else []
        self.assertTrue(snapshots, "docs/avatars/ should contain fetched avatar snapshots")
        by_username = {b.get("username", "").lstrip("@"): b for b in self.data["bots"]}
        target = next(b for b in snapshots if b.stem in by_username)
        self.assertEqual(photo_url(by_username[target.stem]), f"avatars/{target.stem}.jpg")

    def test_bot_view_falls_back_to_https_photo_url(self):
        with_photo = [b for b in self.data["bots"]
                      if (b.get("fetch") or {}).get("photo_url")
                      and not (AVATAR_DIR / (b.get("username", "").lstrip("@") + ".jpg")).is_file()]
        if with_photo:
            bot = with_photo[0]
            self.assertEqual(bot_view(bot)["photo_url"], bot["fetch"]["photo_url"])

    def test_bot_view_rejects_non_https_photo_url(self):
        for bad in ("", "http://insecure.example/a.jpg", "javascript:alert(1)", None):
            bot = {"username": "@x", "fetch": {"photo_url": bad}}
            self.assertEqual(bot_view(bot)["photo_url"], "")

    def test_photo_url_renders_real_img(self):
        self.assertIn('<img class="avatar-img"', self.html)
        # 明确尺寸防布局偏移；首屏外 lazy；统一 async 解码与 no-referrer
        self.assertRegex(self.html, r'<img class="avatar-img" src="[^"]+" alt="" width="(?:36|44)" height="(?:36|44)"')
        self.assertIn('loading="lazy"', self.html)
        self.assertIn('decoding="async"', self.html)
        self.assertIn('referrerpolicy="no-referrer"', self.html)
        self.assertEqual(self.html.count('alt=""'), self.html.count('<img class="avatar-img"'))

    def test_local_avatars_referenced(self):
        # 有本地快照的 bot 必须引用本地路径，不得再用会过期的 telesco.pe 链接
        from scripts.build_site import is_hidden

        snapshot_users = {p.stem for p in AVATAR_DIR.glob("*.jpg")} if AVATAR_DIR.is_dir() else set()
        self.assertTrue(snapshot_users, "docs/avatars/ should contain fetched avatar snapshots")
        for b in self.data["bots"]:
            u = b.get("username", "").lstrip("@")
            if u in snapshot_users and not is_hidden(b):
                self.assertIn(f'src="avatars/{u}.jpg"', self.html)
        self.assertRegex(self.html, r'src="avatars/[A-Za-z0-9_]+\.jpg"')

    def test_first_screen_hero_avatar_is_not_lazy(self):
        # Hero 区域 Top 3 使用 eager 加载：不含 loading 属性
        hero = re.search(r'<aside class="hero-panel".*?</aside>', self.html, re.S).group(0)
        self.assertIn('<img class="avatar-img"', hero)
        self.assertNotIn('loading=', hero)

    def test_text_fallback_kept_alongside_img_and_without_url(self):
        # 无 photo_url 的 bot 只保留文字 fallback
        bot = {"username": "@no_photo_bot", "category": "tools", "notes": "n",
               "featured": False, "official": False, "fetch": {"status": "ok"}}
        html = build_html({"bots": [bot], "last_fetched_at": "2026-01-01T00:00:00Z"})
        self.assertNotIn('avatar-img', html)
        self.assertIn('avatar-fallback', html)
        self.assertIn("N", html)
        # 真实头像也内嵌文字 fallback，供加载失败时回退；每个头像恰好一个 fallback
        self.assertGreater(self.html.count("avatar-fallback"), 0)
        avatar_spans = (
            self.html.count('class="avatar"')
            + self.html.count('class="avatar avatar-small"')
        )
        self.assertEqual(self.html.count("avatar-fallback"), avatar_spans)

    def test_committed_page_matches_template_with_avatars(self):
        committed = OUT_FILE.read_text(encoding="utf-8")
        self.assertEqual(committed, self.html)
        self.assertEqual(
            committed.count('<img class="avatar-img"'),
            self.html.count('<img class="avatar-img"'),
        )


if __name__ == "__main__":
    unittest.main()

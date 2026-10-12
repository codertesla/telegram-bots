"""Offline tests for scripts/fetch_bots.py parsing + merge logic.

Run: python -m unittest discover -s tests
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fetch_bots as fb  # noqa: E402

BOT_PAGE = """<html><head><title>Telegram: Contact @demo_bot</title></head><body>
<div class="tgme_page_title" dir="auto"><span dir="auto">Demo Bot</span></div>
<div class="tgme_page_extra">@demo_bot</div>
<div class="tgme_page_extra">12 345 monthly users</div>
<div class="tgme_page_description">Line 1<br/>Line 2</div>
<a class="tgme_action_button_new shine" href="tg://resolve?domain=demo_bot">Start Bot</a>
</body></html>"""

CHANNEL_PAGE = """<html><head><title>Telegram: Contact @demo_bot</title></head><body>
<div class="tgme_page_title" dir="auto"><span dir="auto">Some Channel</span></div>
<div class="tgme_page_extra">42 subscribers</div>
<a class="tgme_action_button_new shine" href="tg://resolve?domain=demo_bot">View in Telegram</a>
</body></html>"""

USER_PAGE = """<html><head><title>Telegram: Contact @demo_bot</title></head><body>
<div class="tgme_page_title" dir="auto"><span dir="auto">someone</span></div>
<div class="tgme_page_extra">@demo_bot</div>
<a class="tgme_action_button_new shine" href="tg://resolve?domain=demo_bot">Send Message</a>
</body></html>"""

GENERIC_PAGE = """<html><head><title>Telegram: Contact @demo_bot</title></head><body>
<div class="tgme_page_description">
  If you have <strong>Telegram</strong>, you can contact <a class="tgme_username_link" href="tg://resolve?domain=demo_bot">@demo_bot</a> right away.
</div>
<a class="tgme_action_button_new" href="tg://resolve?domain=demo_bot">Send Message</a>
</body></html>"""

BLOCKED_PAGE = "<html><head><title>Just a moment...</title></head><body>checking</body></html>"


def obs_ok(**kw):
    o = {"obs": "ok", "http_code": 200, "fetched_at": "2026-10-12T00:00:00+00:00", "error_msg": None,
         "title": "Demo Bot", "description": None, "extra_raw": None, "monthly_users": None, "type": "bot",
         "is_verified": False, "photo_url": None, "page_kind": "bot", "not_bot": False}
    o.update(kw)
    return o


DEAD = {"obs": "dead", "http_code": 200, "fetched_at": "2026-10-12T00:00:00+00:00", "error_msg": None}
ERR = {"obs": "error", "http_code": 503, "fetched_at": None, "error_msg": "http 503"}


class ParseTests(unittest.TestCase):
    def test_bot(self):
        p = fb.parse_preview(BOT_PAGE, "demo_bot")
        self.assertEqual(p["status_hint"], "ok")
        self.assertEqual(p["title"], "Demo Bot")
        self.assertEqual(p["monthly_users"], 12345)
        self.assertEqual(p["description"], "Line 1\nLine 2")
        self.assertFalse(p["not_bot"])

    def test_channel_is_not_bot(self):
        p = fb.parse_preview(CHANNEL_PAGE, "demo_bot")
        self.assertEqual(p["page_kind"], "channel")
        self.assertTrue(p["not_bot"])

    def test_user_is_not_bot(self):
        p = fb.parse_preview(USER_PAGE, "demo_bot")
        self.assertEqual(p["page_kind"], "user")
        self.assertTrue(p["not_bot"])

    def test_generic_contact_is_dead(self):
        self.assertEqual(fb.parse_preview(GENERIC_PAGE, "demo_bot")["status_hint"], "dead")

    def test_generic_page_for_other_username_is_ambiguous(self):
        self.assertEqual(fb.parse_preview(GENERIC_PAGE, "other_bot")["status_hint"], "ambiguous")

    def test_blocked_page_is_ambiguous(self):
        self.assertEqual(fb.parse_preview(BLOCKED_PAGE, "demo_bot")["status_hint"], "ambiguous")


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.ok = fb.merge_observation({"status": "pending"}, obs_ok(title="Demo Bot"))

    def test_single_dead_keeps_ok(self):
        m = fb.merge_observation(self.ok, DEAD)
        self.assertEqual(m["status"], "ok")
        self.assertEqual(m["dead_streak"], 1)
        self.assertEqual(m["title"], "Demo Bot")

    def test_consecutive_dead_marks_dead_then_hide_threshold(self):
        m = self.ok
        for _ in range(fb.DEAD_CONFIRM):
            m = fb.merge_observation(m, DEAD)
        self.assertEqual(m["status"], "dead")
        for _ in range(fb.HIDE_AFTER - fb.DEAD_CONFIRM):
            m = fb.merge_observation(m, DEAD)
        self.assertGreaterEqual(m["dead_streak"], fb.HIDE_AFTER)

    def test_ok_resets_streak(self):
        m = fb.merge_observation(fb.merge_observation(self.ok, DEAD), obs_ok())
        self.assertEqual(m["dead_streak"], 0)
        self.assertEqual(m["status"], "ok")

    def test_error_keeps_previous_fields(self):
        m = fb.merge_observation(self.ok, ERR)
        self.assertEqual(m["status"], "ok")
        self.assertEqual(m["title"], "Demo Bot")
        self.assertEqual(m["fetched_at"], self.ok["fetched_at"])
        self.assertEqual(m["error_msg"], "http 503")

    def test_error_does_not_reset_dead_streak(self):
        m = fb.merge_observation(fb.merge_observation(self.ok, DEAD), ERR)
        self.assertEqual(m["dead_streak"], 1)

    def test_unchanged_ok_keeps_fetched_at(self):
        m = fb.merge_observation(self.ok, obs_ok(fetched_at="2026-10-19T00:00:00+00:00"))
        self.assertEqual(m["fetched_at"], self.ok["fetched_at"])
        self.assertEqual(m, self.ok)


if __name__ == "__main__":
    unittest.main()

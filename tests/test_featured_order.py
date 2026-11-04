"""精选区人工顺序（顶层 featured_order）的回归测试。

覆盖：README 与站点两个渲染器行为一致、未列条目按月底降序兜底、
顺序表与 featured=true 集合失配时 --check seed 必须拒绝。
"""
import copy
import io
import json
import unittest
from contextlib import redirect_stdout

from scripts import build_site, render_readme
from scripts.validate import DATA_FILE, check_seed

DATA = json.loads(DATA_FILE.read_text(encoding="utf-8"))


def make_bot(name, mu):
    return {
        "username": "@" + name,
        "fetch": {"status": "ok", "monthly_users": mu},
    }


def names(bots):
    return [str(b.get("username", "")).lower().lstrip("@") for b in bots]


class FeaturedOrderTests(unittest.TestCase):
    def test_both_renderers_follow_featured_order(self):
        featured = [b for b in DATA["bots"] if b.get("featured")]
        expected = [u.lower().lstrip("@") for u in DATA["featured_order"]]
        for sorter in (render_readme.sort_featured, build_site.sort_featured):
            with self.subTest(sorter=sorter.__module__):
                self.assertEqual(names(sorter(featured, DATA["featured_order"])), expected)

    def test_first_two_are_soso_then_botfather(self):
        featured = [b for b in DATA["bots"] if b.get("featured")]
        got = names(render_readme.sort_featured(featured, DATA["featured_order"]))
        self.assertEqual(got[:2], ["soso", "botfather"])

    def test_unlisted_bots_keep_monthly_desc(self):
        bots = [make_bot("a", 10000), make_bot("b", 500000),
                make_bot("c", 200000), make_bot("d", 300000)]
        self.assertEqual(names(render_readme.sort_featured(bots, ["@c"])),
                         ["c", "b", "d", "a"])
        self.assertEqual(names(build_site.sort_featured(bots, ["@c"])),
                         ["c", "b", "d", "a"])

    def test_missing_order_falls_back_to_monthly_desc(self):
        bots = [make_bot("a", 10000), make_bot("b", 500000),
                make_bot("c", 200000), make_bot("d", 300000)]
        self.assertEqual(names(render_readme.sort_featured(bots, None)),
                         ["b", "d", "c", "a"])
        self.assertEqual(names(build_site.sort_featured(bots, [])),
                         ["b", "d", "c", "a"])

    def test_seed_accepts_matching_order(self):
        with redirect_stdout(io.StringIO()):
            self.assertTrue(check_seed(copy.deepcopy(DATA)))

    def test_seed_rejects_incomplete_order(self):
        data = copy.deepcopy(DATA)
        data["featured_order"] = data["featured_order"][:-1]
        with redirect_stdout(io.StringIO()):
            self.assertFalse(check_seed(data))

    def test_seed_rejects_non_featured_entry(self):
        data = copy.deepcopy(DATA)
        data["featured_order"] = data["featured_order"] + ["@not_featured"]
        with redirect_stdout(io.StringIO()):
            self.assertFalse(check_seed(data))

    def test_seed_rejects_duplicate_entry(self):
        data = copy.deepcopy(DATA)
        data["featured_order"] = data["featured_order"] + [data["featured_order"][0]]
        with redirect_stdout(io.StringIO()):
            self.assertFalse(check_seed(data))


if __name__ == "__main__":
    unittest.main()

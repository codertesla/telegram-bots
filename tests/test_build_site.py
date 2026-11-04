import json
import unittest
from pathlib import Path

from scripts.build_site import DATA_FILE, OUT_FILE, ROOT, build_html


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


if __name__ == "__main__":
    unittest.main()

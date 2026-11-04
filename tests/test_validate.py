"""validate.py 的离线单元测试，重点覆盖数据溯源（防手工编造）检查。"""
import copy
import json
import unittest
from datetime import datetime, timezone

from scripts.validate import (
    check_provenance,
    parse_extra_raw,
    parse_fetched_at,
    DATA_FILE,
)

FA = "2026-11-04T09:00:01.123456+00:00"
TOP = "2026-11-04T09:10:00.654321+00:00"
NOW = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)


def make_bot(bid="x", *, mu=10000, raw="10 000 monthly users", fa=FA,
             status="ok", http=200):
    return {
        "id": bid,
        "username": "@" + bid,
        "fetch": {
            "status": status,
            "http_code": http,
            "fetched_at": fa,
            "extra_raw": raw,
            "monthly_users": mu,
        },
    }


def make_data(bots, *, top=TOP, label="2026-11"):
    return {
        "schema_version": 1,
        "last_fetched_at": top,
        "last_verified_label": label,
        "bots": bots,
    }


class ParseHelpersTests(unittest.TestCase):
    def test_parse_extra_raw_variants(self):
        cases = {
            "299 956 monthly users": 299956,
            "6 368 886 subscribers": 6368886,
            "12 400 members": 12400,
            "1,234 monthly users": 1234,
            "45 000 000 monthly users": 45000000,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_extra_raw(raw), expected)

    def test_parse_extra_raw_rejects_junk(self):
        for raw in (None, "", "unknown", "12 bots", 12345):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_extra_raw(raw))

    def test_parse_fetched_at_requires_timezone(self):
        self.assertIsNotNone(parse_fetched_at(FA))
        self.assertIsNone(parse_fetched_at("2026-11-04T09:00:01.123456"))
        self.assertIsNone(parse_fetched_at("not-a-date"))
        self.assertIsNone(parse_fetched_at(None))


class ProvenanceTests(unittest.TestCase):
    def test_committed_data_passes(self):
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        self.assertTrue(check_provenance(data), "仓库当前 bots.json 必须能通过溯源检查")

    def test_clean_synthetic_data_passes(self):
        data = make_data([
            make_bot("a", mu=10000),
            make_bot("b", mu=20000, raw="20 000 monthly users", fa="2026-11-04T09:00:03.123456+00:00"),
            # 合法的无月活条目；即便无数据，脚本也会逐条写入独立时间戳
            make_bot("c", mu=None, raw=None, fa="2026-11-04T09:00:05.123456+00:00"),
        ])
        self.assertTrue(check_provenance(data, now=NOW))

    def test_pr8_batch_forgery_is_rejected(self):
        """PR #8 的 12 条手工数据：连 extra_raw 都伪造了，靠时间戳指纹拦下。"""
        forged_fa = "2026-11-04T12:00:00.000000+00:00"
        bots = [
            make_bot(f"forged{i}", mu=1000000 + i,
                     raw=f"{1000000 + i:,}".replace(",", " ") + " monthly users",
                     fa=forged_fa)
            for i in range(12)
        ]
        data = make_data(bots, top=forged_fa)
        self.assertFalse(check_provenance(data, now=datetime(2026, 11, 4, 13, 0, tzinfo=timezone.utc)))

    def test_extra_raw_must_match_monthly_users(self):
        data = make_data([make_bot("a", mu=999999, raw="10 000 monthly users")])
        self.assertFalse(check_provenance(data, now=NOW))

    def test_missing_extra_raw_is_rejected(self):
        data = make_data([make_bot("a", mu=10000, raw=None)])
        self.assertFalse(check_provenance(data, now=NOW))

    def test_monthly_users_without_ok_status_is_rejected(self):
        data = make_data([make_bot("a", status="dead")])
        self.assertFalse(check_provenance(data, now=NOW))

    def test_monthly_users_without_http_200_is_rejected(self):
        data = make_data([make_bot("a", http=429)])
        self.assertFalse(check_provenance(data, now=NOW))

    def test_shared_fetched_at_is_rejected(self):
        data = make_data([make_bot("a"), make_bot("b", fa=FA)])
        self.assertFalse(check_provenance(data, now=NOW))

    def test_round_minute_zero_microsecond_is_rejected(self):
        data = make_data([make_bot("a", fa="2026-11-04T09:00:00.000000+00:00")])
        self.assertFalse(check_provenance(data, now=NOW))

    def test_future_timestamps_are_rejected(self):
        data = make_data([make_bot("a")], top="2026-11-05T09:10:00.654321+00:00")
        self.assertFalse(check_provenance(data, now=NOW))

    def test_batch_label_mismatch_is_rejected(self):
        data = make_data([make_bot("a")], label="2026-10")
        self.assertFalse(check_provenance(data, now=NOW))

    def test_batch_time_identical_to_entry_time_is_rejected(self):
        data = make_data([make_bot("a", fa=TOP)], top=TOP)
        self.assertFalse(check_provenance(data, now=NOW))

    def test_idempotent_old_snapshot_is_allowed(self):
        """fetch_bots.py 幂等：数据未变时保留旧 fetched_at，不应误判。"""
        data = make_data([
            make_bot("a", fa="2026-11-02T10:44:50.307488+00:00"),
            make_bot("b", fa="2026-11-04T09:00:03.123456+00:00"),
        ])
        self.assertTrue(check_provenance(data, now=NOW))

    def test_mutation_does_not_leak_between_checks(self):
        data = make_data([make_bot("a")])
        snapshot = copy.deepcopy(data)
        check_provenance(data, now=NOW)
        self.assertEqual(data, snapshot, "校验函数不得修改传入数据")


if __name__ == "__main__":
    unittest.main()

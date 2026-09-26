"""npu.dataset 단위 테스트: 키 파싱, 필터 정규화, 케이스 판정, 실제 data.json."""

import unittest

from npu import core, dataset


def _cross(n):
    mid = n // 2
    m = core.create_matrix(n)
    for i in range(n):
        for j in range(n):
            if i == mid or j == mid:
                m[i][j] = 1.0
    return m


def _x(n):
    m = core.create_matrix(n)
    for i in range(n):
        for j in range(n):
            if i == j or i + j == n - 1:
                m[i][j] = 1.0
    return m


class KeyParsingTest(unittest.TestCase):
    def test_parse_size(self):
        self.assertEqual(dataset.parse_size_from_key("size_13_1"), 13)

    def test_parse_bad_key_raises(self):
        with self.assertRaises(ValueError):
            dataset.parse_size_from_key("bad_key")

    def test_sort_key_is_natural(self):
        keys = ["size_13_1", "size_5_2", "size_5_1"]
        self.assertEqual(
            sorted(keys, key=dataset.pattern_sort_key),
            ["size_5_1", "size_5_2", "size_13_1"],
        )


class NormalizeFiltersTest(unittest.TestCase):
    def test_keys_normalized_to_standard_labels(self):
        raw = {"size_5": {"cross": _cross(5), "x": _x(5)}}
        norm = dataset.normalize_filters(raw)
        self.assertIn(5, norm)
        self.assertEqual(
            sorted(norm[5]), [core.LABEL_CROSS, core.LABEL_X]
        )


class AnalyzePatternTest(unittest.TestCase):
    def setUp(self):
        self.filters = {5: {core.LABEL_CROSS: _cross(5), core.LABEL_X: _x(5)}}

    def test_pass_when_verdict_matches_expected(self):
        entry = {"input": _cross(5), "expected": "+"}
        res = dataset.analyze_pattern("size_5_1", entry, self.filters)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["verdict"], core.LABEL_CROSS)

    def test_size_mismatch_fails_without_crash(self):
        entry = {"input": _cross(3), "expected": "x"}
        res = dataset.analyze_pattern("size_5_9", entry, self.filters)
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("크기 불일치", res["reason"])

    def test_missing_filter_fails(self):
        entry = {"input": _cross(13), "expected": "+"}
        res = dataset.analyze_pattern("size_13_1", entry, self.filters)
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("필터", res["reason"])

    def test_bad_label_fails(self):
        entry = {"input": _cross(5), "expected": "circle"}
        res = dataset.analyze_pattern("size_5_1", entry, self.filters)
        self.assertEqual(res["status"], "FAIL")

    def test_missing_input_key_fails_without_crash(self):
        res = dataset.analyze_pattern("size_5_1", {"expected": "x"}, self.filters)
        self.assertEqual(res["status"], "FAIL")


class RealDataTest(unittest.TestCase):
    """실제 data/data.json 로드 시 통과 3 / 실패 3 이 나오는지 확인."""

    def test_dataset_pass_fail_totals(self):
        data = dataset.load_data(dataset.DATA_PATH)
        filters = dataset.normalize_filters(data["filters"])
        results = [
            dataset.analyze_pattern(pid, entry, filters)
            for pid, entry in data["patterns"].items()
        ]
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        self.assertEqual(len(results), 6)
        self.assertEqual(passed, 3)
        self.assertEqual(failed, 3)


if __name__ == "__main__":
    unittest.main()

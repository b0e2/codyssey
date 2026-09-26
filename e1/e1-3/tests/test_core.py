"""npu.core 단위 테스트: 라벨 정규화, 행렬 접근, MAC 연산, 판정."""

import unittest

from npu import core


CROSS = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
X = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]


class NormalizeLabelTest(unittest.TestCase):
    def test_cross_variants(self):
        for raw in ("cross", "Cross", "CROSS", "+"):
            self.assertEqual(core.normalize_label(raw), core.LABEL_CROSS)

    def test_x_variants(self):
        for raw in ("x", "X"):
            self.assertEqual(core.normalize_label(raw), core.LABEL_X)

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            core.normalize_label("circle")

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            core.normalize_label(None)


class MatrixTest(unittest.TestCase):
    def test_create_shape_and_fill(self):
        m = core.create_matrix(4, fill=2.0)
        self.assertEqual(core.matrix_size(m), 4)
        self.assertEqual(core.get_cell(m, 0, 0), 2.0)

    def test_set_and_get(self):
        m = core.create_matrix(3)
        core.set_cell(m, 1, 2, 7.0)
        self.assertEqual(core.get_cell(m, 1, 2), 7.0)

    def test_non_square_raises(self):
        with self.assertRaises(ValueError):
            core.matrix_size([[1, 2, 3], [4, 5]])

    def test_flatten_length_and_order(self):
        flat = core.flatten([[1, 2], [3, 4]])
        self.assertEqual(len(flat), 4)
        self.assertEqual(flat, [1, 2, 3, 4])


class MacTest(unittest.TestCase):
    def test_cross_on_cross_scores_5(self):
        self.assertEqual(core.mac_2d(CROSS, CROSS), 5.0)

    def test_cross_on_x_scores_1(self):
        self.assertEqual(core.mac_2d(CROSS, X), 1.0)

    def test_size_mismatch_raises(self):
        with self.assertRaises(ValueError):
            core.mac_2d(CROSS, core.create_matrix(5))

    def test_mac_1d_matches_2d(self):
        flat_p = core.flatten(CROSS)
        flat_f = core.flatten(X)
        self.assertEqual(core.mac_1d(flat_p, flat_f), core.mac_2d(CROSS, X))

    def test_mac_1d_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            core.mac_1d([1, 2, 3], [1, 2])


class JudgeTest(unittest.TestCase):
    def test_cross_wins(self):
        self.assertEqual(core.judge(5.0, 1.0), core.LABEL_CROSS)

    def test_x_wins(self):
        self.assertEqual(core.judge(1.0, 5.0), core.LABEL_X)

    def test_tie_within_epsilon_is_undecided(self):
        self.assertEqual(
            core.judge(0.9, 0.9 - 1e-16), core.LABEL_UNDECIDED
        )

    def test_difference_above_epsilon_not_undecided(self):
        self.assertNotEqual(
            core.judge(1.0, 1.0 - 1e-6), core.LABEL_UNDECIDED
        )


if __name__ == "__main__":
    unittest.main()

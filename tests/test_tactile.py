import json
import math
import unittest
from pathlib import Path

from tactile import estimate


def case(name):
    return json.loads((Path(__file__).parents[1] / "examples" / f"{name}.json").read_text())


class TactileTests(unittest.TestCase):
    def test_unequal_gain_and_center(self):
        data = estimate(case("single-patch"))
        self.assertEqual(data["status"], "contact")
        self.assertEqual(data["force_n"], 3)
        self.assertEqual(data["taxel_forces_n"][1], [0, 1, 2])
        self.assertAlmostEqual(data["center_mm"][0], 25 / 3)
        self.assertAlmostEqual(data["center_mm"][1], 5)

    def test_disconnected_contacts_center_over_empty_cell(self):
        data = estimate(case("two-contacts"))
        self.assertEqual(data["force_n"], 4)
        self.assertEqual(data["center_mm"], [5, 5])
        self.assertEqual(data["taxel_forces_n"][1][1], 0)

    def test_deadband_boundary_and_negative_noise(self):
        data = estimate(case("quiet"))
        self.assertEqual(data["status"], "below_threshold")
        self.assertEqual(data["force_n"], 0)
        self.assertIsNone(data["center_mm"])

    def test_active_boundary_and_weak_load(self):
        setup = case("quiet")
        setup["minimum_load_n"] = .5
        setup["frame"][1][1] = 149
        self.assertEqual(estimate(setup)["force_n"], .49)
        self.assertIsNone(estimate(setup)["center_mm"])
        setup["frame"][1][1] = 150
        self.assertEqual(estimate(setup)["center_mm"], [5, 5])

    def test_upper_and_lower_rail_invalidate_frame(self):
        setup = case("clipped")
        setup["frame"][2][0] = 0
        data = estimate(setup)
        self.assertEqual(data["status"], "clipped")
        self.assertEqual(data["clipped_row_col"], [[1, 2], [2, 0]])
        for key in ("force_n", "center_mm", "taxel_forces_n"):
            self.assertIsNone(data[key])

    def test_dimension_gain_and_baseline_validation(self):
        for key, bad in (("counts_per_newton", [[0]]), ("frame", [[100]]),
                         ("deadband_counts", math.nan), ("unloaded_frames", [[[0]]])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                estimate({**case("single-patch"), key: bad})

    def test_common_unloaded_offset_cancels(self):
        setup = case("single-patch")
        expected = estimate(setup)
        for frame in [*setup["unloaded_frames"], setup["frame"]]:
            for row in frame:
                for c in range(len(row)):
                    row[c] += 42
        self.assertEqual(estimate(setup), expected)

    def test_asymmetric_row_column_and_pitch(self):
        setup = case("quiet")
        setup["pitch_mm"] = 4
        setup["frame"][2][1] = 205
        self.assertEqual(estimate(setup)["center_mm"], [4, 8])

    def test_bad_adc_count_and_clipped_baseline(self):
        setup = case("quiet")
        setup["frame"][0][0] = True
        with self.assertRaisesRegex(ValueError, "integer counts"):
            estimate(setup)
        setup["frame"][0][0] = 100
        setup["unloaded_frames"][0][0][0] = 0
        with self.assertRaisesRegex(ValueError, "ADC rail"):
            estimate(setup)

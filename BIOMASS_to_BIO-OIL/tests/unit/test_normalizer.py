import unittest

from biomass_pyrolysis_equilibrium.data.normalizer import parse_numeric_cell


class TestNormalizer(unittest.TestCase):
    def test_parse_comma_decimal(self):
        value, warnings = parse_numeric_cell(
            "12,5",
            decimal_separator=",",
            midpoint_for_ranges=True,
            incomplete_range_use_single_bound=True,
            warning_prefix="T",
        )
        self.assertAlmostEqual(value, 12.5)
        self.assertEqual(len(warnings), 0)

    def test_parse_range_midpoint(self):
        value, warnings = parse_numeric_cell(
            "10-20",
            decimal_separator=",",
            midpoint_for_ranges=True,
            incomplete_range_use_single_bound=True,
            warning_prefix="T",
        )
        self.assertAlmostEqual(value, 15.0)
        self.assertTrue(any(w.code == "T_RANGE_MIDPOINT" for w in warnings))

    def test_parse_incomplete_range(self):
        value, warnings = parse_numeric_cell(
            "10-",
            decimal_separator=",",
            midpoint_for_ranges=True,
            incomplete_range_use_single_bound=True,
            warning_prefix="T",
        )
        self.assertAlmostEqual(value, 10.0)
        self.assertTrue(any(w.code == "T_INCOMPLETE_RANGE_ASSUMED" for w in warnings))


if __name__ == "__main__":
    unittest.main()

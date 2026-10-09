from django.test import SimpleTestCase

from planner.size_guide import SIZES


class SizeGuideTests(SimpleTestCase):
    def test_ranges_match_spec_table(self):
        table = [(s.name, s.width, s.low, s.high) for s in SIZES]

        self.assertEqual(
            table,
            [
                ("Practice", 18, 50, 63),
                ("Baby", 36, 99, 126),
                ("Lap", 36, 99, 126),
                ("Throw", 50, 138, 175),
                ("Twin", 66, 182, 231),
                ("Full", 80, 220, 280),
                ("Queen", 90, 248, 315),
                ("King", 108, 297, 378),
            ],
        )

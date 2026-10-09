from django.test import SimpleTestCase

from planner.rules import fit_errors
from stitches.models import Stitch

ONE_COLOR = Stitch(name="Single crochet", multiple=1, colors=1)
TWO_COLOR = Stitch(name="Two-color moss", multiple=2, colors=2)


class FitErrorsTests(SimpleTestCase):
    def test_needs_more_stitches_than_n(self):
        errors = fit_errors(n=2, stitches=[ONE_COLOR, ONE_COLOR], color_count=10)

        self.assertEqual(
            errors, ["Too few stitches: with 2 draws before a repeat, the project needs at least 3 active stitches."]
        )

    def test_one_color_stitches_need_n_plus_one_colors(self):
        stitches = [ONE_COLOR] * 3

        self.assertEqual(fit_errors(n=2, stitches=stitches, color_count=3), [])
        self.assertEqual(
            fit_errors(n=2, stitches=stitches, color_count=2),
            ["Too few colors: with 2 draws before a repeat, the project needs at least 3 active colors."],
        )

    def test_two_color_stitch_needs_2n_plus_2_colors(self):
        stitches = [ONE_COLOR, ONE_COLOR, TWO_COLOR]

        self.assertEqual(fit_errors(n=2, stitches=stitches, color_count=6), [])
        self.assertEqual(
            fit_errors(n=2, stitches=stitches, color_count=5),
            [
                "Too few colors: with 2 draws before a repeat and a two-color stitch, "
                "the project needs at least 6 active colors."
            ],
        )

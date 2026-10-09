from django.test import TestCase

from planner.rules import DrawError, blocked, pick_draw
from planner.tests.factories import add_draw, make_project


class BlockedTests(TestCase):
    def test_blocks_colors_from_last_n_draws(self):
        project = make_project(
            stitches=[("Single crochet", 1, 0, 1), ("Two-color moss", 2, 0, 2)],
            colors=["red", "blue", "cream", "green"],
            repeat_gap=2,
        )
        add_draw(project, "Single crochet", "red")
        add_draw(project, "Two-color moss", "blue", "cream")
        add_draw(project, "Single crochet", "green")

        _, colors = blocked(project)

        self.assertEqual({c.name for c in colors}, {"blue", "cream", "green"})

    def test_blocks_stitches_from_n_draws_before_given_draw(self):
        project = make_project(
            stitches=[("A", 1, 0, 1), ("B", 1, 0, 1), ("C", 1, 0, 1)],
            colors=["red", "blue", "cream"],
            repeat_gap=1,
        )
        add_draw(project, "A", "red")
        rerolled = add_draw(project, "B", "blue")
        add_draw(project, "C", "cream")

        stitches, colors = blocked(project, before=rerolled)

        self.assertEqual({str(s) for s in stitches}, {"A"})
        self.assertEqual({str(c) for c in colors}, {"red"})

    def test_n_of_zero_blocks_nothing(self):
        project = make_project(repeat_gap=0)
        add_draw(project, "Single crochet", "red")

        self.assertEqual(blocked(project), (set(), set()))


class PickDrawTests(TestCase):
    def test_picks_unblocked_stitch_and_color_and_rows_in_range(self):
        project = make_project(
            stitches=[("A", 1, 0, 1), ("B", 1, 0, 1)],
            colors=["red", "blue"],
            repeat_gap=1,
            min_rows=3,
            max_rows=3,
        )
        add_draw(project, "A", "red")

        pick = pick_draw(project)

        self.assertEqual(str(pick.stitch), "B")
        self.assertEqual(str(pick.color1), "blue")
        self.assertIsNone(pick.color2)
        self.assertEqual(pick.rows, 3)

    def test_two_color_stitch_gets_two_different_colors(self):
        project = make_project(stitches=[("Moss", 2, 0, 2)], colors=["red", "blue"])

        for _ in range(10):
            pick = pick_draw(project)
            self.assertEqual({str(pick.color1), str(pick.color2)}, {"red", "blue"})

    def test_skips_inactive_stitches_and_colors(self):
        project = make_project(
            stitches=[("A", 1, 0, 1), ("B", 1, 0, 1)], colors=["red", "blue"]
        )
        project.project_stitches.filter(stitch__name="A").update(active=False)
        project.colors.filter(name="red").update(active=False)

        for _ in range(10):
            pick = pick_draw(project)
            self.assertEqual((str(pick.stitch), str(pick.color1)), ("B", "blue"))

    def test_raises_when_nothing_can_be_drawn(self):
        project = make_project()
        project.colors.update(active=False)

        with self.assertRaisesMessage(DrawError, "No stitch and color combination"):
            pick_draw(project)

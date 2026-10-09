from django.test import TestCase

from planner.tests.factories import add_draw, make_project


class UsageTests(TestCase):
    def setUp(self):
        self.project = make_project(
            stitches=[("Single crochet", 1, 0, 1), ("Moss", 2, 0, 2), ("Unused", 1, 0, 1)],
            colors=["red", "blue", "cream"],
        )
        add_draw(self.project, "Single crochet", "red", rows=3)
        add_draw(self.project, "Moss", "blue", "red", rows=2)
        add_draw(self.project, "Single crochet", "blue", rows=4)

    def test_stitch_usage_counts_draws(self):
        usage = {str(s): s.draw_count for s in self.project.stitch_usage()}

        self.assertEqual(usage, {"Moss": 1, "Single crochet": 2, "Unused": 0})

    def test_color_usage_counts_both_colors_of_two_color_draws(self):
        usage = {str(c): c.draw_count for c in self.project.color_usage()}

        self.assertEqual(usage, {"blue": 2, "cream": 0, "red": 2})


class SharingTests(TestCase):
    def test_turning_sharing_on_generates_ten_char_token_once(self):
        project = make_project()

        project.set_shared(True)
        token = project.share_token
        project.set_shared(False)
        project.set_shared(True)

        project.refresh_from_db()
        self.assertTrue(project.is_shared)
        self.assertEqual(project.share_token, token)
        self.assertRegex(token, r"^[A-Za-z0-9]{10}$")

    def test_turning_sharing_off_keeps_token(self):
        project = make_project()
        project.set_shared(True)

        project.set_shared(False)

        project.refresh_from_db()
        self.assertFalse(project.is_shared)
        self.assertIsNotNone(project.share_token)


class PaddingTextTests(TestCase):
    def test_padding_of_one_goes_at_start_only(self):
        project = make_project(stitches=[("Moss", 2, 0, 1)], stitch_count=151)

        draw = add_draw(project, "Moss", "red")

        self.assertEqual(draw.padding_text, "1 at the start")


class ProjectStrTests(TestCase):
    def test_str_is_name(self):
        self.assertEqual(str(make_project(name="Rainbow")), "Rainbow")

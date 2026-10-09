from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from planner.tests.factories import add_draw, make_project


class DrawViewTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.project = make_project(
            owner=self.alice,
            stitches=[("Shell", 6, 1, 1), ("Moss", 2, 0, 2)],
            colors=["red", "blue", "cream", "green"],
            repeat_gap=0,
            stitch_count=150,
        )


class NewDrawTests(DrawViewTestCase):
    def test_draw_adds_to_history(self):
        response = self.client.post(reverse("draw_create", args=[self.project.pk]))

        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        self.assertEqual(self.project.draws.count(), 1)

    def test_shows_error_when_nothing_can_be_drawn(self):
        self.project.colors.update(active=False)

        response = self.client.post(reverse("draw_create", args=[self.project.pk]), follow=True)

        self.assertContains(response, "No stitch and color combination can be drawn.")
        self.assertEqual(self.project.draws.count(), 0)

    def test_other_users_cannot_draw(self):
        self.client.force_login(User.objects.create_user("bob"))

        response = self.client.post(reverse("draw_create", args=[self.project.pk]))

        self.assertEqual(response.status_code, 404)


class HistoryTests(DrawViewTestCase):
    def test_shows_draws_with_padding_split(self):
        add_draw(self.project, "Shell", "red", rows=3)
        add_draw(self.project, "Moss", "blue", "cream", rows=2)

        response = self.client.get(reverse("project_detail", args=[self.project.pk]))

        self.assertContains(response, "Shell")
        self.assertContains(response, "3 at the start, 2 at the end")
        self.assertContains(response, "blue and cream")
        self.assertContains(response, "No padding")


class EditDeleteRerollTests(DrawViewTestCase):
    def test_delete_removes_draw(self):
        draw = add_draw(self.project, "Shell", "red")

        response = self.client.post(reverse("draw_delete", args=[draw.pk]))

        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        self.assertFalse(self.project.draws.exists())

    def test_other_users_cannot_delete(self):
        draw = add_draw(self.project, "Shell", "red")
        self.client.force_login(User.objects.create_user("bob"))

        response = self.client.post(reverse("draw_delete", args=[draw.pk]))

        self.assertEqual(response.status_code, 404)

    def test_reroll_replaces_draw_in_place_following_rule_for_draws_before_it(self):
        project = make_project(
            owner=self.alice,
            stitches=[("A", 1, 0, 1), ("B", 1, 0, 1), ("C", 1, 0, 1)],
            colors=["red", "blue", "cream"],
            repeat_gap=1,
            min_rows=5,
            max_rows=5,
        )
        add_draw(project, "A", "red", rows=1)
        rerolled = add_draw(project, "B", "blue", rows=1)
        add_draw(project, "C", "cream", rows=1)

        for _ in range(10):
            response = self.client.post(reverse("draw_reroll", args=[rerolled.pk]))
            rerolled.refresh_from_db()
            self.assertNotEqual(str(rerolled.stitch), "A")
            self.assertNotEqual(str(rerolled.color1), "red")
            self.assertEqual(rerolled.rows, 5)

        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        self.assertEqual(project.draws.count(), 3)

    def test_reroll_shows_error_when_nothing_can_be_drawn(self):
        draw = add_draw(self.project, "Shell", "red")
        self.project.colors.update(active=False)

        response = self.client.post(reverse("draw_reroll", args=[draw.pk]), follow=True)

        self.assertContains(response, "No stitch and color combination can be drawn.")


class DrawEditTests(DrawViewTestCase):
    def setUp(self):
        super().setUp()
        self.draw = add_draw(self.project, "Shell", "red", rows=2)
        self.ids = {str(s): s.pk for s in self.project.project_stitches.all()}
        self.ids.update({str(c): c.pk for c in self.project.colors.all()})

    def post(self, stitch, color1, color2="", rows=3):
        return self.client.post(
            reverse("draw_edit", args=[self.draw.pk]),
            {
                "stitch": self.ids[stitch],
                "color1": self.ids[color1],
                "color2": self.ids[color2] if color2 else "",
                "rows": rows,
            },
        )

    def test_edits_draw_without_checking_repeat_rule(self):
        self.project.repeat_gap = 1
        self.project.save()
        add_draw(self.project, "Moss", "blue", "cream")

        response = self.post("Moss", "blue", "cream", rows=9)

        self.draw.refresh_from_db()
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        self.assertEqual(
            (str(self.draw.stitch), self.draw.colors_text, self.draw.rows),
            ("Moss", "blue and cream", 9),
        )

    def test_two_color_stitch_needs_a_different_second_color(self):
        response = self.post("Moss", "blue")
        self.assertContains(response, "Moss needs two different colors.")

        response = self.post("Moss", "blue", "blue")
        self.assertContains(response, "Moss needs two different colors.")

    def test_one_color_stitch_cannot_have_second_color(self):
        response = self.post("Shell", "blue", "cream")

        self.assertContains(response, "Shell uses one color.")

    def test_edit_page_shows_form_and_requires_stitch(self):
        response = self.client.get(reverse("draw_edit", args=[self.draw.pk]))
        self.assertContains(response, "Edit draw in Blanket")

        response = self.client.post(
            reverse("draw_edit", args=[self.draw.pk]), {"color1": self.ids["red"], "rows": 2}
        )
        self.assertContains(response, "This field is required.")

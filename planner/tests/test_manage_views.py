from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from planner.tests.factories import add_draw, make_project
from stitches.models import Stitch


class ManageTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.project = make_project(
            owner=self.alice,
            stitches=[("A", 1, 0, 1), ("B", 1, 0, 1), ("C", 1, 0, 1)],
            colors=["red", "blue", "cream"],
            repeat_gap=1,
        )
        self.detail = reverse("project_detail", args=[self.project.pk])

    def stitch(self, name):
        return self.project.project_stitches.get(stitch__name=name)

    def color(self, name):
        return self.project.colors.get(name=name)


class ToggleTests(ManageTestCase):
    def test_deactivates_and_reactivates_stitch(self):
        url = reverse("project_stitch_toggle", args=[self.stitch("A").pk])

        response = self.client.post(url)
        self.assertRedirects(response, self.detail)
        self.assertFalse(self.stitch("A").active)

        self.client.post(url)
        self.assertTrue(self.stitch("A").active)

    def test_blocks_stitch_deactivation_that_breaks_fit(self):
        self.client.post(reverse("project_stitch_toggle", args=[self.stitch("A").pk]))

        response = self.client.post(
            reverse("project_stitch_toggle", args=[self.stitch("B").pk]), follow=True
        )

        self.assertContains(response, "Too few stitches")
        self.assertTrue(self.stitch("B").active)

    def test_deactivates_color_and_blocks_when_too_few(self):
        response = self.client.post(reverse("project_color_toggle", args=[self.color("red").pk]))
        self.assertRedirects(response, self.detail)
        self.assertFalse(self.color("red").active)

        response = self.client.post(
            reverse("project_color_toggle", args=[self.color("blue").pk]), follow=True
        )
        self.assertContains(response, "Too few colors")
        self.assertTrue(self.color("blue").active)

        self.client.post(reverse("project_color_toggle", args=[self.color("red").pk]))
        self.assertTrue(self.color("red").active)

    def test_existing_draws_keep_deactivated_stitch(self):
        add_draw(self.project, "A", "red")

        self.client.post(reverse("project_stitch_toggle", args=[self.stitch("A").pk]))

        self.assertEqual(str(self.project.draws.get().stitch), "A")

    def test_other_users_cannot_toggle(self):
        self.client.force_login(User.objects.create_user("bob"))

        response = self.client.post(reverse("project_stitch_toggle", args=[self.stitch("A").pk]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("project_color_toggle", args=[self.color("red").pk]))
        self.assertEqual(response.status_code, 404)


class AddRemoveTests(ManageTestCase):
    def test_adds_visible_stitch(self):
        shell = Stitch.objects.create(name="Shell", multiple=6, owner=self.alice)

        response = self.client.post(
            reverse("project_stitch_add", args=[self.project.pk]), {"stitch": shell.pk}
        )

        self.assertRedirects(response, self.detail)
        self.assertTrue(self.stitch("Shell").active)

    def test_cannot_add_hidden_or_duplicate_stitch(self):
        bob = User.objects.create_user("bob")
        secret = Stitch.objects.create(name="Secret", multiple=6, owner=bob)
        url = reverse("project_stitch_add", args=[self.project.pk])

        response = self.client.post(url, {"stitch": secret.pk}, follow=True)
        self.assertContains(response, "Select a valid choice")

        response = self.client.post(url, {"stitch": self.stitch("A").stitch_id}, follow=True)
        self.assertContains(response, "Select a valid choice")
        self.assertEqual(self.project.project_stitches.count(), 3)

    def test_adds_colors(self):
        response = self.client.post(
            reverse("project_color_add", args=[self.project.pk]), {"colors": "green\nred\n"}
        )

        self.assertRedirects(response, self.detail)
        self.assertEqual(
            sorted(str(c) for c in self.project.colors.all()), ["blue", "cream", "green", "red"]
        )

    def test_removes_unused_stitch_and_color(self):
        self.client.post(reverse("project_stitch_add", args=[self.project.pk]),
                         {"stitch": Stitch.objects.create(name="D", multiple=1, owner=self.alice).pk})
        self.client.post(reverse("project_color_add", args=[self.project.pk]), {"colors": "green"})

        self.client.post(reverse("project_stitch_remove", args=[self.stitch("D").pk]))
        response = self.client.post(reverse("project_color_remove", args=[self.color("green").pk]))

        self.assertRedirects(response, self.detail)
        self.assertFalse(self.project.project_stitches.filter(stitch__name="D").exists())
        self.assertFalse(self.project.colors.filter(name="green").exists())

    def test_refuses_to_remove_used_stitch_or_color(self):
        add_draw(self.project, "A", "red")
        self.client.post(reverse("project_stitch_add", args=[self.project.pk]),
                         {"stitch": Stitch.objects.create(name="D", multiple=1, owner=self.alice).pk})
        self.client.post(reverse("project_color_add", args=[self.project.pk]), {"colors": "green"})

        response = self.client.post(
            reverse("project_stitch_remove", args=[self.stitch("A").pk]), follow=True
        )
        self.assertContains(response, "A is used in a draw. Deactivate it instead.")
        response = self.client.post(
            reverse("project_color_remove", args=[self.color("red").pk]), follow=True
        )
        self.assertContains(response, "red is used in a draw. Deactivate it instead.")

    def test_refuses_removal_that_breaks_fit(self):
        self.project.repeat_gap = 2
        self.project.save()

        response = self.client.post(
            reverse("project_stitch_remove", args=[self.stitch("A").pk]), follow=True
        )

        self.assertContains(response, "Too few stitches")
        self.assertEqual(self.project.project_stitches.count(), 3)

    def test_removes_inactive_stitch_without_fit_check(self):
        self.project.repeat_gap = 2
        self.project.save()
        self.project.project_stitches.filter(stitch__name="A").update(active=False)

        self.client.post(reverse("project_stitch_remove", args=[self.stitch("A").pk]))

        self.assertFalse(self.project.project_stitches.filter(stitch__name="A").exists())

    def test_add_colors_requires_text(self):
        response = self.client.post(
            reverse("project_color_add", args=[self.project.pk]), {"colors": ""}, follow=True
        )

        self.assertContains(response, "This field is required.")

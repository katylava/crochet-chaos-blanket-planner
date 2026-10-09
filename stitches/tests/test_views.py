from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from planner.models import ProjectStitch
from planner.tests.factories import make_project
from stitches.models import Stitch


class StitchListTests(TestCase):
    def test_lists_public_and_own_stitches_only(self):
        owner = User.objects.create_user("owner")
        alice = User.objects.create_user("alice")
        Stitch.objects.create(name="Public shell", multiple=6, owner=owner, is_public=True)
        Stitch.objects.create(name="Owner private", multiple=6, owner=owner)
        Stitch.objects.create(name="Alice private", multiple=2, owner=alice)
        self.client.force_login(alice)

        response = self.client.get(reverse("stitch_list"))

        self.assertContains(response, "Public shell")
        self.assertContains(response, "Alice private")
        self.assertNotContains(response, "Owner private")


class StitchEditDeleteTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.owner = User.objects.create_user("owner")
        self.mine = Stitch.objects.create(name="Mine", multiple=2, owner=self.alice)
        self.public = Stitch.objects.create(
            name="Public", multiple=2, owner=self.owner, is_public=True
        )
        self.client.force_login(self.alice)

    def test_edits_own_private_stitch(self):
        response = self.client.post(
            reverse("stitch_edit", args=[self.mine.pk]),
            {"name": "Renamed", "multiple": 4, "edge_stitches": 1, "colors": 2},
        )

        self.mine.refresh_from_db()
        self.assertRedirects(response, reverse("stitch_list"))
        self.assertEqual((self.mine.name, self.mine.multiple, self.mine.colors), ("Renamed", 4, 2))

    def test_cannot_edit_public_or_others_stitches(self):
        response = self.client.get(reverse("stitch_edit", args=[self.public.pk]))

        self.assertEqual(response.status_code, 404)

    def test_deletes_unused_own_stitch(self):
        response = self.client.post(reverse("stitch_delete", args=[self.mine.pk]))

        self.assertRedirects(response, reverse("stitch_list"))
        self.assertFalse(Stitch.objects.filter(pk=self.mine.pk).exists())

    def test_refuses_to_delete_stitch_used_in_a_project(self):
        project = make_project(owner=self.alice, stitches=[])
        ProjectStitch.objects.create(project=project, stitch=self.mine)

        response = self.client.post(reverse("stitch_delete", args=[self.mine.pk]), follow=True)

        self.assertContains(response, "used in a project")
        self.assertTrue(Stitch.objects.filter(pk=self.mine.pk).exists())

    def test_list_shows_edit_link_for_own_private_stitch_only(self):
        response = self.client.get(reverse("stitch_list"))

        self.assertContains(response, reverse("stitch_edit", args=[self.mine.pk]))
        self.assertNotContains(response, reverse("stitch_edit", args=[self.public.pk]))

    def test_edit_page_shows_form(self):
        response = self.client.get(reverse("stitch_edit", args=[self.mine.pk]))

        self.assertContains(response, "Edit Mine")

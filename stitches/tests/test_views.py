import shutil
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from planner.models import ProjectStitch
from planner.tests.factories import make_project
from stitches.models import Stitch
from stitches.photos import clean_photo
from stitches.tests.test_photos import make_upload

MEDIA_ROOT = tempfile.mkdtemp()


class StitchListTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)

    def names(self, response):
        return [s.name for s in response.context["page"]]

    def test_searches_by_name(self):
        Stitch.objects.create(name="Shell", multiple=6, owner=self.alice)
        Stitch.objects.create(name="Moss", multiple=2, owner=self.alice)
        Stitch.objects.create(name="Two-color moss", multiple=2, owner=self.alice)

        response = self.client.get(reverse("stitch_list"), {"q": "moss"})

        self.assertEqual(self.names(response), ["Moss", "Two-color moss"])
        self.assertContains(response, 'value="moss"')

    def test_filters_to_own_stitches(self):
        owner = User.objects.create_user("owner")
        Stitch.objects.create(name="Public", multiple=2, owner=owner, is_public=True)
        Stitch.objects.create(name="Mine", multiple=2, owner=self.alice)

        response = self.client.get(reverse("stitch_list"), {"mine": "1"})

        self.assertEqual(self.names(response), ["Mine"])

    def test_pages_fifty_at_a_time_and_keeps_search(self):
        for i in range(51):
            Stitch.objects.create(name=f"Stitch {i:02}", multiple=1, owner=self.alice)

        first = self.client.get(reverse("stitch_list"), {"q": "stitch"})
        second = self.client.get(reverse("stitch_list"), {"q": "stitch", "page": 2})

        self.assertEqual(len(self.names(first)), 50)
        self.assertEqual(self.names(second), ["Stitch 50"])
        self.assertContains(first, "?q=stitch&page=2")

    def test_lists_public_and_own_stitches_only(self):
        owner = User.objects.create_user("owner")
        Stitch.objects.create(name="Public shell", multiple=6, owner=owner, is_public=True)
        Stitch.objects.create(name="Owner private", multiple=6, owner=owner)
        Stitch.objects.create(name="Alice private", multiple=2, owner=self.alice)

        response = self.client.get(reverse("stitch_list"))

        self.assertContains(response, "Public shell")
        self.assertContains(response, "Alice private")
        self.assertNotContains(response, "Owner private")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class StitchEditDeleteTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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

    def test_detail_shows_edit_and_delete_for_own_private_stitch_only(self):
        response = self.client.get(reverse("stitch_detail", args=[self.mine.pk]))
        self.assertContains(response, reverse("stitch_edit", args=[self.mine.pk]))
        self.assertContains(response, 'data-confirm="Delete Mine?"')

        response = self.client.get(reverse("stitch_detail", args=[self.public.pk]))
        self.assertNotContains(response, reverse("stitch_edit", args=[self.public.pk]))
        self.assertNotContains(response, reverse("stitch_delete", args=[self.public.pk]))

    def test_edit_page_shows_form(self):
        response = self.client.get(reverse("stitch_edit", args=[self.mine.pk]))

        self.assertContains(response, "Edit Mine")

    def test_list_shows_photo_thumbnail(self):
        self.mine.photo = clean_photo(make_upload())
        self.mine.save()

        response = self.client.get(reverse("stitch_list"))

        self.assertContains(response, f'src="{self.mine.photo.url}"')
        self.assertContains(
            response, f'<a href="{self.mine.photo.url}" target="_blank" rel="noopener">'
        )

    def test_list_shows_placeholder_for_stitch_without_photo(self):
        response = self.client.get(reverse("stitch_list"))

        self.assertContains(response, 'aria-label="No photo"', count=2)


class StitchDetailTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.owner = User.objects.create_user("owner")
        self.client.force_login(self.alice)

    def test_shows_stitch_with_instructions(self):
        stitch = Stitch.objects.create(
            name="Moss",
            multiple=2,
            edge_stitches=1,
            owner=self.owner,
            is_public=True,
            instructions="Row 1: sc, ch 1.\nRow 2: sc in ch-1 space.",
            source="https://example.com/moss",
        )

        response = self.client.get(reverse("stitch_detail", args=[stitch.pk]))

        self.assertContains(response, "<h1>Moss</h1>", html=True)
        self.assertContains(response, "Row 1: sc, ch 1.<br>Row 2: sc in ch-1 space.")
        self.assertContains(response, 'href="https://example.com/moss"')
        self.assertContains(response, 'aria-label="No photo"')

    def test_hides_other_users_private_stitch(self):
        stitch = Stitch.objects.create(name="Secret", multiple=2, owner=self.owner)

        response = self.client.get(reverse("stitch_detail", args=[stitch.pk]))

        self.assertEqual(response.status_code, 404)

    def test_list_links_to_detail(self):
        stitch = Stitch.objects.create(name="Moss", multiple=2, owner=self.alice)

        response = self.client.get(reverse("stitch_list"))

        self.assertContains(response, reverse("stitch_detail", args=[stitch.pk]))

    @override_settings(MEDIA_ROOT=MEDIA_ROOT)
    def test_shows_photo_credit_with_linked_url(self):
        stitch = Stitch.objects.create(
            name="Moss",
            multiple=2,
            owner=self.alice,
            photo=clean_photo(make_upload()),
            photo_credit="Photo by Jane, CC BY-SA 4.0, https://example.com/photo",
        )

        response = self.client.get(reverse("stitch_detail", args=[stitch.pk]))

        self.assertContains(response, "Photo by Jane, CC BY-SA 4.0")
        self.assertContains(
            response, f'<a href="{stitch.photo.url}" target="_blank" rel="noopener">'
        )
        self.assertContains(response, 'href="https://example.com/photo"')

    def test_hides_photo_credit_without_photo(self):
        stitch = Stitch.objects.create(
            name="Moss", multiple=2, owner=self.alice, photo_credit="Photo by Jane"
        )

        response = self.client.get(reverse("stitch_detail", args=[stitch.pk]))

        self.assertNotContains(response, "Photo by Jane")

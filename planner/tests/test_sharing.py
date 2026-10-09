import shutil
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from planner.models import DiaryEntry
from planner.tests.factories import add_draw, make_project
from stitches.photos import clean_photo
from stitches.tests.test_photos import make_upload

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class SharingTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.project = make_project(
            owner=self.alice,
            name="Rainbow",
            stitches=[("Shell", 6, 1, 1)],
            colors=["red", "blue"],
            stitch_count=150,
        )

    def share(self):
        self.client.post(reverse("project_share", args=[self.project.pk]))
        self.project.refresh_from_db()
        return reverse("shared_project", args=[self.project.share_token])

    def test_toggle_turns_sharing_on_and_off(self):
        url = self.share()
        self.assertTrue(self.project.is_shared)

        self.client.post(reverse("project_share", args=[self.project.pk]))
        self.project.refresh_from_db()

        self.assertFalse(self.project.is_shared)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_shared_page_shows_only_public_fields(self):
        add_draw(self.project, "Shell", "red", rows=3)
        stitch = self.project.project_stitches.get().stitch
        stitch.source = "https://example.com/copied"
        stitch.save()
        DiaryEntry.objects.create(
            project=self.project, text="secret diary text", photo=clean_photo(make_upload())
        )
        self.project.notes = "private notes"
        self.project.save()
        url = self.share()
        self.client.logout()

        response = self.client.get(url)

        self.assertContains(response, "Rainbow")
        self.assertContains(response, "150 stitches per row")
        self.assertContains(response, "Shell")
        self.assertContains(response, "red")
        self.assertContains(response, "blue")
        self.assertContains(response, "red, 3 rows")
        self.assertContains(response, DiaryEntry.objects.get().photo.url)
        for hidden in ["secret diary text", "private notes", "example.com", "at the start", "Reroll"]:
            self.assertNotContains(response, hidden)

    def test_shared_page_links_colors_to_yarn(self):
        self.project.colors.filter(name="red").update(yarn_url="https://example.com/red")
        url = self.share()
        self.client.logout()

        response = self.client.get(url)

        self.assertContains(response, 'href="https://example.com/red"')

    def test_project_page_shows_share_link_when_shared(self):
        url = self.share()

        response = self.client.get(reverse("project_detail", args=[self.project.pk]))

        self.assertContains(response, url)
        self.assertContains(response, "Turn off sharing")

    def test_other_users_cannot_toggle_sharing(self):
        self.client.force_login(User.objects.create_user("bob"))

        response = self.client.post(reverse("project_share", args=[self.project.pk]))

        self.assertEqual(response.status_code, 404)

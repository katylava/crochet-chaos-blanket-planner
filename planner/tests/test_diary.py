import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from planner.models import DiaryEntry
from planner.tests.factories import make_project
from stitches.tests.test_photos import make_upload

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class DiaryTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.project = make_project(owner=self.alice)
        self.url = reverse("diary", args=[self.project.pk])

    def test_empty_diary_prompts_for_yarn_photo(self):
        response = self.client.get(self.url)

        self.assertContains(response, "photo of all the yarns")

    def test_adds_entry_with_text_and_resized_photo(self):
        response = self.client.post(self.url, {"text": "All the yarns", "photo": make_upload()})

        entry = DiaryEntry.objects.get()
        self.assertRedirects(response, self.url)
        self.assertEqual(entry.text, "All the yarns")
        self.assertEqual(Image.open(entry.photo.path).size[0], 1200)

        response = self.client.get(self.url)
        self.assertContains(response, "All the yarns")
        self.assertContains(response, entry.photo.url)
        self.assertNotContains(response, "photo of all the yarns")

    def test_adds_entry_with_only_text(self):
        self.client.post(self.url, {"text": "Row 40 done"})

        self.assertEqual(DiaryEntry.objects.get().text, "Row 40 done")

    def test_requires_text_or_photo(self):
        response = self.client.post(self.url, {"text": ""})

        self.assertContains(response, "Add text, a photo, or both.")
        self.assertFalse(DiaryEntry.objects.exists())

    def test_other_users_get_404(self):
        self.client.force_login(User.objects.create_user("bob"))

        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_project_page_links_to_diary(self):
        response = self.client.get(reverse("project_detail", args=[self.project.pk]))

        self.assertContains(response, self.url)

    def test_rejects_oversized_photo_without_extra_error(self):
        upload = make_upload(name="big.bmp", size=(2000, 1800), fmt="BMP")
        self.assertGreater(upload.size, 10 * 1024 * 1024)

        response = self.client.post(self.url, {"photo": upload})

        self.assertContains(response, "at most 10 MB")
        self.assertNotContains(response, "Add text, a photo, or both.")

    def test_form_comes_first_and_entries_are_newest_first(self):
        DiaryEntry.objects.create(
            project=self.project, text="older", created_at=timezone.now() - timedelta(days=1)
        )
        DiaryEntry.objects.create(project=self.project, text="newer")

        html = self.client.get(self.url).content.decode()

        self.assertLess(html.index("Add entry"), html.index("newer"))
        self.assertLess(html.index("newer"), html.index("older"))

    def test_shows_time_for_local_formatting(self):
        entry = DiaryEntry.objects.create(project=self.project, text="hi")

        response = self.client.get(self.url)

        self.assertContains(response, f'<time datetime="{entry.created_at.isoformat()}" data-local>')

    def test_deletes_entry_after_confirming(self):
        entry = DiaryEntry.objects.create(project=self.project, text="oops")
        delete_url = reverse("diary_entry_delete", args=[entry.pk])

        self.assertContains(self.client.get(self.url), 'data-confirm="Delete this diary entry?"')
        response = self.client.post(delete_url)

        self.assertRedirects(response, self.url)
        self.assertFalse(DiaryEntry.objects.exists())

    def test_other_users_cannot_delete_entries(self):
        entry = DiaryEntry.objects.create(project=self.project, text="mine")
        self.client.force_login(User.objects.create_user("bob"))

        response = self.client.post(reverse("diary_entry_delete", args=[entry.pk]))

        self.assertEqual(response.status_code, 404)

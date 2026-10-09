import shutil
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
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

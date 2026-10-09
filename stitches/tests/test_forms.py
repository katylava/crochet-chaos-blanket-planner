import shutil
import tempfile
from io import BytesIO

import pillow_heif

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from stitches.forms import StitchForm
from stitches.models import Stitch
from stitches.tests.test_photos import make_upload

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class StitchCreateTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)

    def test_creates_private_stitch_with_resized_photo(self):
        response = self.client.post(
            reverse("stitch_create"),
            {
                "name": "Shell",
                "multiple": 6,
                "edge_stitches": 1,
                "colors": 1,
                "source": "https://example.com/shell",
                "photo": make_upload(),
            },
        )

        stitch = Stitch.objects.get()
        self.assertRedirects(response, reverse("stitch_list"))
        self.assertEqual(stitch.owner, self.alice)
        self.assertFalse(stitch.is_public)
        self.assertEqual(Image.open(stitch.photo.path).size[0], 1200)
        self.assertTrue(stitch.photo.name.endswith(".jpg"))

    def test_saves_instructions(self):
        self.client.post(
            reverse("stitch_create"),
            {
                "name": "Moss",
                "multiple": 2,
                "edge_stitches": 0,
                "colors": 1,
                "instructions": "Row 1: sc, ch 1, skip 1.\nRow 2: sc in ch-1 space.",
            },
        )

        self.assertEqual(
            Stitch.objects.get().instructions, "Row 1: sc, ch 1, skip 1.\nRow 2: sc in ch-1 space."
        )

    def test_form_explains_turning_chains(self):
        response = self.client.get(reverse("stitch_create"))

        self.assertContains(response, "Turning chains never count as stitches here")

    def test_accepts_heic_photo(self):
        buffer = BytesIO()
        pillow_heif.from_pillow(Image.new("RGB", (1600, 1600), "blue")).save(buffer)
        heic = SimpleUploadedFile("IMG_0002.HEIC", buffer.getvalue(), content_type="image/heic")

        self.client.post(
            reverse("stitch_create"),
            {"name": "Puff", "multiple": 2, "edge_stitches": 0, "colors": 1, "photo": heic},
        )

        stitch = Stitch.objects.get()
        self.assertEqual(Image.open(stitch.photo.path).format, "JPEG")

    def test_rejects_photo_over_10_mb(self):
        upload = make_upload()
        upload.size = 10 * 1024 * 1024 + 1
        form = StitchForm(
            {"name": "Puff", "multiple": 2, "edge_stitches": 0, "colors": 1},
            {"photo": upload},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("at most 10 MB", form.errors["photo"][0])

import shutil
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from stitches.models import Stitch
from stitches.tests.test_photos import make_upload

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class StitchAdminTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.owner = User.objects.create_superuser("owner", password="pw")
        self.client.force_login(self.owner)

    def test_owner_adds_public_stitch_with_resized_photo(self):
        self.client.post(
            reverse("admin:stitches_stitch_add"),
            {
                "name": "Shell",
                "multiple": 6,
                "edge_stitches": 1,
                "colors": 1,
                "is_public": "on",
                "photo": make_upload(),
            },
        )

        stitch = Stitch.objects.get()
        self.assertEqual(stitch.owner, self.owner)
        self.assertTrue(stitch.is_public)
        self.assertEqual(Image.open(stitch.photo.path).size[0], 1200)

    def test_editing_keeps_original_owner(self):
        alice = User.objects.create_user("alice")
        stitch = Stitch.objects.create(name="Alice's", multiple=2, owner=alice)

        self.client.post(
            reverse("admin:stitches_stitch_change", args=[stitch.pk]),
            {"name": "Alice's", "multiple": 3, "edge_stitches": 0, "colors": 1},
        )

        stitch.refresh_from_db()
        self.assertEqual(stitch.multiple, 3)
        self.assertEqual(stitch.owner, alice)

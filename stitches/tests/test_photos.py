from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image
import pillow_heif

from stitches.photos import clean_photo


def make_upload(name="photo.png", size=(2400, 1600), fmt="PNG"):
    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue())


class CleanPhotoTests(SimpleTestCase):
    def test_resizes_upload_to_1200_wide_jpeg(self):
        result = clean_photo(make_upload())

        image = Image.open(result)
        self.assertEqual(image.format, "JPEG")
        self.assertEqual(image.size, (1200, 800))
        self.assertEqual(result.name, "photo.jpg")

    def test_rejects_upload_over_10_mb(self):
        upload = make_upload()
        upload.size = 10 * 1024 * 1024 + 1

        with self.assertRaisesMessage(ValidationError, "at most 10 MB"):
            clean_photo(upload)

    def test_converts_heic_upload(self):
        buffer = BytesIO()
        pillow_heif.from_pillow(Image.new("RGB", (2400, 1600), "red")).save(buffer)
        upload = SimpleUploadedFile("IMG_0001.HEIC", buffer.getvalue())

        result = clean_photo(upload)

        image = Image.open(result)
        self.assertEqual(image.format, "JPEG")
        self.assertEqual(result.name, "IMG_0001.jpg")

"""Photo upload rules shared by stitch photos and diary progress photos."""

from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

# Pillow reads HEIC only with this plugin. iPhones save photos as HEIC.
register_heif_opener()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
TARGET_WIDTH = 1200


def clean_photo(photo):
    """Return the upload resized to TARGET_WIDTH px wide and saved as JPEG."""
    if photo.size > MAX_UPLOAD_BYTES:
        raise ValidationError("Photos can be at most 10 MB.")
    image = ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
    height = round(image.height * TARGET_WIDTH / image.width)
    image = image.resize((TARGET_WIDTH, height), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    image.save(buffer, "JPEG", quality=85)
    return ContentFile(buffer.getvalue(), name=f"{Path(photo.name).stem}.jpg")

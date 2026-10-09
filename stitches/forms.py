from django import forms
from django.core.files.uploadedfile import UploadedFile

from stitches.models import Stitch
from stitches.photos import clean_photo


class PhotoFormMixin:
    """Resize a newly uploaded `photo`. Keep an unchanged or cleared photo as is."""

    def clean_photo(self):
        photo = self.cleaned_data["photo"]
        if isinstance(photo, UploadedFile):
            return clean_photo(photo)
        return photo


class StitchForm(PhotoFormMixin, forms.ModelForm):
    class Meta:
        model = Stitch
        fields = ["name", "multiple", "edge_stitches", "colors", "source", "photo"]

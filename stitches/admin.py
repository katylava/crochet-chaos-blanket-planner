from django import forms
from django.contrib import admin

from stitches.forms import PhotoFormMixin
from stitches.models import Stitch
from stitches.widgets import NumericInputsMixin


class StitchAdminForm(NumericInputsMixin, PhotoFormMixin, forms.ModelForm):
    class Meta:
        model = Stitch
        fields = [
            "name",
            "multiple",
            "edge_stitches",
            "colors",
            "instructions",
            "source",
            "photo",
            "photo_credit",
            "is_public",
        ]


@admin.register(Stitch)
class StitchAdmin(admin.ModelAdmin):
    form = StitchAdminForm
    list_display = ["name", "multiple", "edge_stitches", "colors", "is_public", "owner"]
    list_filter = ["is_public", "colors"]
    search_fields = ["name"]

    def save_model(self, request, stitch, form, change):
        if not change:
            stitch.owner = request.user
        super().save_model(request, stitch, form, change)

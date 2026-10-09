from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from accounts.models import Invite


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ["note", "created_at", "used_by", "used_at", "signup_link"]
    fields = ["note", "signup_link", "used_by", "used_at"]
    readonly_fields = ["signup_link", "used_by", "used_at"]

    @admin.display(description="Signup link")
    def signup_link(self, invite):
        if invite.pk is None:
            return "Save to create the link."
        if invite.used_at:
            return "Used."
        url = reverse("signup", args=[invite.token])
        return format_html('<a href="{}">{}</a> (copy this link and send it)', url, url)

    def save_model(self, request, invite, form, change):
        if not change:
            invite.created_by = request.user
        super().save_model(request, invite, form, change)

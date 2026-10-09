import secrets

from django.conf import settings
from django.db import models


def new_invite_token():
    return secrets.token_urlsafe(16)


class Invite(models.Model):
    """A single-use signup link. The site owner creates these in the admin."""

    token = models.CharField(max_length=64, unique=True, default=new_invite_token, editable=False)
    note = models.CharField(max_length=200, blank=True, help_text="Who this invite is for.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invites_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_by = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invite",
        editable=False,
    )
    used_at = models.DateTimeField(null=True, blank=True, editable=False)

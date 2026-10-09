from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Invite


class InviteAdminTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser("owner", password="pw")
        self.client.force_login(self.owner)

    def test_adding_invite_sets_creator(self):
        self.client.post(reverse("admin:accounts_invite_add"), {"note": "for alice"})

        invite = Invite.objects.get()
        self.assertEqual(invite.created_by, self.owner)
        self.assertEqual(invite.note, "for alice")

    def test_change_page_shows_signup_link(self):
        invite = Invite.objects.create(created_by=self.owner)

        response = self.client.get(reverse("admin:accounts_invite_change", args=[invite.pk]))

        self.assertContains(response, f'href="/accounts/signup/{invite.token}/"')

    def test_add_page_explains_link_comes_after_save(self):
        response = self.client.get(reverse("admin:accounts_invite_add"))

        self.assertContains(response, "Save to create the link.")

    def test_used_invite_shows_used_instead_of_link(self):
        alice = User.objects.create_user("alice")
        invite = Invite.objects.create(created_by=self.owner, used_by=alice, used_at=timezone.now())

        response = self.client.get(reverse("admin:accounts_invite_change", args=[invite.pk]))

        self.assertContains(response, "Used.")
        self.assertNotContains(response, f"/accounts/signup/{invite.token}/")

    def test_editing_invite_keeps_original_creator(self):
        other_admin = User.objects.create_superuser("other", password="pw")
        invite = Invite.objects.create(created_by=other_admin)

        self.client.post(
            reverse("admin:accounts_invite_change", args=[invite.pk]), {"note": "changed"}
        )

        invite.refresh_from_db()
        self.assertEqual(invite.note, "changed")
        self.assertEqual(invite.created_by, other_admin)

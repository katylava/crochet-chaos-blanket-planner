from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Invite


class SignupTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser("owner", password="pw")
        self.invite = Invite.objects.create(created_by=self.owner)

    def signup(self, token, username="alice"):
        return self.client.post(
            reverse("signup", args=[token]),
            {"username": username, "password1": "a-good-pass-123", "password2": "a-good-pass-123"},
        )

    def test_valid_invite_creates_user_and_uses_invite(self):
        response = self.signup(self.invite.token)

        alice = User.objects.get(username="alice")
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.used_by, alice)
        self.assertIsNotNone(self.invite.used_at)
        self.assertRedirects(response, reverse("project_list"), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), alice.pk)

    def test_used_invite_cannot_sign_up_again(self):
        self.signup(self.invite.token)
        self.client.logout()

        response = self.signup(self.invite.token, username="mallory")

        self.assertEqual(response.status_code, 404)
        self.assertFalse(User.objects.filter(username="mallory").exists())

    def test_get_shows_signup_form(self):
        response = self.client.get(reverse("signup", args=[self.invite.token]))

        self.assertContains(response, "<h1>Sign up</h1>", html=True)
        self.assertContains(response, 'name="password2"')

    def test_login_page_mentions_invites(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, "needs an invite")

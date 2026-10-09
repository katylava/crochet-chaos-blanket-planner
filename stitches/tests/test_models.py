from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from stitches.models import Stitch


class PaddingTests(SimpleTestCase):
    def test_splits_odd_padding_with_extra_at_start(self):
        stitch = Stitch(multiple=6, edge_stitches=1)

        self.assertEqual(stitch.padding(150), (3, 2))


class VisibleToTests(TestCase):
    def test_user_sees_public_stitches_and_own_private_stitches(self):
        owner = User.objects.create_user("owner")
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        public = Stitch.objects.create(name="Shell", multiple=6, owner=owner, is_public=True)
        mine = Stitch.objects.create(name="Mine", multiple=2, owner=alice)
        Stitch.objects.create(name="Bob's", multiple=2, owner=bob)

        self.assertQuerySetEqual(
            Stitch.objects.visible_to(alice), [mine, public], ordered=False
        )


class StrTests(SimpleTestCase):
    def test_str_is_name(self):
        self.assertEqual(str(Stitch(name="Shell")), "Shell")

from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from stitches.models import Stitch


class SeedDevTests(TestCase):
    def run_seed(self):
        call_command("seed_dev", stdout=StringIO())

    def test_creates_admin_and_public_stitches(self):
        self.run_seed()

        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("admin"))
        stitches = Stitch.objects.all()
        self.assertGreaterEqual(stitches.count(), 8)
        self.assertTrue(all(s.is_public and s.owner == admin for s in stitches))
        self.assertTrue(any(s.colors == 2 for s in stitches))
        self.assertGreater(len({(s.multiple, s.edge_stitches) for s in stitches}), 3)
        self.assertTrue(any(sum(s.padding(150)) > 0 for s in stitches))

    def test_running_twice_does_not_duplicate(self):
        self.run_seed()
        count = Stitch.objects.count()

        self.run_seed()

        self.assertEqual(Stitch.objects.count(), count)
        self.assertEqual(User.objects.count(), 1)

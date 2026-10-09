from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from stitches.models import Stitch

# (name, multiple, edge stitches, colors). Values are for development, not authoritative.
STITCHES = [
    ("Single crochet", 1, 0, 1),
    ("Half double crochet", 1, 0, 1),
    ("Double crochet", 1, 0, 1),
    ("Moss stitch", 2, 0, 1),
    ("Puff stitch", 2, 1, 1),
    ("V-stitch", 3, 1, 1),
    ("Waffle stitch", 3, 2, 1),
    ("Shell stitch", 6, 1, 1),
    ("Two-color moss stitch", 2, 0, 2),
    ("Two-color spike stitch", 4, 1, 2),
]


class Command(BaseCommand):
    help = "Create a dev superuser (admin/admin) and public seed stitches."

    def handle(self, *args, **options):
        admin = User.objects.filter(username="admin").first()
        if admin is None:
            admin = User.objects.create_superuser("admin", password="admin")
            self.stdout.write("Created superuser admin with password admin.")
        for name, multiple, edge, colors in STITCHES:
            Stitch.objects.get_or_create(
                name=name,
                owner=admin,
                defaults={
                    "multiple": multiple,
                    "edge_stitches": edge,
                    "colors": colors,
                    "is_public": True,
                },
            )
        self.stdout.write(f"Seeded {len(STITCHES)} stitches.")

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from stitches.models import Stitch

# (name, multiple, edge stitches, colors, instructions). Values are for
# development, not authoritative. Instructions use US crochet terms.
STITCHES = [
    (
        "Single crochet",
        1,
        0,
        1,
        "Insert hook in next stitch, yarn over, pull up a loop.\n"
        "Yarn over, pull through both loops on hook.",
    ),
    (
        "Half double crochet",
        1,
        0,
        1,
        "Yarn over, insert hook in next stitch, yarn over, pull up a loop.\n"
        "Yarn over, pull through all 3 loops on hook.",
    ),
    (
        "Double crochet",
        1,
        0,
        1,
        "Yarn over, insert hook in next stitch, yarn over, pull up a loop.\n"
        "Yarn over, pull through 2 loops. Yarn over, pull through the last 2 loops.",
    ),
    (
        "Moss stitch",
        2,
        0,
        1,
        "Row 1: *sc in next stitch, ch 1, skip 1 stitch*, repeat across.\n"
        "Row 2: *sc in next ch-1 space, ch 1, skip the sc*, repeat across.\n"
        "Repeat row 2.",
    ),
    (
        "Puff stitch",
        2,
        1,
        1,
        "Puff: (yarn over, insert hook in stitch, pull up a loop) 3 times in the same stitch. "
        "Yarn over, pull through all 7 loops, ch 1 to close.\n"
        "Row: *puff in next stitch, skip 1 stitch*, repeat across, sc in last stitch.",
    ),
    (
        "V-stitch",
        3,
        1,
        1,
        "V: (dc, ch 1, dc) in the same stitch.\n"
        "Row 1: *skip 2 stitches, V in next stitch*, repeat across, dc in last stitch.\n"
        "Following rows: V in the ch-1 space of each V below.",
    ),
    (
        "Waffle stitch",
        3,
        2,
        1,
        "Row 1: dc in each stitch.\n"
        "Row 2: dc in first stitch, *front post dc around next stitch, dc in next 2 stitches*, "
        "repeat across, dc in last stitch.\n"
        "Row 3: dc in first stitch, *dc in the post stitch, front post dc around next 2 stitches*, "
        "repeat across, dc in last stitch.\n"
        "Repeat rows 2 and 3.",
    ),
    (
        "Shell stitch",
        6,
        1,
        1,
        "Row 1: sc in first stitch, *skip 2 stitches, 5 dc in next stitch, skip 2 stitches, "
        "sc in next stitch*, repeat across.\n"
        "Row 2: 3 dc in first sc, *sc in center dc of next shell, 5 dc in next sc*, "
        "repeat across, ending with 3 dc in last sc.\n"
        "Row 3: sc in first dc, *5 dc in next sc, sc in center dc of next shell*, repeat across.\n"
        "Repeat rows 2 and 3.",
    ),
    (
        "Two-color moss stitch",
        2,
        0,
        2,
        "Work moss stitch, changing color every row.\n"
        "Carry the unused color up the side instead of cutting it.",
    ),
    (
        "Two-color spike stitch",
        4,
        1,
        2,
        "Work 2 rows of sc in the first color.\n"
        "Change to the second color. Row: *sc in next 3 stitches, sc in next stitch "
        "inserting the hook 2 rows below*, repeat across, sc in last stitch.\n"
        "Work 1 more row of sc, then switch colors and repeat.",
    ),
]


class Command(BaseCommand):
    help = "Create a dev superuser (admin/admin) and public seed stitches."

    def handle(self, *args, **options):
        admin = User.objects.filter(username="admin").first()
        if admin is None:
            admin = User.objects.create_superuser("admin", password="admin")
            self.stdout.write("Created superuser admin with password admin.")
        for name, multiple, edge, colors, instructions in STITCHES:
            stitch, _ = Stitch.objects.get_or_create(
                name=name,
                owner=admin,
                defaults={
                    "multiple": multiple,
                    "edge_stitches": edge,
                    "colors": colors,
                    "is_public": True,
                },
            )
            # Fill instructions only where they're blank, so reseeding keeps edits.
            if not stitch.instructions:
                stitch.instructions = instructions
                stitch.save(update_fields=["instructions"])
        self.stdout.write(f"Seeded {len(STITCHES)} stitches.")

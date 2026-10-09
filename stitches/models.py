from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class StitchQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Public stitches plus the user's own private stitches."""
        return self.filter(models.Q(is_public=True) | models.Q(owner=user))


class Stitch(models.Model):
    name = models.CharField(max_length=200)
    multiple = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='N in "multiple of N + M": the number of stitches in one repeat.',
    )
    edge_stitches = models.PositiveIntegerField(
        default=0,
        help_text=(
            'M in "multiple of N + M". Enter only the extra stitches that appear in every row. '
            "Turning chains never count as stitches here, so if the pattern's M includes a "
            "turning chain, leave it out."
        ),
    )
    colors = models.PositiveSmallIntegerField(
        choices=[(1, "1"), (2, "2")],
        default=1,
        help_text="A two-color stitch needs two different colors per draw.",
    )
    instructions = models.TextField(blank=True, help_text="How to work the stitch.")
    source = models.URLField(blank=True, help_text="The URL the stitch data came from.")
    photo = models.ImageField(upload_to="stitches/", blank=True)
    photo_credit = models.CharField(
        max_length=500,
        blank=True,
        help_text="Who took the photo and its license, if it isn't yours. Links are clickable.",
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)

    objects = StitchQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def padding(self, stitch_count):
        """Return padding stitches as (start, end). Odd padding puts the extra at the start."""
        total = (stitch_count - self.edge_stitches) % self.multiple
        end = total // 2
        return total - end, end

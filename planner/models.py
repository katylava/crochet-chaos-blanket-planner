import secrets
import string

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from stitches.models import Stitch

SHARE_TOKEN_ALPHABET = string.ascii_letters + string.digits


def new_share_token():
    """10 random letters and digits, about 60 bits of randomness."""
    return "".join(secrets.choice(SHARE_TOKEN_ALPHABET) for _ in range(10))


class Project(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=200)
    stitch_count = models.PositiveIntegerField(
        "stitch count per row", validators=[MinValueValidator(1)]
    )
    notes = models.TextField(
        blank=True, help_text="Record your hook size here so you don't forget which one you used."
    )
    min_rows = models.PositiveIntegerField("minimum rows per draw", validators=[MinValueValidator(1)])
    max_rows = models.PositiveIntegerField("maximum rows per draw", validators=[MinValueValidator(1)])
    # The form shows this as "Once a stitch or color is picked, skip it for the next N draws."
    repeat_gap = models.PositiveIntegerField("draws to skip a picked stitch or color")
    share_token = models.CharField(max_length=10, unique=True, null=True, blank=True, editable=False)
    is_shared = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_shared(self, shared):
        """Turn public sharing on or off. The token is generated once and kept."""
        if shared and self.share_token is None:
            self.share_token = new_share_token()
        self.is_shared = shared
        self.save(update_fields=["is_shared", "share_token"])

    def stitch_usage(self):
        """Return the project's stitches, each with draw_count set."""
        draws = list(self.draws.all())
        stitches = list(self.project_stitches.select_related("stitch"))
        for stitch in stitches:
            stitch.draw_count = sum(1 for d in draws if d.stitch_id == stitch.id)
        return stitches

    def color_usage(self):
        """Return the project's colors, each with draw_count set.

        Both colors of a two-color draw count.
        """
        draws = list(self.draws.all())
        colors = list(self.colors.all())
        for color in colors:
            color.draw_count = sum(1 for d in draws if color.id in (d.color1_id, d.color2_id))
        return colors


class ProjectStitch(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_stitches")
    stitch = models.ForeignKey(Stitch, on_delete=models.PROTECT, related_name="project_stitches")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["stitch__name"]
        constraints = [
            models.UniqueConstraint(fields=["project", "stitch"], name="unique_project_stitch")
        ]

    def __str__(self):
        return self.stitch.name


class ProjectColor(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="colors")
    name = models.CharField(max_length=100)
    yarn_url = models.URLField(
        "yarn link", blank=True, help_text="Optional link to the yarn's product page."
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["project", "name"], name="unique_project_color")
        ]

    def __str__(self):
        return self.name


class Draw(models.Model):
    """One draw in a project's history. History order is creation order (id)."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="draws")
    stitch = models.ForeignKey(ProjectStitch, on_delete=models.PROTECT, related_name="draws")
    color1 = models.ForeignKey(ProjectColor, on_delete=models.PROTECT, related_name="+")
    color2 = models.ForeignKey(
        ProjectColor, on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    rows = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["id"]

    def position(self):
        """This draw's 1-based number in the project's history."""
        return self.project.draws.filter(id__lte=self.id).count()

    @property
    def colors_text(self):
        if self.color2:
            return f"{self.color1} and {self.color2}"
        return str(self.color1)

    @property
    def padding_text(self):
        start, end = self.stitch.stitch.padding(self.project.stitch_count)
        if start == 0:
            return "No padding"
        if end == 0:
            return f"{start} at the start"
        return f"{start} at the start, {end} at the end"


class DiaryEntry(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="diary_entries")
    created_at = models.DateTimeField(default=timezone.now)
    text = models.TextField(blank=True)
    photo = models.ImageField(upload_to="progress/", blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "diary entries"

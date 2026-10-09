from django import forms

from planner.models import DiaryEntry, Draw, Project, ProjectColor
from planner.rules import fit_errors, project_fit_errors
from stitches.forms import PhotoFormMixin
from stitches.models import Stitch
from stitches.widgets import NumericInputsMixin


def parse_colors(text):
    """Return color names from text with one name per line, without blanks or repeats."""
    names = []
    for line in text.splitlines():
        name = line.strip()
        if name and name not in names:
            names.append(name)
    return names


class ProjectSettingsForm(NumericInputsMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "stitch_count", "notes", "min_rows", "max_rows", "repeat_gap"]

    def clean(self):
        cleaned = super().clean()
        min_rows, max_rows = cleaned.get("min_rows"), cleaned.get("max_rows")
        if min_rows and max_rows and min_rows > max_rows:
            self.add_error("max_rows", "The maximum can't be less than the minimum.")
        return cleaned


class ProjectEditForm(ProjectSettingsForm):
    def clean(self):
        cleaned = super().clean()
        n = cleaned.get("repeat_gap")
        if n is not None:
            for error in project_fit_errors(self.instance, n=n):
                self.add_error(None, error)
        return cleaned


class ProjectCreateForm(ProjectSettingsForm):
    stitches = forms.ModelMultipleChoiceField(
        queryset=Stitch.objects.none(), widget=forms.CheckboxSelectMultiple
    )
    colors = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text='One color name per line, for example "rust" or "cream".',
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stitches"].queryset = Stitch.objects.visible_to(user)

    def clean_colors(self):
        return parse_colors(self.cleaned_data["colors"])

    def clean(self):
        cleaned = super().clean()
        n = cleaned.get("repeat_gap")
        stitches = cleaned.get("stitches")
        colors = cleaned.get("colors")
        if n is not None and stitches is not None and colors is not None:
            for error in fit_errors(n, list(stitches), len(colors)):
                self.add_error(None, error)
        return cleaned


class DrawForm(NumericInputsMixin, forms.ModelForm):
    """Manual edits. These aren't checked against the repeat rule."""

    class Meta:
        model = Draw
        fields = ["stitch", "color1", "color2", "rows"]
        labels = {"color1": "Color", "color2": "Second color"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.instance.project
        self.fields["stitch"].queryset = project.project_stitches.select_related("stitch")
        self.fields["color1"].queryset = project.colors.all()
        self.fields["color2"].queryset = project.colors.all()

    def clean(self):
        cleaned = super().clean()
        stitch = cleaned.get("stitch")
        color1, color2 = cleaned.get("color1"), cleaned.get("color2")
        if stitch and color1:
            if stitch.stitch.colors == 2 and (color2 is None or color2 == color1):
                self.add_error("color2", f"{stitch} needs two different colors.")
            if stitch.stitch.colors == 1 and color2 is not None:
                self.add_error("color2", f"{stitch} uses one color.")
        return cleaned


class AddStitchForm(forms.Form):
    stitch = forms.ModelChoiceField(queryset=Stitch.objects.none())

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stitch"].queryset = Stitch.objects.visible_to(project.owner).exclude(
            project_stitches__project=project
        )


class ColorForm(forms.ModelForm):
    """Add or edit one of a project's colors. Pass an instance with its project set."""

    class Meta:
        model = ProjectColor
        fields = ["name", "yarn_url"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        others = self.instance.project.colors.exclude(pk=self.instance.pk)
        if others.filter(name=name).exists():
            raise forms.ValidationError(f"This project already has a color named {name}.")
        return name


class DiaryEntryForm(PhotoFormMixin, forms.ModelForm):
    class Meta:
        model = DiaryEntry
        fields = ["text", "photo"]

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("text") and not cleaned.get("photo") and not self.errors:
            raise forms.ValidationError("Add text, a photo, or both.")
        return cleaned

from django.contrib.auth.models import User
from django.test import TestCase

from planner.forms import DrawForm, NewColorFormSet, ProjectCreateForm, ProjectEditForm
from planner.tests.factories import add_draw, make_project
from stitches.admin import StitchAdminForm
from stitches.forms import StitchForm


class NumericInputTests(TestCase):
    """Integer fields render as text with a numeric keypad, so scrolling can't change them."""

    def assert_numeric(self, form, *names):
        for name in names:
            html = str(form[name])
            self.assertIn('type="text"', html, name)
            self.assertIn('inputmode="numeric"', html, name)

    def test_integer_fields_use_numeric_text_inputs(self):
        user = User.objects.create_user("alice")
        project = make_project(owner=user)
        draw = add_draw(project, "Single crochet", "red")

        self.assert_numeric(StitchForm(), "multiple", "edge_stitches")
        self.assert_numeric(StitchAdminForm(), "multiple", "edge_stitches")
        fields = ("stitch_count", "min_rows", "max_rows", "repeat_gap")
        self.assert_numeric(ProjectCreateForm(user=user, colors=NewColorFormSet(prefix="colors")), *fields)
        self.assert_numeric(ProjectEditForm(instance=project), *fields)
        self.assert_numeric(DrawForm(instance=draw), "rows")

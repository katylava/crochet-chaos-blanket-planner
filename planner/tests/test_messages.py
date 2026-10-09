from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from planner.tests.factories import add_draw, make_project
from stitches.models import Stitch


class SuccessMessageTests(TestCase):
    """Actions that don't otherwise show their result say what they did."""

    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.project = make_project(
            owner=self.alice,
            stitches=[("A", 1, 0, 1), ("B", 1, 0, 1)],
            colors=["red", "blue"],
        )

    def post(self, name, *args, data=None):
        response = self.client.post(reverse(name, args=args), data or {}, follow=True)
        return [str(m) for m in response.context["messages"]]

    def test_project_actions_report_success(self):
        a = self.project.project_stitches.get(stitch__name="A")
        red = self.project.colors.get(name="red")
        c = Stitch.objects.create(name="C", multiple=1, owner=self.alice)
        draw = add_draw(self.project, "B", "blue")
        pk = self.project.pk

        self.assertEqual(self.post("project_stitch_toggle", a.pk), ["Deactivated A."])
        self.assertEqual(self.post("project_stitch_toggle", a.pk), ["Activated A."])
        self.assertEqual(self.post("project_stitch_add", pk, data={"stitches": [c.pk]}), ["Added C."])
        self.assertEqual(
            self.post("project_color_add", pk, data={"name": "green"}), ["Added green."]
        )
        self.assertEqual(
            self.post("project_color_edit", red.pk, data={"name": "brick"}), ["Saved brick."]
        )
        self.assertEqual(
            self.post("project_stitch_remove", self.project.project_stitches.get(stitch=c).pk),
            ["Removed C."],
        )
        self.assertEqual(self.post("draw_reroll", draw.pk), ["Rerolled draw 1."])
        self.assertEqual(
            self.post(
                "draw_edit",
                draw.pk,
                data={"stitch": a.pk, "color1": red.pk, "color2": "", "rows": 2},
            ),
            ["Saved draw 1."],
        )
        self.assertEqual(self.post("draw_delete", draw.pk), ["Deleted draw 1."])
        self.assertEqual(self.post("project_share", pk), ["Sharing is on."])
        self.assertEqual(self.post("project_share", pk), ["Sharing is off."])
        self.assertEqual(
            self.post(
                "project_edit",
                pk,
                data={
                    "name": "Blanket",
                    "stitch_count": 150,
                    "min_rows": 1,
                    "max_rows": 4,
                    "repeat_gap": 0,
                },
            ),
            ["Saved settings."],
        )

    def test_stitch_actions_report_success(self):
        data = {"name": "Mine", "multiple": 2, "edge_stitches": 0, "colors": 1}

        self.assertEqual(self.post("stitch_create", data=data), ["Added Mine."])
        mine = Stitch.objects.get(name="Mine")
        self.assertEqual(self.post("stitch_edit", mine.pk, data=data), ["Saved Mine."])
        self.assertEqual(self.post("stitch_delete", mine.pk), ["Deleted Mine."])

    def test_errors_and_successes_are_styled_differently(self):
        response = self.client.post(
            reverse("project_share", args=[self.project.pk]), follow=True
        )

        self.assertContains(response, '<li class="success">Sharing is on.</li>', html=True)

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from planner.models import Project
from planner.tests.factories import make_project
from stitches.models import Stitch


class ProjectListTests(TestCase):
    def test_lists_only_own_projects(self):
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        make_project(owner=alice, name="Alice's blanket")
        make_project(owner=bob, name="Bob's blanket")
        self.client.force_login(alice)

        response = self.client.get(reverse("project_list"))

        self.assertContains(response, "Alice&#x27;s blanket")
        self.assertNotContains(response, "Bob")

    def test_requires_login(self):
        response = self.client.get(reverse("project_list"))

        self.assertRedirects(response, f"{reverse('login')}?next=/", fetch_redirect_response=False)


class ProjectCreateTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.sc = Stitch.objects.create(name="Single crochet", multiple=1, owner=self.alice)
        self.dc = Stitch.objects.create(name="Double crochet", multiple=1, owner=self.alice)

    def post(self, **overrides):
        data = {
            "name": "Rainbow",
            "stitch_count": 150,
            "notes": "5 mm hook",
            "min_rows": 1,
            "max_rows": 4,
            "repeat_gap": 1,
            "stitches": [self.sc.pk, self.dc.pk],
            "colors": "rust\ncream\n",
        }
        data.update(overrides)
        return self.client.post(reverse("project_create"), data)

    def test_creates_project_with_stitches_and_colors(self):
        response = self.post()

        project = Project.objects.get()
        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        self.assertEqual(project.owner, self.alice)
        self.assertEqual(
            sorted(str(s) for s in project.project_stitches.all()),
            ["Double crochet", "Single crochet"],
        )
        self.assertEqual(sorted(str(c) for c in project.colors.all()), ["cream", "rust"])

    def test_blocks_n_that_does_not_fit(self):
        response = self.post(repeat_gap=2)

        self.assertContains(response, "Too few stitches")
        self.assertContains(response, "Too few colors")
        self.assertFalse(Project.objects.exists())

    def test_blocks_max_rows_below_min_rows(self):
        response = self.post(min_rows=5, max_rows=4)

        self.assertContains(response, "The maximum can&#x27;t be less than the minimum.")

    def test_ignores_blank_and_repeated_color_lines(self):
        self.post(colors="rust\n\n rust \ncream")

        self.assertEqual(Project.objects.get().colors.count(), 2)

    def test_form_shows_size_guide_and_hook_hint(self):
        response = self.client.get(reverse("project_create"))

        self.assertContains(response, "Pick a number and embrace the chaos.")
        self.assertContains(response, "Try all your stitches at practice size with scrap yarn")
        self.assertContains(response, "50 to 63")
        self.assertContains(response, "hook size")

    def test_offers_only_visible_stitches(self):
        bob = User.objects.create_user("bob")
        Stitch.objects.create(name="Bob secret", multiple=1, owner=bob)

        response = self.client.get(reverse("project_create"))

        self.assertContains(response, "Single crochet")
        self.assertNotContains(response, "Bob secret")

    def test_requires_stitches(self):
        response = self.post(stitches=[])

        self.assertContains(response, "This field is required.")
        self.assertNotContains(response, "Too few")

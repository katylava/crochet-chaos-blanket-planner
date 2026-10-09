from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from planner.models import Project
from planner.tests.factories import add_draw, make_project
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
        self.assertNotContains(response, "Bob&#x27;s blanket")

    def test_requires_login(self):
        response = self.client.get(reverse("project_list"))

        self.assertRedirects(response, f"{reverse('login')}?next=/", fetch_redirect_response=False)


class ProjectCreateTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.sc = Stitch.objects.create(name="Single crochet", multiple=1, owner=self.alice)
        self.dc = Stitch.objects.create(name="Double crochet", multiple=1, owner=self.alice)

    def post(self, colors=(("rust", ""), ("cream", "")), **overrides):
        """Post the form. `colors` is a list of (name, yarn link) rows."""
        data = {
            "name": "Rainbow",
            "stitch_count": 150,
            "notes": "5 mm hook",
            "min_rows": 1,
            "max_rows": 4,
            "repeat_gap": 1,
            "stitches": [self.sc.pk, self.dc.pk],
            "colors-TOTAL_FORMS": len(colors),
            "colors-INITIAL_FORMS": 0,
        }
        for i, (name, link) in enumerate(colors):
            data[f"colors-{i}-name"] = name
            data[f"colors-{i}-yarn_url"] = link
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

    def test_saves_yarn_links_and_ignores_blank_rows(self):
        self.post(colors=[("rust", "https://example.com/rust"), ("", ""), ("cream", "")])

        colors = {c.name: c.yarn_url for c in Project.objects.get().colors.all()}
        self.assertEqual(colors, {"rust": "https://example.com/rust", "cream": ""})

    def test_rejects_repeated_color_names(self):
        response = self.post(colors=[("rust", ""), (" rust ", ""), ("cream", "")])

        self.assertContains(response, "rust is listed more than once.")
        self.assertFalse(Project.objects.exists())

    def test_rejects_yarn_link_without_name(self):
        response = self.post(colors=[("rust", ""), ("cream", ""), ("", "https://example.com/x")])

        self.assertContains(response, "Add a name for this color.")
        self.assertFalse(Project.objects.exists())

    def test_form_has_add_another_color_button(self):
        response = self.client.get(reverse("project_create"))

        self.assertContains(response, "Add another color")
        self.assertContains(response, 'name="colors-TOTAL_FORMS"')

    def test_form_shows_size_guide_and_hook_hint(self):
        response = self.client.get(reverse("project_create"))

        self.assertContains(response, "Pick a number and embrace the chaos.")
        self.assertContains(response, "Try all your stitches at practice size with scrap yarn")
        self.assertContains(response, "50 to 63")
        self.assertContains(response, "hook size")

    def test_size_guide_follows_stitch_count_field(self):
        html = self.client.get(reverse("project_create")).content.decode()

        guide = html.index("Pick a number and embrace the chaos.")
        self.assertLess(html.index('name="stitch_count"'), guide)
        self.assertLess(guide, html.index('name="min_rows"'))

    def test_new_project_starts_with_default_draw_settings(self):
        form = self.client.get(reverse("project_create")).context["form"]

        self.assertEqual(
            (form["min_rows"].value(), form["max_rows"].value(), form["repeat_gap"].value()),
            (1, 4, 2),
        )

    def test_stitch_choices_show_multiple_and_colors(self):
        Stitch.objects.create(name="Moss", multiple=2, edge_stitches=1, colors=2, owner=self.alice)

        response = self.client.get(reverse("project_create"))

        self.assertContains(response, "Moss (multiple of 2 + 1, 2 colors)")
        self.assertContains(response, "Single crochet (multiple of 1 + 0, 1 color)")

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


class ProjectDetailTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.project = make_project(
            owner=self.alice,
            stitches=[("Shell", 6, 1, 1), ("Moss", 2, 0, 2)],
            colors=["red", "blue"],
            notes="5 mm hook",
        )
        self.draw = add_draw(self.project, "Shell", "red", rows=3)

    def get(self):
        return self.client.get(reverse("project_detail", args=[self.project.pk]))

    def section(self, response, element_id):
        """Return the HTML of the element with this id, up to its closing tag."""
        html = response.content.decode()
        start = html.index(f'id="{element_id}"')
        tag = html.rindex("<", 0, start)
        name = html[tag + 1 : start].split()[0]
        return html[tag : html.index(f"</{name}>", start)]

    def test_shows_settings_in_plain_words(self):
        self.project.repeat_gap = 2
        self.project.save()

        response = self.get()

        self.assertContains(response, "5 mm hook")
        self.assertContains(response, "150 stitches per row")
        self.assertContains(response, "1 to 4 rows per draw")
        self.assertContains(response, "No stitch or color repeats within 2 draws")
        self.assertNotContains(response, "N =")

    def test_zero_gap_says_repeats_are_allowed(self):
        response = self.get()

        self.assertContains(response, "Stitches and colors can repeat in back-to-back draws")

    def test_draw_button_comes_before_stitch_and_color_management(self):
        html = self.get().content.decode()

        self.assertLess(html.index(">Draw</button>"), html.index('id="active-stitches"'))
        self.assertLess(html.index(">Draw</button>"), html.index('id="active-colors"'))

    def test_highlights_latest_draw(self):
        add_draw(self.project, "Moss", "blue", "red", rows=2)

        latest = self.section(self.get(), "latest-draw")

        self.assertIn("Draw 2", latest)
        self.assertIn("Moss", latest)
        self.assertIn("blue and red", latest)

    def test_history_lists_earlier_draws_newest_first(self):
        add_draw(self.project, "Moss", "blue", "red", rows=2)
        add_draw(self.project, "Shell", "blue", rows=2)

        history = self.section(self.get(), "history")

        self.assertLess(history.index("Draw 2"), history.index("Draw 1"))
        self.assertNotIn("Draw 3", history)

    def test_links_draw_actions(self):
        response = self.get()

        for name in ["draw_edit", "draw_delete", "draw_reroll"]:
            self.assertContains(response, reverse(name, args=[self.draw.pk]))

    def test_destructive_actions_ask_for_confirmation(self):
        latest = add_draw(self.project, "Moss", "blue", "red", rows=2)

        response = self.get()

        self.assertContains(response, 'data-confirm="Delete draw 2?"')
        self.assertContains(response, 'data-confirm="Reroll draw 1?')
        self.assertNotContains(response, 'data-confirm="Reroll draw 2?')
        self.assertContains(response, reverse("draw_reroll", args=[latest.pk]))

    def test_remove_asks_for_confirmation(self):
        self.project.colors.create(name="unused")

        response = self.get()

        self.assertContains(response, 'data-confirm="Remove unused from this project?"')

    def test_tables_show_active_items_with_draw_counts(self):
        response = self.get()

        stitches = self.section(response, "active-stitches")
        shell_url = reverse("stitch_detail", args=[self.draw.stitch.stitch_id])
        self.assertInHTML(f'<td><a href="{shell_url}">Shell</a></td><td>1</td>', stitches)
        colors = self.section(response, "active-colors")
        self.assertIn("red", colors)
        self.assertNotIn("Status", stitches + colors)

    def test_inactive_items_are_listed_separately(self):
        self.project.project_stitches.filter(stitch__name="Moss").update(active=False)
        self.project.colors.filter(name="blue").update(active=False)

        response = self.get()

        self.assertNotIn("Moss", self.section(response, "active-stitches"))
        self.assertIn("Moss", self.section(response, "inactive-stitches"))
        self.assertNotIn("blue", self.section(response, "active-colors"))
        self.assertIn("blue", self.section(response, "inactive-colors"))

    def test_project_list_links_to_project_and_new_project(self):
        response = self.client.get(reverse("project_list"))

        self.assertContains(response, reverse("project_detail", args=[self.project.pk]))
        self.assertContains(response, reverse("project_create"))

    def test_other_users_get_404(self):
        self.client.force_login(User.objects.create_user("bob"))

        self.assertEqual(self.get().status_code, 404)


class ProjectEditTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice")
        self.client.force_login(self.alice)
        self.project = make_project(
            owner=self.alice,
            stitches=[("A", 1, 0, 1), ("B", 1, 0, 1), ("C", 1, 0, 1)],
            colors=["red", "blue", "cream"],
            repeat_gap=1,
        )

    def post(self, repeat_gap):
        return self.client.post(
            reverse("project_edit", args=[self.project.pk]),
            {"name": "Renamed", "stitch_count": 120, "min_rows": 2, "max_rows": 3, "repeat_gap": repeat_gap},
        )

    def test_saves_settings(self):
        response = self.post(repeat_gap=2)

        self.project.refresh_from_db()
        self.assertRedirects(response, reverse("project_detail", args=[self.project.pk]))
        self.assertEqual((self.project.name, self.project.repeat_gap), ("Renamed", 2))

    def test_fit_check_counts_only_active_stitches(self):
        self.project.project_stitches.filter(stitch__name="C").update(active=False)

        response = self.post(repeat_gap=2)

        self.assertContains(response, "Too few stitches")
        self.project.refresh_from_db()
        self.assertEqual(self.project.repeat_gap, 1)

    def test_edit_page_shows_size_guide(self):
        response = self.client.get(reverse("project_edit", args=[self.project.pk]))

        self.assertContains(response, "Edit Blanket")
        self.assertContains(response, "Pick a number and embrace the chaos.")

    def test_requires_n(self):
        response = self.post(repeat_gap="")

        self.assertContains(response, "This field is required.")

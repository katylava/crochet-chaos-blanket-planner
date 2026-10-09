from django.contrib.auth.models import User

from planner.models import Draw, Project, ProjectColor, ProjectStitch
from stitches.models import Stitch


def make_project(
    owner=None,
    stitches=(("Single crochet", 1, 0, 1),),
    colors=("red",),
    repeat_gap=0,
    **fields,
):
    """Create a project. Each stitch is (name, multiple, edge stitches, colors)."""
    owner = owner or User.objects.create_user("maker")
    defaults = {"name": "Blanket", "stitch_count": 150, "min_rows": 1, "max_rows": 4}
    project = Project.objects.create(
        owner=owner, repeat_gap=repeat_gap, **{**defaults, **fields}
    )
    for name, multiple, edge, color_count in stitches:
        stitch = Stitch.objects.create(
            name=name, multiple=multiple, edge_stitches=edge, colors=color_count, owner=owner
        )
        ProjectStitch.objects.create(project=project, stitch=stitch)
    for color in colors:
        ProjectColor.objects.create(project=project, name=color)
    return project


def add_draw(project, stitch, *colors, rows=2):
    color_objs = [project.colors.get(name=name) for name in colors]
    return Draw.objects.create(
        project=project,
        stitch=project.project_stitches.get(stitch__name=stitch),
        color1=color_objs[0],
        color2=color_objs[1] if len(color_objs) > 1 else None,
        rows=rows,
    )

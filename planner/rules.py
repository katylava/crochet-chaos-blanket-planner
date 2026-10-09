"""Draw rules from the spec: when N fits a project, and the repeat rule."""

import random

from planner.models import Draw


class DrawError(Exception):
    pass


def fit_errors(n, stitches, color_count):
    """Return messages saying why N doesn't fit the active stitches and colors."""
    errors = []
    if len(stitches) <= n:
        errors.append(
            f"Too few stitches: with N = {n}, the project needs at least {n + 1} active stitches."
        )
    if any(stitch.colors == 2 for stitch in stitches):
        # The last N draws can block up to 2N colors, and the next draw can need 2 more.
        colors_needed = 2 * n + 2
        condition = f"N = {n} and a two-color stitch"
    else:
        colors_needed = n + 1
        condition = f"N = {n}"
    if color_count < colors_needed:
        errors.append(
            f"Too few colors: with {condition}, "
            f"the project needs at least {colors_needed} active colors."
        )
    return errors


def blocked(project, before=None):
    """Return (stitches, colors) used in the N draws before `before`, or the last N draws.

    Both are sets of ProjectStitch and ProjectColor objects.
    """
    draws = project.draws.order_by("-id")
    if before is not None:
        draws = draws.filter(id__lt=before.id)
    recent = draws[: project.repeat_gap]
    stitches = set()
    colors = set()
    for draw in recent:
        stitches.add(draw.stitch)
        colors.add(draw.color1)
        if draw.color2:
            colors.add(draw.color2)
    return stitches, colors


def pick_draw(project, before=None, rng=random):
    """Return a new unsaved random Draw that follows the repeat rule.

    `before` is the draw being rerolled. The repeat rule then checks the N draws
    before it instead of the last N draws.
    """
    blocked_stitches, blocked_colors = blocked(project, before)
    stitches = [s for s in project.project_stitches.filter(active=True) if s not in blocked_stitches]
    colors = [c for c in project.colors.filter(active=True) if c not in blocked_colors]
    stitches = [s for s in stitches if s.stitch.colors <= len(colors)]
    if not stitches:
        raise DrawError(
            "No stitch and color combination can be drawn. "
            "Activate more stitches or colors, or lower N."
        )
    stitch = rng.choice(stitches)
    picked = rng.sample(colors, stitch.stitch.colors)
    return Draw(
        project=project,
        stitch=stitch,
        color1=picked[0],
        color2=picked[1] if len(picked) > 1 else None,
        rows=rng.randint(project.min_rows, project.max_rows),
    )

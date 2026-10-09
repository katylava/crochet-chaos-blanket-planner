from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from planner.forms import (
    AddStitchForm,
    ColorForm,
    DiaryEntryForm,
    DrawForm,
    NewColorFormSet,
    ProjectCreateForm,
    ProjectEditForm,
)
from planner.models import DiaryEntry, Draw, Project, ProjectColor, ProjectStitch
from planner.rules import DrawError, pick_draw, project_fit_errors
from planner.size_guide import GUIDE_TEXT, SIZES


def own_project(request, pk):
    return get_object_or_404(Project, pk=pk, owner=request.user)


def own_draw(request, pk):
    return get_object_or_404(Draw, pk=pk, project__owner=request.user)


@login_required
def project_list(request):
    projects = request.user.projects.all()
    return render(request, "planner/project_list.html", {"projects": projects})


@login_required
def project_create(request):
    colors = NewColorFormSet(request.POST or None, prefix="colors")
    form = ProjectCreateForm(request.POST or None, user=request.user, colors=colors)
    # Validate both so errors show for the settings and the color rows together.
    form_valid, colors_valid = form.is_valid(), colors.is_valid()
    if form_valid and colors_valid:
        with transaction.atomic():
            form.instance.owner = request.user
            project = form.save()
            for stitch in form.cleaned_data["stitches"]:
                ProjectStitch.objects.create(project=project, stitch=stitch)
            for name, yarn_url in colors.colors():
                ProjectColor.objects.create(project=project, name=name, yarn_url=yarn_url)
        return redirect("project_detail", project.pk)
    return render(
        request,
        "planner/project_form.html",
        {"form": form, "colors": colors, "sizes": SIZES, "guide_text": GUIDE_TEXT},
    )


@login_required
def project_edit(request, pk):
    project = own_project(request, pk)
    form = ProjectEditForm(request.POST or None, instance=project)
    if form.is_valid():
        form.save()
        messages.success(request, "Saved settings.")
        return redirect("project_detail", project.pk)
    return render(
        request,
        "planner/project_form.html",
        {"form": form, "sizes": SIZES, "guide_text": GUIDE_TEXT},
    )


@login_required
def project_detail(request, pk):
    project = own_project(request, pk)
    draws = list(project.draws.select_related("stitch__stitch", "color1", "color2"))
    for number, draw in enumerate(draws, start=1):
        draw.number = number
    stitches = project.stitch_usage()
    colors = project.color_usage()
    return render(
        request,
        "planner/project_detail.html",
        {
            "project": project,
            "latest": draws[-1] if draws else None,
            "history": draws[-2::-1],
            "active_stitches": [s for s in stitches if s.active],
            "inactive_stitches": [s for s in stitches if not s.active],
            "active_colors": [c for c in colors if c.active],
            "inactive_colors": [c for c in colors if not c.active],
            "add_stitch_form": AddStitchForm(project=project),
            "color_form": ColorForm(instance=ProjectColor(project=project)),
        },
    )


@login_required
@require_POST
def draw_create(request, pk):
    project = own_project(request, pk)
    try:
        pick_draw(project).save()
    except DrawError as error:
        messages.error(request, str(error))
    return redirect("project_detail", project.pk)


@login_required
@require_POST
def draw_delete(request, pk):
    draw = own_draw(request, pk)
    number = draw.position()
    draw.delete()
    messages.success(request, f"Deleted draw {number}.")
    return redirect("project_detail", draw.project_id)


@login_required
@require_POST
def draw_reroll(request, pk):
    draw = own_draw(request, pk)
    try:
        new = pick_draw(draw.project, before=draw)
    except DrawError as error:
        messages.error(request, str(error))
    else:
        draw.stitch, draw.color1, draw.color2, draw.rows = (
            new.stitch,
            new.color1,
            new.color2,
            new.rows,
        )
        draw.save()
        messages.success(request, f"Rerolled draw {draw.position()}.")
    return redirect("project_detail", draw.project_id)


@login_required
def draw_edit(request, pk):
    draw = own_draw(request, pk)
    form = DrawForm(request.POST or None, instance=draw)
    if form.is_valid():
        form.save()
        messages.success(request, f"Saved draw {draw.position()}.")
        return redirect("project_detail", draw.project_id)
    return render(request, "planner/draw_form.html", {"form": form, "draw": draw})


def toggle_active(request, item):
    """Flip a ProjectStitch or ProjectColor. Block deactivation if N would no longer fit."""
    if item.active:
        errors = project_fit_errors(item.project, deactivating=item)
        if errors:
            for error in errors:
                messages.error(request, f"Can't deactivate {item}. {error}")
            return redirect("project_detail", item.project_id)
    item.active = not item.active
    item.save(update_fields=["active"])
    messages.success(request, f"{'Activated' if item.active else 'Deactivated'} {item}.")
    return redirect("project_detail", item.project_id)


@login_required
@require_POST
def project_stitch_toggle(request, pk):
    item = get_object_or_404(ProjectStitch, pk=pk, project__owner=request.user)
    return toggle_active(request, item)


@login_required
@require_POST
def project_color_toggle(request, pk):
    item = get_object_or_404(ProjectColor, pk=pk, project__owner=request.user)
    return toggle_active(request, item)


def report_form_errors(request, form):
    for errors in form.errors.values():
        for error in errors:
            messages.error(request, error)


@login_required
@require_POST
def project_stitch_add(request, pk):
    project = own_project(request, pk)
    form = AddStitchForm(request.POST, project=project)
    if form.is_valid():
        ProjectStitch.objects.create(project=project, stitch=form.cleaned_data["stitch"])
        messages.success(request, f"Added {form.cleaned_data['stitch']}.")
    else:
        report_form_errors(request, form)
    return redirect("project_detail", project.pk)


@login_required
@require_POST
def project_color_add(request, pk):
    project = own_project(request, pk)
    form = ColorForm(request.POST, instance=ProjectColor(project=project))
    if form.is_valid():
        color = form.save()
        messages.success(request, f"Added {color}.")
    else:
        report_form_errors(request, form)
    return redirect("project_detail", project.pk)


@login_required
def project_color_edit(request, pk):
    color = get_object_or_404(ProjectColor, pk=pk, project__owner=request.user)
    form = ColorForm(request.POST or None, instance=color)
    if form.is_valid():
        form.save()
        messages.success(request, f"Saved {color}.")
        return redirect("project_detail", color.project_id)
    # Show the saved name in the heading even when the form has an invalid new one.
    saved_name = ProjectColor.objects.get(pk=color.pk).name
    return render(
        request,
        "planner/color_form.html",
        {"form": form, "color": color, "saved_name": saved_name},
    )


def remove_item(request, item):
    """Remove a ProjectStitch or ProjectColor that no draw uses, if N still fits."""
    errors = project_fit_errors(item.project, deactivating=item) if item.active else []
    if errors:
        for error in errors:
            messages.error(request, f"Can't remove {item}. {error}")
        return redirect("project_detail", item.project_id)
    try:
        item.delete()
    except ProtectedError:
        messages.error(request, f"{item} is used in a draw. Deactivate it instead.")
    else:
        messages.success(request, f"Removed {item}.")
    return redirect("project_detail", item.project_id)


@login_required
@require_POST
def project_stitch_remove(request, pk):
    item = get_object_or_404(ProjectStitch, pk=pk, project__owner=request.user)
    return remove_item(request, item)


@login_required
@require_POST
def project_color_remove(request, pk):
    item = get_object_or_404(ProjectColor, pk=pk, project__owner=request.user)
    return remove_item(request, item)


@login_required
def diary(request, pk):
    project = own_project(request, pk)
    entry = DiaryEntry(project=project)
    form = DiaryEntryForm(request.POST or None, request.FILES or None, instance=entry)
    if form.is_valid():
        form.save()
        return redirect("diary", project.pk)
    return render(
        request,
        "planner/diary.html",
        {"project": project, "entries": project.diary_entries.all(), "form": form},
    )


@login_required
@require_POST
def project_share(request, pk):
    project = own_project(request, pk)
    project.set_shared(not project.is_shared)
    messages.success(request, f"Sharing is {'on' if project.is_shared else 'off'}.")
    return redirect("project_detail", project.pk)


def shared_project(request, token):
    """Read-only page for anyone with the link. Shows only what the spec allows."""
    project = get_object_or_404(Project, share_token=token, is_shared=True)
    return render(
        request,
        "planner/shared_project.html",
        {
            "project": project,
            "stitches": project.project_stitches.select_related("stitch"),
            "colors": project.colors.all(),
            "draws": project.draws.select_related("stitch__stitch", "color1", "color2"),
            "photos": project.diary_entries.exclude(photo=""),
        },
    )

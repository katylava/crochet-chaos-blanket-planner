from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from planner.forms import (
    AddColorsForm,
    AddStitchForm,
    DrawForm,
    ProjectCreateForm,
    ProjectEditForm,
)
from planner.models import Draw, Project, ProjectColor, ProjectStitch
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
    form = ProjectCreateForm(request.POST or None, user=request.user)
    if form.is_valid():
        with transaction.atomic():
            form.instance.owner = request.user
            project = form.save()
            for stitch in form.cleaned_data["stitches"]:
                ProjectStitch.objects.create(project=project, stitch=stitch)
            for name in form.cleaned_data["colors"]:
                ProjectColor.objects.create(project=project, name=name)
        return redirect("project_detail", project.pk)
    return render(
        request,
        "planner/project_form.html",
        {"form": form, "sizes": SIZES, "guide_text": GUIDE_TEXT},
    )


@login_required
def project_edit(request, pk):
    project = own_project(request, pk)
    form = ProjectEditForm(request.POST or None, instance=project)
    if form.is_valid():
        form.save()
        return redirect("project_detail", project.pk)
    return render(
        request,
        "planner/project_form.html",
        {"form": form, "sizes": SIZES, "guide_text": GUIDE_TEXT},
    )


@login_required
def project_detail(request, pk):
    project = own_project(request, pk)
    draws = project.draws.select_related("stitch__stitch", "color1", "color2")
    return render(
        request,
        "planner/project_detail.html",
        {
            "project": project,
            "draws": draws,
            "stitch_usage": project.stitch_usage(),
            "color_usage": project.color_usage(),
            "add_stitch_form": AddStitchForm(project=project),
            "add_colors_form": AddColorsForm(),
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
    draw.delete()
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
    return redirect("project_detail", draw.project_id)


@login_required
def draw_edit(request, pk):
    draw = own_draw(request, pk)
    form = DrawForm(request.POST or None, instance=draw)
    if form.is_valid():
        form.save()
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
    else:
        report_form_errors(request, form)
    return redirect("project_detail", project.pk)


@login_required
@require_POST
def project_color_add(request, pk):
    project = own_project(request, pk)
    form = AddColorsForm(request.POST)
    if form.is_valid():
        for name in form.cleaned_data["colors"]:
            ProjectColor.objects.get_or_create(project=project, name=name)
    else:
        report_form_errors(request, form)
    return redirect("project_detail", project.pk)


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

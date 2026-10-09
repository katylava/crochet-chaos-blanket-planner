from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from planner.forms import DrawForm, ProjectCreateForm
from planner.models import Draw, Project, ProjectColor, ProjectStitch
from planner.rules import DrawError, pick_draw
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
def project_detail(request, pk):
    project = own_project(request, pk)
    draws = project.draws.select_related("stitch__stitch", "color1", "color2")
    return render(request, "planner/project_detail.html", {"project": project, "draws": draws})


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

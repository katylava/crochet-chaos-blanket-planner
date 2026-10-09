from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from stitches.forms import StitchForm

from stitches.models import Stitch


@login_required
def stitch_list(request):
    stitches = Stitch.objects.visible_to(request.user)
    return render(request, "stitches/stitch_list.html", {"stitches": stitches})


@login_required
def stitch_create(request):
    form = StitchForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.instance.owner = request.user
        form.save()
        return redirect("stitch_list")
    return render(request, "stitches/stitch_form.html", {"form": form})


def own_private_stitch(request, pk):
    """Users manage only their own private stitches. Public ones belong to the admin site."""
    return get_object_or_404(Stitch, pk=pk, owner=request.user, is_public=False)


@login_required
def stitch_edit(request, pk):
    stitch = own_private_stitch(request, pk)
    form = StitchForm(request.POST or None, request.FILES or None, instance=stitch)
    if form.is_valid():
        form.save()
        return redirect("stitch_list")
    return render(request, "stitches/stitch_form.html", {"form": form})


@login_required
@require_POST
def stitch_delete(request, pk):
    stitch = own_private_stitch(request, pk)
    try:
        stitch.delete()
    except ProtectedError:
        messages.error(request, f"{stitch.name} is used in a project, so it can't be deleted.")
    return redirect("stitch_list")

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from stitches.forms import StitchForm

from stitches.models import Stitch


@login_required
def stitch_list(request):
    stitches = Stitch.objects.visible_to(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        stitches = stitches.filter(name__icontains=q)
    mine = request.GET.get("mine") == "1"
    if mine:
        stitches = stitches.filter(owner=request.user, is_public=False)
    page = Paginator(stitches, 50).get_page(request.GET.get("page"))
    # The query string without the page number, for the paging links.
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "stitches/stitch_list.html",
        {"page": page, "q": q, "mine": mine, "query": params.urlencode()},
    )


@login_required
def stitch_detail(request, pk):
    stitch = get_object_or_404(Stitch.objects.visible_to(request.user), pk=pk)
    return render(request, "stitches/stitch_detail.html", {"stitch": stitch})


@login_required
def stitch_create(request):
    form = StitchForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.instance.owner = request.user
        stitch = form.save()
        messages.success(request, f"Added {stitch}.")
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
        messages.success(request, f"Saved {stitch}.")
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
    else:
        messages.success(request, f"Deleted {stitch.name}.")
    return redirect("stitch_list")

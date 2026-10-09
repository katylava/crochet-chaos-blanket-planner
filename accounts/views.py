from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Invite


def signup(request, token):
    invite = get_object_or_404(Invite, token=token, used_at__isnull=True)
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        invite.used_by = user
        invite.used_at = timezone.now()
        invite.save()
        login(request, user)
        return redirect("project_list")
    return render(request, "accounts/signup.html", {"form": form})

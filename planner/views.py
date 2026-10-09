from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def project_list(request):
    projects = request.user.projects.all()
    return render(request, "planner/project_list.html", {"projects": projects})

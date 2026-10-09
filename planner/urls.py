from django.urls import path

from planner import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
]

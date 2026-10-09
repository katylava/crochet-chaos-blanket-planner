from django.urls import path

from planner import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/draw/", views.draw_create, name="draw_create"),
    path("draws/<int:pk>/delete/", views.draw_delete, name="draw_delete"),
    path("draws/<int:pk>/reroll/", views.draw_reroll, name="draw_reroll"),
    path("draws/<int:pk>/edit/", views.draw_edit, name="draw_edit"),
]

from django.urls import path

from planner import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/diary/", views.diary, name="diary"),
    path("projects/<int:pk>/share/", views.project_share, name="project_share"),
    path("s/<str:token>/", views.shared_project, name="shared_project"),
    path("projects/<int:pk>/draw/", views.draw_create, name="draw_create"),
    path("projects/<int:pk>/stitches/add/", views.project_stitch_add, name="project_stitch_add"),
    path("projects/<int:pk>/colors/add/", views.project_color_add, name="project_color_add"),
    path(
        "project-stitches/<int:pk>/remove/",
        views.project_stitch_remove,
        name="project_stitch_remove",
    ),
    path(
        "project-colors/<int:pk>/remove/", views.project_color_remove, name="project_color_remove"
    ),
    path("project-stitches/<int:pk>/toggle/", views.project_stitch_toggle, name="project_stitch_toggle"),
    path("project-colors/<int:pk>/toggle/", views.project_color_toggle, name="project_color_toggle"),
    path("draws/<int:pk>/delete/", views.draw_delete, name="draw_delete"),
    path("draws/<int:pk>/reroll/", views.draw_reroll, name="draw_reroll"),
    path("draws/<int:pk>/edit/", views.draw_edit, name="draw_edit"),
]

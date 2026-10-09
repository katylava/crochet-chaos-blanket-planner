from django.urls import path

from stitches import views

urlpatterns = [
    path("", views.stitch_list, name="stitch_list"),
    path("new/", views.stitch_create, name="stitch_create"),
    path("<int:pk>/", views.stitch_detail, name="stitch_detail"),
    path("<int:pk>/edit/", views.stitch_edit, name="stitch_edit"),
    path("<int:pk>/delete/", views.stitch_delete, name="stitch_delete"),
]

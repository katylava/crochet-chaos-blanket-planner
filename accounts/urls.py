from django.urls import path

from accounts import views

urlpatterns = [
    path("signup/<str:token>/", views.signup, name="signup"),
]

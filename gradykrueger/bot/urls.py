from django.urls import path

from . import views

urlpatterns = [
    path("bot", views.handler, name="gradykrueger_hook"),
    path("register", views.register, name="register"),
]

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("account.urls")),
    path("", include("tasks.urls")),
    path("", include("subscription.urls")),
    path("", include("olympiad.urls")),
]

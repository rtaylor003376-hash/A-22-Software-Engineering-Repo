from django.contrib import admin
from django.urls import include, path

from accounts import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", views.profile, name="profile"),
    path("login/", views.login_view, name="login"),
]

from django.contrib import admin
from django.urls import include, path

from accounts import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("profile/", views.profile, name="profile"),
]

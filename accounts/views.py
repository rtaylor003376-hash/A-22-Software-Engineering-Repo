from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")
    return render(request, "login.html")


@login_required
def profile(request):
    context = {
        "name": request.user.get_full_name(),
        "email": request.user.email,
        "role": request.user.get_role_display(),
        "is_moderator": request.user.role == "moderator",
        "joined": request.user.date_joined,
    }
    return render(request, "profile.html", context)

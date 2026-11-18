from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import RatingForm
from .models import Shop

FILTERS = [
    ["fast", "Fast Wi-Fi"],
    ["outlets", "Outlets"],
    ["seating", "Seating"],
    ["quiet", "Quiet"],
    ["open", "Open now"],
]

TIMES = [
    ["now", "Right now"],
    ["morning", "Morning"],
    ["afternoon", "Afternoon"],
    ["evening", "Evening"],
]


def current_time_of_day():
    hour = timezone.localtime(timezone=ZoneInfo("America/New_York")).hour
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def speed_label(download):
    if download is None:
        return "No data"
    if download >= 50:
        return "Fast"
    if download >= 25:
        return "OK"
    return "Slow"


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "login.html")


@login_required
def home(request):
    search = request.GET.get("q", "").lower()
    time = request.GET.get("time", "now")
    if time not in ["now", "morning", "afternoon", "evening"]:
        time = "now"
    active = []
    for key, label in FILTERS:
        if request.GET.get(key) == "1":
            active.append(key)

    slot = current_time_of_day() if time == "now" else time
    all_shops = Shop.objects.annotate(
        download=Avg("ratings__download", filter=Q(ratings__time_of_day=slot)),
        upload=Avg("ratings__upload", filter=Q(ratings__time_of_day=slot)),
        rating_count=Count("ratings"),
        last_rating=Max("ratings__created"),
    )

    shops = []
    for shop in all_shops:
        shop.label = speed_label(shop.download)

        if search not in shop.name.lower():
            continue
        if "fast" in active and shop.label != "Fast":
            continue
        if "outlets" in active and shop.outlets == "few":
            continue
        if "seating" in active and shop.seating == "limited":
            continue
        if "quiet" in active and not shop.quiet:
            continue
        if "open" in active and not shop.open:
            continue
        shops.append(shop)

    first_name = request.user.first_name
    if first_name == "":
        first_name = request.user.username
    initials = first_name[:1] + request.user.last_name[:1]

    context = {
        "shops": shops,
        "is_moderator": request.user.role == "moderator",
        "first_name": first_name,
        "initials": initials.upper(),
        "search": request.GET.get("q", ""),
        "view": request.GET.get("view", "list"),
        "time": time,
        "times": TIMES,
        "filters": FILTERS,
        "active": active,
    }
    return render(request, "home.html", context)


@login_required
def profile(request):
    context = {
        "name": request.user.get_full_name(),
        "email": request.user.email,
        "role": request.user.get_role_display(),
        "joined": request.user.date_joined,
    }
    return render(request, "profile.html", context)


@login_required
def rate(request):
    if request.method == "POST":
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.time_of_day = current_time_of_day()
            rating.save()
            messages.success(request, f"Thanks! Your speed test for {rating.shop} was saved.")
            return redirect("home")
    else:
        form = RatingForm()
    return render(request, "rate.html", {"form": form})

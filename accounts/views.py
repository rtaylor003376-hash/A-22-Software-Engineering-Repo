from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

SHOPS = [
    {
        "name": "Bodo's (Corner)",
        "distance": 0.1,
        "speeds": {
            "now": [19, 5],
            "morning": [14, 4],
            "afternoon": [19, 5],
            "evening": [22, 6],
        },
        "seating": "plenty",
        "outlets": "few",
        "noise": "Noise: loud",
        "quiet": False,
        "ratings": 12,
        "last_test": "5 hrs ago",
        "open": False,
        "hours": "closed · opens 7 AM",
    },
    {
        "name": "Grit (Corner)",
        "distance": 0.2,
        "speeds": {
            "now": [52, 14],
            "morning": [58, 16],
            "afternoon": [52, 14],
            "evening": [44, 12],
        },
        "seating": "plenty",
        "outlets": "some",
        "noise": "Quiet upstairs",
        "quiet": True,
        "ratings": 38,
        "last_test": "20 min ago",
        "open": True,
        "hours": "open till 7 PM",
    },
    {
        "name": "Starbucks (Corner)",
        "distance": 0.2,
        "speeds": {
            "now": [31, 9],
            "morning": [36, 10],
            "afternoon": [31, 9],
            "evening": [27, 8],
        },
        "seating": "limited",
        "outlets": "few",
        "noise": "Quiet upstairs",
        "quiet": True,
        "ratings": 54,
        "last_test": "1 hr ago",
        "open": True,
        "hours": "open till 9 PM",
    },
    {
        "name": "1515",
        "distance": 0.3,
        "speeds": {
            "now": [64, 18],
            "morning": [71, 20],
            "afternoon": [64, 18],
            "evening": [49, 13],
        },
        "seating": "some",
        "outlets": "plenty",
        "noise": "Noise: medium",
        "quiet": False,
        "ratings": 21,
        "last_test": "3 hrs ago",
        "open": True,
        "hours": "open till 6 PM",
    },
]

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


def speed_label(download):
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

    shops = []
    for original in SHOPS:
        # Copy instead of mutating the shared SHOPS dicts in place -- SHOPS
        # is module-level state shared by every request in the process, so
        # writing into it directly let one request's values leak into
        # another's under concurrent access.
        shop = dict(original)
        shop["download"] = shop["speeds"][time][0]
        shop["upload"] = shop["speeds"][time][1]
        shop["label"] = speed_label(shop["download"])

        if search not in shop["name"].lower():
            continue
        if "fast" in active and shop["label"] != "Fast":
            continue
        if "outlets" in active and shop["outlets"] == "few":
            continue
        if "seating" in active and shop["seating"] == "limited":
            continue
        if "quiet" in active and not shop["quiet"]:
            continue
        if "open" in active and not shop["open"]:
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

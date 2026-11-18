from django.db import migrations

# The shops that used to be hard-coded in views.py, with their speeds
# turned into one starter rating per time of day.
SHOPS = [
    {
        "name": "Bodo's (Corner)",
        "distance": 0.1,
        "seating": "plenty",
        "outlets": "few",
        "noise": "Noise: loud",
        "quiet": False,
        "open": False,
        "hours": "closed · opens 7 AM",
        "speeds": {"morning": [14, 4], "afternoon": [19, 5], "evening": [22, 6]},
    },
    {
        "name": "Grit (Corner)",
        "distance": 0.2,
        "seating": "plenty",
        "outlets": "some",
        "noise": "Quiet upstairs",
        "quiet": True,
        "open": True,
        "hours": "open till 7 PM",
        "speeds": {"morning": [58, 16], "afternoon": [52, 14], "evening": [44, 12]},
    },
    {
        "name": "Starbucks (Corner)",
        "distance": 0.2,
        "seating": "limited",
        "outlets": "few",
        "noise": "Quiet upstairs",
        "quiet": True,
        "open": True,
        "hours": "open till 9 PM",
        "speeds": {"morning": [36, 10], "afternoon": [31, 9], "evening": [27, 8]},
    },
    {
        "name": "1515",
        "distance": 0.3,
        "seating": "some",
        "outlets": "plenty",
        "noise": "Noise: medium",
        "quiet": False,
        "open": True,
        "hours": "open till 6 PM",
        "speeds": {"morning": [71, 20], "afternoon": [64, 18], "evening": [49, 13]},
    },
]


def add_shops(apps, schema_editor):
    Shop = apps.get_model("accounts", "Shop")
    Rating = apps.get_model("accounts", "Rating")
    for data in SHOPS:
        data = dict(data)
        speeds = data.pop("speeds")
        shop = Shop.objects.create(**data)
        for time_of_day, (download, upload) in speeds.items():
            Rating.objects.create(
                shop=shop, download=download, upload=upload, time_of_day=time_of_day
            )


def remove_shops(apps, schema_editor):
    Shop = apps.get_model("accounts", "Shop")
    Shop.objects.filter(name__in=[s["name"] for s in SHOPS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_shop_rating"),
    ]

    operations = [
        migrations.RunPython(add_shops, remove_shops),
    ]

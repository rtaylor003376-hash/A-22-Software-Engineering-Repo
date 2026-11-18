from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("moderator", "Moderator"),
    ]

    # everyone starts as a student and we'll change to moderator in admin
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")


class Shop(models.Model):
    name = models.CharField(max_length=100)
    distance = models.FloatField()
    seating = models.CharField(max_length=20)
    outlets = models.CharField(max_length=20)
    noise = models.CharField(max_length=50)
    quiet = models.BooleanField(default=False)
    open = models.BooleanField(default=True)
    hours = models.CharField(max_length=50)

    class Meta:
        ordering = ["distance", "id"]

    def __str__(self):
        return self.name


class Rating(models.Model):
    TIME_OF_DAY_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
        ("evening", "Evening"),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="ratings")
    # starter ratings that came with the app don't belong to anyone
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    download = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10000)])
    upload = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10000)])
    time_of_day = models.CharField(max_length=20, choices=TIME_OF_DAY_CHOICES)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shop} {self.download}/{self.upload} Mbps"

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("moderator", "Moderator"),
    ]

    # everyone starts as a student and we'll change to moderator in admin
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")

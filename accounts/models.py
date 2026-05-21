from django.conf import settings
from django.db import models


class Profile(models.Model):
    LEARNER = "learner"
    TEACHER = "teacher"
    BOTH = "both"

    ROLE_CHOICES = [
        (LEARNER, "Learner"),
        (TEACHER, "Teacher"),
        (BOTH, "Both"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120, blank=True)
    headline = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    availability = models.CharField(max_length=160, blank=True)
    learning_goal = models.TextField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=BOTH)
    is_onboarding_completed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        display_name = self.full_name or self.user.get_username()
        return f"{display_name}'s profile"

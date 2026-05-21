from django.conf import settings
from django.db import models


class Skill(models.Model):
    TEACH = "teach"
    LEARN = "learn"
    SKILL_TYPE_CHOICES = [
        (TEACH, "Teach"),
        (LEARN, "Learn"),
    ]

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    LEVEL_CHOICES = [
        (BEGINNER, "Beginner"),
        (INTERMEDIATE, "Intermediate"),
        (ADVANCED, "Advanced"),
    ]

    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"
    MODE_CHOICES = [
        (ONLINE, "Online"),
        (OFFLINE, "Offline"),
        (HYBRID, "Hybrid"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="skills",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    skill_type = models.CharField(max_length=20, choices=SKILL_TYPE_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=ONLINE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

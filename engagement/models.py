import uuid

from django.conf import settings
from django.db import models


class Achievement(models.Model):
    FIRST_SKILL = "first_skill_added"
    FIRST_EXCHANGE = "first_exchange_accepted"
    FIRST_SESSION = "first_session_completed"
    HELPFUL_MENTOR = "helpful_mentor"
    ACTIVE_LEARNER = "active_learner"
    SKILL_SHARER = "skill_sharer"
    TOP_RATED = "top_rated"
    COMMUNITY_STAR = "community_star"

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField()
    points = models.PositiveIntegerField(default=30)
    target_value = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    icon_label = models.CharField(max_length=4, default="AC")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="achievements", on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, related_name="unlocks", on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    progress_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    target_value = models.DecimalField(max_digits=8, decimal_places=2, default=1)

    class Meta:
        ordering = ["-unlocked_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "achievement"], name="unique_user_achievement")
        ]

    def __str__(self):
        return f"{self.user} unlocked {self.achievement}"


class Certificate(models.Model):
    LEARNER = "learner_completion"
    MENTOR = "mentor_contribution"

    CERTIFICATE_TYPE_CHOICES = [
        (LEARNER, "Learner Completion"),
        (MENTOR, "Mentor Recognition"),
    ]

    certificate_id = models.CharField(max_length=40, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="certificates", on_delete=models.CASCADE)
    skill = models.ForeignKey("skills.Skill", null=True, blank=True, on_delete=models.SET_NULL)
    exchange = models.ForeignKey("matching.SkillExchange", null=True, blank=True, on_delete=models.SET_NULL)
    session = models.ForeignKey("skill_sessions.Session", null=True, blank=True, on_delete=models.SET_NULL)
    certificate_type = models.CharField(
        max_length=30,
        choices=CERTIFICATE_TYPE_CHOICES,
        default=LEARNER,
    )
    title = models.CharField(max_length=180)
    mentor_name = models.CharField(max_length=120, blank=True)
    learner_name = models.CharField(max_length=120, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    hours_completed = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    sessions_count = models.PositiveIntegerField(default=0)
    verification_code = models.CharField(max_length=40, unique=True, editable=False)
    issued_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "exchange"],
                condition=models.Q(
                    certificate_type__in=["learner_completion", "mentor_contribution"],
                    exchange__isnull=False,
                ),
                name="unique_role_certificate_per_user_exchange",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = f"SS-{uuid.uuid4().hex[:10].upper()}"
        if not self.verification_code:
            self.verification_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.user}"

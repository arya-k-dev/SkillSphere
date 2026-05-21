from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Session(models.Model):
    VIDEO_CALL = "video_call"
    CHAT = "chat"
    IN_PERSON = "in_person"

    FORMAT_CHOICES = [
        (VIDEO_CALL, "Video call"),
        (CHAT, "Chat"),
        (IN_PERSON, "In person"),
    ]

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (SCHEDULED, "Scheduled"),
        (IN_PROGRESS, "In progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

    exchange = models.ForeignKey(
        "matching.SkillExchange",
        related_name="sessions",
        on_delete=models.CASCADE,
    )
    request = models.ForeignKey(
        "matching.MatchRequest",
        related_name="sessions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="mentor_sessions",
        on_delete=models.CASCADE,
    )
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="learner_sessions",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=VIDEO_CALL)
    location = models.CharField(max_length=255, blank=True)
    meeting_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SCHEDULED)
    notes = models.TextField(blank=True)
    topics_covered = models.TextField(blank=True)
    shared_resources = models.TextField(blank=True)
    assignments = models.TextField(blank=True)
    mentor_attendance = models.BooleanField(default=False)
    learner_attendance = models.BooleanField(default=False)
    hours_taught = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    hours_learned = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    reminder_1hr_sent = models.BooleanField(default=False)
    reminder_15min_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_date", "scheduled_time"]

    def __str__(self):
        return f"{self.title} on {self.scheduled_date}"

    @property
    def starts_at(self):
        naive = timezone.datetime.combine(self.scheduled_date, self.scheduled_time)
        if timezone.is_naive(naive):
            return timezone.make_aware(naive, timezone.get_current_timezone())
        return naive

    def clean(self):
        if self.mentor_id and self.learner_id and self.mentor_id == self.learner_id:
            raise ValidationError("Mentor and learner must be different users.")
        if self.duration_minutes <= 0:
            raise ValidationError("Duration must be positive.")
        if self.hours_taught < 0 or self.hours_learned < 0:
            raise ValidationError("Session hours cannot be negative.")
        if self.scheduled_date and self.scheduled_time and self.status == self.SCHEDULED:
            if self.starts_at < timezone.now():
                raise ValidationError("Scheduled date and time cannot be in the past.")
        if self.exchange_id and self.mentor_id and self.learner_id:
            participant_ids = {self.exchange.requester_id, self.exchange.responder_id}
            if self.mentor_id not in participant_ids or self.learner_id not in participant_ids:
                raise ValidationError("Only users in the exchange can be assigned to this session.")

    def user_is_participant(self, user):
        return user.is_authenticated and user.pk in {self.mentor_id, self.learner_id}

    def partner_for(self, user):
        if user == self.mentor:
            return self.learner
        if user == self.learner:
            return self.mentor
        return None


class SessionFeedback(models.Model):
    session = models.ForeignKey(Session, related_name="feedback", on_delete=models.CASCADE)
    given_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="session_feedback",
        on_delete=models.CASCADE,
    )
    rating = models.PositiveSmallIntegerField()
    comments = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["session", "given_by"], name="unique_feedback_per_user_per_session")
        ]

    def __str__(self):
        return f"{self.rating}/5 for {self.session}"

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Rating must be between 1 and 5.")
        if self.session_id and self.given_by_id and not self.session.user_is_participant(self.given_by):
            raise ValidationError("Only session participants can submit feedback.")

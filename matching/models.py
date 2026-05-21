from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.db.models import Q

from skills.models import Skill


class MatchRequest(models.Model):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (DECLINED, "Declined"),
        (CANCELLED, "Cancelled"),
    ]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_match_requests",
        on_delete=models.CASCADE,
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="received_match_requests",
        on_delete=models.CASCADE,
    )
    offered_skill = models.ForeignKey(
        Skill,
        related_name="exchange_requests_offered",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Skill the sender can teach in exchange.",
    )
    requested_skill = models.ForeignKey(
        Skill,
        related_name="exchange_requests_requested",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Skill the sender wants to learn from the receiver.",
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver", "offered_skill", "requested_skill"],
                condition=Q(status="pending"),
                name="unique_pending_exchange_request",
            ),
            models.UniqueConstraint(
                fields=["sender", "receiver", "offered_skill", "requested_skill"],
                condition=Q(status__in=["pending", "accepted"]),
                name="unique_active_exchange_request",
            )
        ]

    def __str__(self):
        return f"{self.sender} to {self.receiver} ({self.get_status_display()})"

    def clean(self):
        if self.sender_id and self.receiver_id and self.sender_id == self.receiver_id:
            raise ValidationError("You cannot send a match request to yourself.")

        if not self.sender_id or not self.receiver_id:
            return

        duplicate_active = MatchRequest.objects.filter(
            sender=self.sender,
            receiver=self.receiver,
            offered_skill=self.offered_skill,
            requested_skill=self.requested_skill,
            status__in=[self.PENDING, self.ACCEPTED],
        )
        if self.pk:
            duplicate_active = duplicate_active.exclude(pk=self.pk)

        if self.status in [self.PENDING, self.ACCEPTED] and duplicate_active.exists():
            raise ValidationError("An active request already exists for this match.")

    def accept(self, user):
        if user != self.receiver:
            raise PermissionDenied("Only the receiver can accept this request.")
        if MatchRequest.objects.filter(
            sender=self.sender,
            receiver=self.receiver,
            offered_skill=self.offered_skill,
            requested_skill=self.requested_skill,
            status=self.ACCEPTED,
        ).exclude(pk=self.pk).exists():
            raise ValidationError("Exchange already accepted.")
        self.status = self.ACCEPTED
        self.save(update_fields=["status", "updated_at"])
        exchange, _ = SkillExchange.objects.get_or_create(
            requester=self.sender,
            responder=self.receiver,
            offered_skill=self.offered_skill,
            requested_skill=self.requested_skill,
            defaults={"request": self},
        )
        if exchange.request_id != self.pk:
            exchange.request = self
            exchange.save(update_fields=["request"])

        from messaging.services import ensure_exchange_communication

        ensure_exchange_communication(exchange, notify_acceptance=True)

    def decline(self, user):
        if user != self.receiver:
            raise PermissionDenied("Only the receiver can decline this request.")
        self.status = self.DECLINED
        self.save(update_fields=["status", "updated_at"])

    def cancel(self, user):
        if user != self.sender:
            raise PermissionDenied("Only the sender can cancel this request.")
        self.status = self.CANCELLED
        self.save(update_fields=["status", "updated_at"])


class SkillExchange(models.Model):
    request = models.OneToOneField(
        MatchRequest,
        related_name="exchange",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="requested_skill_exchanges",
        on_delete=models.CASCADE,
    )
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="responded_skill_exchanges",
        on_delete=models.CASCADE,
    )
    offered_skill = models.ForeignKey(
        Skill,
        related_name="active_exchanges_offered",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    requested_skill = models.ForeignKey(
        Skill,
        related_name="active_exchanges_requested",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["requester", "responder", "offered_skill", "requested_skill"],
                name="unique_active_skill_exchange",
            )
        ]

    def __str__(self):
        return f"{self.requester} and {self.responder}"

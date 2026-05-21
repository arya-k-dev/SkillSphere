from django.conf import settings
from django.db import models
from django.urls import reverse


class ChatThread(models.Model):
    exchange = models.OneToOneField(
        "matching.SkillExchange",
        related_name="chat_thread",
        on_delete=models.CASCADE,
    )
    user_one = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="chat_threads_as_user_one",
        on_delete=models.CASCADE,
    )
    user_two = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="chat_threads_as_user_two",
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Chat for exchange #{self.exchange_id}"

    def get_partner(self, user):
        if user == self.user_one:
            return self.user_two
        if user == self.user_two:
            return self.user_one
        return None

    def includes_user(self, user):
        return user.is_authenticated and user.pk in {self.user_one_id, self.user_two_id}

    def get_absolute_url(self):
        return reverse("messaging:exchange_chat", kwargs={"exchange_id": self.exchange_id})

    def unread_count_for(self, user):
        return self.messages.exclude(sender=user).filter(is_read=False).count()


class Message(models.Model):
    thread = models.ForeignKey(ChatThread, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_chat_messages",
        on_delete=models.CASCADE,
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender} in thread #{self.thread_id}"


class Notification(models.Model):
    REQUEST_SENT = "request_sent"
    REQUEST_ACCEPTED = "request_accepted"
    REQUEST_REJECTED = "request_rejected"
    MESSAGE = "message"
    SESSION = "session"
    RATING = "rating"
    BADGE = "badge"
    CERTIFICATE = "certificate"

    NOTIFICATION_TYPES = [
        (REQUEST_SENT, "Request sent"),
        (REQUEST_ACCEPTED, "Request accepted"),
        (REQUEST_REJECTED, "Request rejected"),
        (MESSAGE, "Message"),
        (SESSION, "Session"),
        (RATING, "Rating"),
        (BADGE, "Badge"),
        (CERTIFICATE, "Certificate"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=140)
    message = models.TextField()
    notification_type = models.CharField(max_length=40, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} for {self.user}"

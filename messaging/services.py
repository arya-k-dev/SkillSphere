from django.urls import reverse
import logging

from .models import ChatThread, Notification


logger = logging.getLogger(__name__)


def display_name(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "full_name", "") or user.get_full_name() or user.get_username()


def create_notification(user, title, message, notification_type, related_url=""):
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_url=related_url,
    )
    logger.debug(
        "Created notification id=%s type=%s receiver_user_id=%s",
        notification.pk,
        notification.notification_type,
        notification.user_id,
    )
    return notification


def notify_request_sent(match_request):
    create_notification(
        user=match_request.receiver,
        title="New exchange request",
        message=f"{display_name(match_request.sender)} sent you a skill exchange request.",
        notification_type=Notification.REQUEST_SENT,
        related_url=reverse("matching:requests"),
    )


def notify_request_rejected(match_request):
    create_notification(
        user=match_request.sender,
        title="Request rejected",
        message=f"{display_name(match_request.receiver)} rejected your exchange request.",
        notification_type=Notification.REQUEST_REJECTED,
        related_url=reverse("matching:requests"),
    )


def notify_message_received(message):
    thread = message.thread
    if thread.user_one_id == message.sender_id:
        recipient = thread.user_two
    elif thread.user_two_id == message.sender_id:
        recipient = thread.user_one
    else:
        return None

    return create_notification(
        user=recipient,
        title="New message",
        message=f"{display_name(message.sender)} sent you a new message.",
        notification_type=Notification.MESSAGE,
        related_url=message.thread.get_absolute_url(),
    )


def ensure_exchange_communication(exchange, notify_acceptance=False):
    thread, _ = ChatThread.objects.get_or_create(
        exchange=exchange,
        defaults={
            "user_one": exchange.requester,
            "user_two": exchange.responder,
            "is_active": True,
        },
    )
    if not thread.is_active:
        thread.is_active = True
        thread.save(update_fields=["is_active", "updated_at"])

    if notify_acceptance:
        chat_url = reverse("messaging:exchange_chat", kwargs={"exchange_id": exchange.pk})
        create_notification(
            user=exchange.requester,
            title="Request accepted",
            message=f"{display_name(exchange.responder)} accepted your exchange request. You can now start chatting.",
            notification_type=Notification.REQUEST_ACCEPTED,
            related_url=chat_url,
        )
    return thread

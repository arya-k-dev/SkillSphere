from .models import Notification


def notification_context(request):
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "latest_notifications": [],
        }

    return {
        "unread_notifications_count": Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count(),
        "latest_notifications": Notification.objects.filter(
            user=request.user,
        ).order_by("-created_at")[:5],
    }


def notification_counts(request):
    return notification_context(request)

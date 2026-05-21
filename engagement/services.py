from dataclasses import dataclass
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from matching.models import SkillExchange
from sessions.models import Session, SessionFeedback
from skills.models import Skill

from .models import Achievement, Certificate, UserAchievement


DEFAULT_ACHIEVEMENTS = [
    {
        "code": Achievement.FIRST_SKILL,
        "name": "First Skill Added",
        "description": "Add your first teach or learn skill.",
        "points": 30,
        "target_value": Decimal("1"),
        "icon_label": "FS",
    },
    {
        "code": Achievement.FIRST_EXCHANGE,
        "name": "First Exchange Accepted",
        "description": "Get your first accepted skill exchange.",
        "points": 40,
        "target_value": Decimal("1"),
        "icon_label": "EX",
    },
    {
        "code": Achievement.FIRST_SESSION,
        "name": "First Session Completed",
        "description": "Complete your first learning session.",
        "points": 50,
        "target_value": Decimal("1"),
        "icon_label": "SC",
    },
    {
        "code": Achievement.HELPFUL_MENTOR,
        "name": "Helpful Mentor",
        "description": "Receive a 5-star session rating.",
        "points": 60,
        "target_value": Decimal("1"),
        "icon_label": "HM",
    },
    {
        "code": Achievement.ACTIVE_LEARNER,
        "name": "Active Learner",
        "description": "Complete 3 sessions as a learner.",
        "points": 75,
        "target_value": Decimal("3"),
        "icon_label": "AL",
    },
    {
        "code": Achievement.SKILL_SHARER,
        "name": "Skill Sharer",
        "description": "Teach 5 total hours.",
        "points": 90,
        "target_value": Decimal("5"),
        "icon_label": "SS",
    },
    {
        "code": Achievement.TOP_RATED,
        "name": "Top Rated",
        "description": "Keep a 4.5+ average rating with at least 3 reviews.",
        "points": 100,
        "target_value": Decimal("3"),
        "icon_label": "TR",
    },
    {
        "code": Achievement.COMMUNITY_STAR,
        "name": "Community Star",
        "description": "Complete 5 skill exchanges.",
        "points": 120,
        "target_value": Decimal("5"),
        "icon_label": "CS",
    },
]


@dataclass
class AchievementProgress:
    achievement: Achievement
    unlocked: bool
    progress_value: Decimal
    target_value: Decimal
    progress_percent: int
    unlocked_at: object = None


def display_name(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "full_name", "") or user.get_full_name() or user.username


def ensure_default_achievements():
    for data in DEFAULT_ACHIEVEMENTS:
        Achievement.objects.update_or_create(code=data["code"], defaults=data)


def user_completed_sessions(user):
    return Session.objects.filter(Q(mentor=user) | Q(learner=user), status=Session.COMPLETED)


def received_feedback(user):
    return SessionFeedback.objects.filter(Q(session__mentor=user) | Q(session__learner=user)).exclude(given_by=user)


def completed_exchange_count(user):
    return (
        user_completed_sessions(user)
        .exclude(exchange__isnull=True)
        .values("exchange_id")
        .distinct()
        .count()
    )


def accepted_exchange_count(user):
    return SkillExchange.objects.filter(Q(requester=user) | Q(responder=user)).count()


def achievement_metric(user, code):
    completed_sessions = user_completed_sessions(user)
    feedback = received_feedback(user)
    if code == Achievement.FIRST_SKILL:
        return Decimal(Skill.objects.filter(user=user).count())
    if code == Achievement.FIRST_EXCHANGE:
        return Decimal(accepted_exchange_count(user))
    if code == Achievement.FIRST_SESSION:
        return Decimal(completed_sessions.count())
    if code == Achievement.HELPFUL_MENTOR:
        return Decimal(feedback.filter(rating=5).count())
    if code == Achievement.ACTIVE_LEARNER:
        return Decimal(Session.objects.filter(learner=user, status=Session.COMPLETED).count())
    if code == Achievement.SKILL_SHARER:
        return completed_sessions.filter(mentor=user).aggregate(total=Sum("hours_taught"))["total"] or Decimal("0")
    if code == Achievement.TOP_RATED:
        summary = feedback.aggregate(avg=Avg("rating"), count=Count("id"))
        if summary["count"] >= 3 and (summary["avg"] or 0) >= 4.5:
            return Decimal(summary["count"])
        return Decimal("0")
    if code == Achievement.COMMUNITY_STAR:
        return Decimal(completed_exchange_count(user))
    return Decimal("0")


def achievement_progress_for_user(user):
    ensure_default_achievements()
    unlocks = {
        item.achievement_id: item
        for item in UserAchievement.objects.select_related("achievement").filter(user=user)
    }
    progress_items = []
    for achievement in Achievement.objects.all():
        value = achievement_metric(user, achievement.code)
        target = achievement.target_value or Decimal("1")
        is_unlocked = value >= target
        unlock = unlocks.get(achievement.pk)
        if is_unlocked and not unlock:
            unlock = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                progress_value=value,
                target_value=target,
            )
        elif unlock and (unlock.progress_value != value or unlock.target_value != target):
            unlock.progress_value = value
            unlock.target_value = target
            unlock.save(update_fields=["progress_value", "target_value"])
        percent = int(min(100, (value / target) * 100)) if target else 100
        progress_items.append(
            AchievementProgress(
                achievement=achievement,
                unlocked=is_unlocked or unlock is not None,
                progress_value=value,
                target_value=target,
                progress_percent=percent,
                unlocked_at=unlock.unlocked_at if unlock else None,
            )
        )
    return progress_items


def evaluate_user_achievements(user):
    return achievement_progress_for_user(user)


def session_skill_for_user(session, user):
    exchange = session.exchange
    if not exchange:
        return None
    if user == session.mentor:
        return exchange.offered_skill if session.mentor_id == exchange.requester_id else exchange.requested_skill
    return exchange.requested_skill if session.mentor_id == exchange.requester_id else exchange.offered_skill


def certificate_average_rating(session):
    rating = session.feedback.aggregate(avg=Avg("rating"))["avg"]
    return Decimal(str(round(rating, 2))) if rating is not None else None


def certificate_hours(session, user):
    if user == session.mentor:
        return session.hours_taught or Decimal("0")
    if user == session.learner:
        return session.hours_learned or Decimal("0")
    return Decimal("0")


def ensure_certificates_for_user(user):
    completed_sessions = (
        user_completed_sessions(user)
        .select_related(
            "mentor",
            "mentor__profile",
            "learner",
            "learner__profile",
            "exchange",
            "exchange__offered_skill",
            "exchange__requested_skill",
        )
        .annotate(feedback_total=Count("feedback"))
        .filter(feedback_total__gte=2)
        .exclude(exchange__isnull=True)
        .order_by("completed_at", "updated_at")
    )

    exchange_ids = completed_sessions.values_list("exchange_id", flat=True).distinct()
    for exchange_id in exchange_ids:
        exchange_sessions = list(completed_sessions.filter(exchange_id=exchange_id))
        if not exchange_sessions:
            continue

        mentor_sessions = [session for session in exchange_sessions if session.mentor_id == user.pk]
        learner_sessions = [session for session in exchange_sessions if session.learner_id == user.pk]
        mentor_hours = sum((session.hours_taught or Decimal("0")) for session in mentor_sessions)
        learner_hours = sum((session.hours_learned or Decimal("0")) for session in learner_sessions)

        if learner_sessions and (learner_hours >= mentor_hours or not mentor_sessions):
            role = Certificate.LEARNER
            title = "Certificate of Skill Completion"
            role_session = learner_sessions[0]
            skill = session_skill_for_user(role_session, user)
            hours = learner_hours
            sessions_count = len(learner_sessions)
        elif mentor_sessions:
            role = Certificate.MENTOR
            title = "Certificate of Skill Mentorship"
            role_session = mentor_sessions[0]
            skill = session_skill_for_user(role_session, user)
            hours = mentor_hours
            sessions_count = len(mentor_sessions)
        else:
            continue

        existing_certificate = Certificate.objects.filter(
            user=user,
            exchange=role_session.exchange,
            certificate_type__in=[Certificate.LEARNER, Certificate.MENTOR],
        ).first()
        if not existing_certificate:
            Certificate.objects.create(
                user=user,
                exchange=role_session.exchange,
                certificate_type=role,
                title=title,
                skill=skill,
                session=role_session,
                mentor_name=display_name(role_session.mentor),
                learner_name=display_name(role_session.learner),
                rating=certificate_average_rating(role_session),
                hours_completed=hours,
                sessions_count=sessions_count,
            )

    return Certificate.objects.filter(
        user=user,
        certificate_type__in=[Certificate.LEARNER, Certificate.MENTOR],
    ).select_related("skill", "session", "exchange")


def user_leaderboard_rows(filter_name="overall"):
    ensure_default_achievements()
    User = get_user_model()
    users = User.objects.filter(is_active=True).select_related("profile").prefetch_related("skills", "achievements")
    rows = []
    for user in users:
        evaluate_user_achievements(user)
        sessions = user_completed_sessions(user)
        if filter_name == "mentors":
            sessions = sessions.filter(mentor=user)
        elif filter_name == "learners":
            sessions = sessions.filter(learner=user)
        elif filter_name == "month":
            now = timezone.now()
            sessions = sessions.filter(completed_at__year=now.year, completed_at__month=now.month)

        completed_count = sessions.count()
        hours_taught = user_completed_sessions(user).filter(mentor=user).aggregate(total=Sum("hours_taught"))["total"] or Decimal("0")
        feedback = received_feedback(user)
        average_rating = feedback.aggregate(avg=Avg("rating"))["avg"] or 0
        five_star_reviews = feedback.filter(rating=5).count()
        badges_count = UserAchievement.objects.filter(user=user).count()
        points = int((completed_count * 50) + (hours_taught * 20) + (badges_count * 30) + (five_star_reviews * 25))
        rows.append(
            {
                "user": user,
                "skills_taught": Skill.objects.filter(user=user, skill_type=Skill.TEACH).count(),
                "completed_sessions": completed_count,
                "hours_taught": hours_taught,
                "average_rating": average_rating,
                "badges_count": badges_count,
                "points": points,
            }
        )
    rows.sort(key=lambda row: row["points"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows

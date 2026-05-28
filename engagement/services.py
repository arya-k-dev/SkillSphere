from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from sessions.models import Session, SessionFeedback
from skills.models import Skill

from .models import Certificate


def display_name(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "full_name", "") or user.get_full_name() or user.username


def user_completed_sessions(user):
    return Session.objects.filter(Q(mentor=user) | Q(learner=user), status=Session.COMPLETED)


def received_feedback(user):
    return SessionFeedback.objects.filter(Q(session__mentor=user) | Q(session__learner=user)).exclude(given_by=user)


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
        certificate_defaults = {
            "certificate_type": role,
            "title": title,
            "skill": skill,
            "session": role_session,
            "mentor_name": display_name(role_session.mentor),
            "learner_name": display_name(role_session.learner),
            "rating": certificate_average_rating(role_session),
            "hours_completed": hours,
            "sessions_count": sessions_count,
        }
        if existing_certificate:
            changed_fields = []
            for field, value in certificate_defaults.items():
                if getattr(existing_certificate, field) != value:
                    setattr(existing_certificate, field, value)
                    changed_fields.append(field)
            if changed_fields:
                existing_certificate.save(update_fields=changed_fields)
        else:
            Certificate.objects.create(
                user=user,
                exchange=role_session.exchange,
                **certificate_defaults,
            )

    return Certificate.objects.filter(
        user=user,
        certificate_type__in=[Certificate.LEARNER, Certificate.MENTOR],
    ).select_related("skill", "session", "exchange")


def user_leaderboard_rows(filter_name="overall"):
    User = get_user_model()
    users = User.objects.filter(is_active=True).select_related("profile").prefetch_related("skills")
    rows = []
    for user in users:
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
        points = int((completed_count * 50) + (hours_taught * 20) + (five_star_reviews * 25))
        rows.append(
            {
                "user": user,
                "skills_taught": Skill.objects.filter(user=user, skill_type=Skill.TEACH).count(),
                "completed_sessions": completed_count,
                "hours_taught": hours_taught,
                "average_rating": average_rating,
                "points": points,
            }
        )
    rows.sort(key=lambda row: row["points"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows

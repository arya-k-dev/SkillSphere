from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, render

from matching.models import SkillExchange
from sessions.models import Session, SessionFeedback
from skills.models import Skill

from .models import Achievement, Certificate
from .services import (
    completed_exchange_count,
    ensure_certificates_for_user,
    evaluate_user_achievements,
    user_leaderboard_rows,
)


ACHIEVEMENT_CATEGORY_LABELS = {
    Achievement.HELPFUL_MENTOR: "Teacher Badges",
    Achievement.SKILL_SHARER: "Teacher Badges",
    Achievement.TOP_RATED: "Teacher Badges",
    Achievement.FIRST_SKILL: "Learner Badges",
    Achievement.FIRST_SESSION: "Learner Badges",
    Achievement.ACTIVE_LEARNER: "Learner Badges",
    Achievement.FIRST_EXCHANGE: "Community Badges",
    Achievement.COMMUNITY_STAR: "Community Badges",
}


ACHIEVEMENT_PROGRESS_UNITS = {
    Achievement.FIRST_SKILL: "skills added",
    Achievement.FIRST_EXCHANGE: "exchanges accepted",
    Achievement.FIRST_SESSION: "sessions completed",
    Achievement.HELPFUL_MENTOR: "five-star reviews",
    Achievement.ACTIVE_LEARNER: "sessions completed",
    Achievement.SKILL_SHARER: "hours taught",
    Achievement.TOP_RATED: "reviews received",
    Achievement.COMMUNITY_STAR: "exchanges completed",
}


def compact_metric(value):
    if value is None:
        return "0"
    if value == int(value):
        return str(int(value))
    return str(value).rstrip("0").rstrip(".")


def grouped_achievement_progress(progress_items):
    grouped = {
        "Teacher Badges": [],
        "Learner Badges": [],
        "Community Badges": [],
    }
    for item in progress_items:
        category = ACHIEVEMENT_CATEGORY_LABELS.get(item.achievement.code, "Community Badges")
        unit = ACHIEVEMENT_PROGRESS_UNITS.get(item.achievement.code, "completed")
        item.progress_text = (
            f"{compact_metric(item.progress_value)}/{compact_metric(item.target_value)} {unit}"
        )
        grouped[category].append(item)
    return [{"title": title, "items": items} for title, items in grouped.items() if items]


def achievement_summary_for_user(user, unlocked_count):
    completed_sessions = Session.objects.filter(
        Q(mentor=user) | Q(learner=user),
        status=Session.COMPLETED,
    )
    hours_taught = completed_sessions.filter(mentor=user).aggregate(total=Sum("hours_taught"))["total"] or 0
    hours_learned = completed_sessions.filter(learner=user).aggregate(total=Sum("hours_learned"))["total"] or 0
    average_rating = (
        SessionFeedback.objects.filter(Q(session__mentor=user) | Q(session__learner=user))
        .exclude(given_by=user)
        .aggregate(avg=Avg("rating"))["avg"]
        or 0
    )
    return {
        "certificates_earned": Certificate.objects.filter(
            user=user,
            certificate_type__in=[Certificate.LEARNER, Certificate.MENTOR],
        ).count(),
        "badges_collected": unlocked_count,
        "hours_taught": hours_taught,
        "hours_learned": hours_learned,
        "average_rating": average_rating,
    }


@login_required
def achievements_page(request):
    progress_items = evaluate_user_achievements(request.user)
    unlocked = [item for item in progress_items if item.unlocked]
    locked = [item for item in progress_items if not item.unlocked]
    return render(
        request,
        "engagement/achievements.html",
        {
            "progress_items": progress_items,
            "unlocked": unlocked,
            "locked": locked,
            "badge_sections": grouped_achievement_progress(progress_items),
            "achievement_stats": achievement_summary_for_user(request.user, len(unlocked)),
        },
    )


@login_required
def certificates_page(request):
    certificates = ensure_certificates_for_user(request.user)
    return render(request, "engagement/certificates.html", {"certificates": certificates})


@login_required
def certificate_detail(request, certificate_id):
    ensure_certificates_for_user(request.user)
    certificate = get_object_or_404(
        Certificate.objects.select_related("user", "user__profile", "skill", "session", "exchange"),
        pk=certificate_id,
        user=request.user,
        certificate_type__in=[Certificate.LEARNER, Certificate.MENTOR],
    )
    return render(request, "engagement/certificate_detail.html", {"certificate": certificate})


@login_required
def leaderboard_page(request):
    active_filter = request.GET.get("filter", "overall")
    if active_filter not in ["overall", "mentors", "learners", "month"]:
        active_filter = "overall"
    rows = user_leaderboard_rows(active_filter)
    return render(
        request,
        "engagement/leaderboard.html",
        {
            "rows": rows,
            "active_filter": active_filter,
        },
    )


@login_required
def community_page(request):
    User = get_user_model()
    users = User.objects.filter(is_active=True).select_related("profile")
    featured_learners = (
        users.annotate(learn_count=Count("skills", filter=Q(skills__skill_type=Skill.LEARN)))
        .filter(learn_count__gt=0)
        .order_by("-learn_count", "username")[:6]
    )
    top_mentors = user_leaderboard_rows("mentors")[:5]
    recent_completed_sessions = (
        Session.objects.select_related(
            "mentor",
            "mentor__profile",
            "learner",
            "learner__profile",
            "exchange",
            "exchange__offered_skill",
            "exchange__requested_skill",
        )
        .filter(status=Session.COMPLETED)
        .order_by("-completed_at", "-updated_at")[:5]
    )
    popular_skills = (
        Skill.objects.values("title", "category")
        .annotate(total=Count("id"))
        .order_by("-total", "title")[:8]
    )
    stats = {
        "total_users": users.count(),
        "total_skills": Skill.objects.count(),
        "completed_sessions": Session.objects.filter(status=Session.COMPLETED).count(),
        "completed_exchanges": Session.objects.filter(status=Session.COMPLETED)
        .exclude(exchange__isnull=True)
        .values("exchange_id")
        .distinct()
        .count(),
        "average_rating": SessionFeedback.objects.aggregate(avg=Avg("rating"))["avg"] or 0,
    }
    return render(
        request,
        "engagement/community.html",
        {
            "featured_learners": featured_learners,
            "top_mentors": top_mentors,
            "recent_completed_sessions": recent_completed_sessions,
            "popular_skills": popular_skills,
            "stats": stats,
        },
    )

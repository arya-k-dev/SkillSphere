from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render

from sessions.models import Session, SessionFeedback
from skills.models import Skill

from .models import Certificate
from .services import (
    display_name,
    ensure_certificates_for_user,
    user_leaderboard_rows,
)


@login_required
def certificates_page(request):
    certificates = ensure_certificates_for_user(request.user)
    return render(request, "engagement/certificates.html", {"certificates": certificates})


def certificate_display_context(certificate):
    mentor_name = certificate.mentor_name
    learner_name = certificate.learner_name
    if certificate.session_id:
        mentor_name = mentor_name or display_name(certificate.session.mentor)
        learner_name = learner_name or display_name(certificate.session.learner)

    fallback_name = display_name(certificate.user)
    skill_name = certificate.skill.title if certificate.skill_id else "this skill"

    if certificate.certificate_type == Certificate.MENTOR:
        mentor_name = mentor_name or fallback_name
        learner_name = learner_name or "the learner"
        issued_to_name = mentor_name
        certificate_text = (
            f"This certificate proudly recognizes {mentor_name} for successfully mentoring "
            f"{learner_name} in {skill_name} through SkillSphere."
        )
    else:
        learner_name = learner_name or fallback_name
        mentor_name = mentor_name or "the mentor"
        issued_to_name = learner_name
        certificate_text = (
            f"This certificate proudly recognizes {learner_name} for successfully completing "
            f"{skill_name} through a SkillSphere skill exchange under the guidance of {mentor_name}."
        )

    return {
        "issued_to_name": issued_to_name,
        "mentor_name": mentor_name,
        "learner_name": learner_name,
        "skill_name": skill_name,
        "certificate_text": certificate_text,
    }


@login_required
def certificate_detail(request, certificate_id):
    ensure_certificates_for_user(request.user)
    certificate = get_object_or_404(
        Certificate.objects.select_related(
            "user",
            "user__profile",
            "skill",
            "session",
            "session__mentor",
            "session__mentor__profile",
            "session__learner",
            "session__learner__profile",
            "exchange",
        ),
        pk=certificate_id,
        user=request.user,
        certificate_type__in=[Certificate.LEARNER, Certificate.MENTOR],
    )
    return render(
        request,
        "engagement/certificate_detail.html",
        {
            "certificate": certificate,
            "certificate_display": certificate_display_context(certificate),
        },
    )


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

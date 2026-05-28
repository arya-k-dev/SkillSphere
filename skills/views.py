from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from matching.utils import get_recommended_matches
from core.public_skills import PUBLIC_SKILLS, PUBLIC_SKILLS_BY_SLUG

from .forms import SkillForm
from .models import Skill


def skill_list(request):
    return redirect("skills:browse")


def public_skill_browse(request):
    return render(request, "skills/public_browse.html", {"public_skills": PUBLIC_SKILLS})


@login_required
def public_skill_detail(request, slug):
    public_skill = PUBLIC_SKILLS_BY_SLUG.get(slug)
    if not public_skill:
        return redirect("skills:browse")

    if request.method == "POST":
        Skill.objects.get_or_create(
            user=request.user,
            title=public_skill["name"],
            skill_type=Skill.LEARN,
            defaults={
                "category": public_skill["category"],
                "description": public_skill["description"],
                "level": Skill.BEGINNER,
                "mode": Skill.ONLINE,
            },
        )
        messages.success(request, f"{public_skill['name']} was added to your learning skills.")
        return redirect("skills:public_detail", slug=slug)

    people_offering = (
        Skill.objects.select_related("user", "user__profile")
        .filter(title__iexact=public_skill["name"], skill_type=Skill.TEACH)
        .exclude(user=request.user)[:8]
    )
    people_wanting = (
        Skill.objects.select_related("user", "user__profile")
        .filter(title__iexact=public_skill["name"], skill_type=Skill.LEARN)
        .exclude(user=request.user)[:8]
    )
    recommended_matches = [
        match
        for match in get_recommended_matches(request.user)
        if any(skill.title.lower() == public_skill["name"].lower() for skill in match.get("teach_skills", []))
        or any(skill.title.lower() == public_skill["name"].lower() for skill in match.get("learn_skills", []))
    ][:4]

    return render(
        request,
        "skills/public_detail.html",
        {
            "public_skill": public_skill,
            "people_offering": people_offering,
            "people_wanting": people_wanting,
            "recommended_matches": recommended_matches,
        },
    )


@login_required
def my_skills(request):
    skills = Skill.objects.filter(user=request.user)
    top_matches = get_recommended_matches(request.user)[:5]
    return render(
        request,
        "skills/my_skills.html",
        {"skills": skills, "top_matches": top_matches},
    )


@login_required
def skill_detail(request, pk):
    skill = get_object_or_404(Skill.objects.select_related("user"), pk=pk)
    return render(request, "skills/skill_detail.html", {"skill": skill})


@login_required
def skill_add(request):
    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user
            skill.save()
            messages.success(request, "Your skill has been added.")
            return redirect("skills:my_skills")
    else:
        form = SkillForm()

    return render(request, "skills/skill_form.html", {"form": form, "title": "Add a Skill"})


@login_required
def skill_edit(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if skill.user != request.user:
        raise PermissionDenied

    if request.method == "POST":
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, "Your skill has been updated.")
            return redirect("skills:my_skills")
    else:
        form = SkillForm(instance=skill)

    return render(request, "skills/skill_form.html", {"form": form, "title": "Edit Skill"})


@login_required
def skill_delete(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    if skill.user != request.user:
        raise PermissionDenied

    if request.method == "POST":
        skill.delete()
        messages.success(request, "Your skill has been deleted.")
        return redirect("skills:my_skills")

    return render(request, "skills/skill_confirm_delete.html", {"skill": skill})

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from matching.models import MatchRequest, SkillExchange
from sessions.models import Session, SessionFeedback
from skills.models import Skill


class Command(BaseCommand):
    help = "Create demo users, skills, accepted exchanges, sessions, and ratings for presentation."

    def handle(self, *args, **options):
        User = get_user_model()
        skill_titles = [
            ("Python", "Technology"),
            ("Web Development", "Technology"),
            ("UI/UX Design", "Creative"),
            ("Graphic Design", "Creative"),
            ("Photography", "Creative"),
            ("Spoken English", "Language"),
            ("Fitness", "Lifestyle"),
            ("Cooking", "Lifestyle"),
            ("Music", "Creative"),
            ("Resume Building", "Career"),
        ]

        users = []
        for index in range(10):
            username = f"demo_user_{index + 1}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": f"Demo{index + 1}",
                    "last_name": "Learner",
                    "email": f"{username}@skillsphere.local",
                    "is_active": True,
                },
            )
            if created:
                user.set_password("demo12345")
                user.save(update_fields=["password"])
            else:
                user.is_active = True
                user.save(update_fields=["is_active"])

            profile = user.profile
            profile.full_name = f"Demo Learner {index + 1}"
            profile.headline = "SkillSphere demo member"
            profile.is_onboarding_completed = True
            profile.save(update_fields=["full_name", "headline", "is_onboarding_completed", "updated_at"])
            users.append(user)

        skills = []
        for index, user in enumerate(users):
            teach_title, teach_category = skill_titles[index % len(skill_titles)]
            learn_title, learn_category = skill_titles[(index + 3) % len(skill_titles)]
            teach_skill, _ = Skill.objects.get_or_create(
                user=user,
                title=teach_title,
                skill_type=Skill.TEACH,
                defaults={
                    "category": teach_category,
                    "description": f"Demo teaching profile for {teach_title}.",
                    "level": Skill.INTERMEDIATE,
                    "mode": Skill.ONLINE,
                },
            )
            learn_skill, _ = Skill.objects.get_or_create(
                user=user,
                title=learn_title,
                skill_type=Skill.LEARN,
                defaults={
                    "category": learn_category,
                    "description": f"Demo learning goal for {learn_title}.",
                    "level": Skill.BEGINNER,
                    "mode": Skill.ONLINE,
                },
            )
            skills.append((teach_skill, learn_skill))

        completed_sessions = 0
        scheduled_sessions = 0
        for index in range(5):
            requester = users[index]
            responder = users[index + 5]
            offered_skill = skills[index][0]
            requested_skill = skills[index + 5][0]
            match_request = MatchRequest.objects.filter(
                sender=requester,
                receiver=responder,
                offered_skill=offered_skill,
                requested_skill=requested_skill,
                status=MatchRequest.ACCEPTED,
            ).first()
            if not match_request:
                match_request = MatchRequest.objects.create(
                    sender=requester,
                    receiver=responder,
                    offered_skill=offered_skill,
                    requested_skill=requested_skill,
                    status=MatchRequest.ACCEPTED,
                    score=80 + index,
                    message="Demo accepted exchange.",
                )
            exchange, _ = SkillExchange.objects.get_or_create(
                requester=requester,
                responder=responder,
                offered_skill=offered_skill,
                requested_skill=requested_skill,
                defaults={"request": match_request},
            )
            if exchange.request_id != match_request.pk:
                exchange.request = match_request
                exchange.save(update_fields=["request"])

            base_date = timezone.localdate()
            session, _ = Session.objects.get_or_create(
                exchange=exchange,
                title=f"{offered_skill.title} demo session",
                scheduled_date=base_date - timedelta(days=index + 1),
                scheduled_time=timezone.datetime.strptime("10:00", "%H:%M").time(),
                defaults={
                    "request": match_request,
                    "mentor": requester,
                    "learner": responder,
                    "description": "Demo completed learning session.",
                    "duration_minutes": 60,
                    "format": Session.VIDEO_CALL,
                    "meeting_link": "https://meet.google.com/demo-session",
                    "status": Session.COMPLETED,
                    "completed_at": timezone.now() - timedelta(days=index + 1),
                    "mentor_attendance": True,
                    "learner_attendance": True,
                    "topics_covered": offered_skill.title,
                    "notes": "Demo session completed successfully.",
                    "shared_resources": "Slides and practice exercises.",
                    "assignments": "Complete a small practice task.",
                    "hours_taught": Decimal("1.00"),
                    "hours_learned": Decimal("1.00"),
                },
            )
            if session.status == Session.COMPLETED:
                completed_sessions += 1
                for user, rating in [(requester, 5), (responder, 4 + (index % 2))]:
                    SessionFeedback.objects.get_or_create(
                        session=session,
                        given_by=user,
                        defaults={
                            "rating": rating,
                            "comments": "Demo feedback for presentation.",
                            "tags": "helpful,clear",
                        },
                    )

            upcoming, created = Session.objects.get_or_create(
                exchange=exchange,
                title=f"Upcoming {requested_skill.title} session",
                scheduled_date=base_date + timedelta(days=index + 1),
                scheduled_time=timezone.datetime.strptime("15:30", "%H:%M").time(),
                defaults={
                    "request": match_request,
                    "mentor": responder,
                    "learner": requester,
                    "description": "Demo upcoming learning session.",
                    "duration_minutes": 45,
                    "format": Session.CHAT,
                    "status": Session.SCHEDULED,
                },
            )
            if created or upcoming.status == Session.SCHEDULED:
                scheduled_sessions += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data ready: 10 users, 20 skills, 5 accepted exchanges, "
                f"{completed_sessions} completed sessions, {scheduled_sessions} upcoming sessions."
            )
        )

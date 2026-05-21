# Generated manually for SkillSphere sessions.

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("matching", "0002_skillexchange_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Session",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("scheduled_date", models.DateField()),
                ("scheduled_time", models.TimeField()),
                ("duration_minutes", models.PositiveIntegerField(default=60)),
                (
                    "format",
                    models.CharField(
                        choices=[("video_call", "Video call"), ("chat", "Chat"), ("in_person", "In person")],
                        default="video_call",
                        max_length=20,
                    ),
                ),
                ("location", models.CharField(blank=True, max_length=255)),
                ("meeting_link", models.URLField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("scheduled", "Scheduled"),
                            ("in_progress", "In progress"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="scheduled",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("topics_covered", models.TextField(blank=True)),
                ("shared_resources", models.TextField(blank=True)),
                ("assignments", models.TextField(blank=True)),
                ("mentor_attendance", models.BooleanField(default=False)),
                ("learner_attendance", models.BooleanField(default=False)),
                ("hours_taught", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("hours_learned", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("reminder_1hr_sent", models.BooleanField(default=False)),
                ("reminder_15min_sent", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "exchange",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="matching.skillexchange",
                    ),
                ),
                (
                    "learner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learner_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "mentor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mentor_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sessions",
                        to="matching.matchrequest",
                    ),
                ),
            ],
            options={
                "ordering": ["scheduled_date", "scheduled_time"],
            },
        ),
        migrations.CreateModel(
            name="SessionFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField()),
                ("comments", models.TextField(blank=True)),
                ("tags", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "given_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="session_feedback",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feedback",
                        to="skill_sessions.session",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="sessionfeedback",
            constraint=models.UniqueConstraint(fields=("session", "given_by"), name="unique_feedback_per_user_per_session"),
        ),
    ]

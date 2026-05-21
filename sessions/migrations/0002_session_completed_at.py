# Generated manually for SkillSphere session completion workflow.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill_sessions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

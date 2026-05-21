# Generated manually for SkillSphere notification types.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("request_sent", "Request sent"),
                    ("request_accepted", "Request accepted"),
                    ("request_rejected", "Request rejected"),
                    ("message", "Message"),
                    ("session", "Session"),
                    ("rating", "Rating"),
                    ("badge", "Badge"),
                    ("certificate", "Certificate"),
                ],
                max_length=40,
            ),
        ),
    ]

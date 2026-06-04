from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("service", "0009_jobshistory_notes_jobshistory_proofurl"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobshistory",
            name="auditReviewedDate",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobshistory",
            name="auditStatus",
            field=models.CharField(
                choices=[
                    ("not_checked", "Not Checked"),
                    ("passed", "Passed"),
                    ("failed", "Failed"),
                ],
                default="not_checked",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="jobshistory",
            name="proofReviewedDate",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobshistory",
            name="proofStatus",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("valid", "Valid"),
                    ("invalid", "Invalid"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Grant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("deadline", models.DateField(blank=True, null=True)),
                ("is_open", models.BooleanField(default=True)),
            ],
            options={"ordering": ["deadline", "name"]},
        ),
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("applicant_name", models.CharField(max_length=200)),
                ("applicant_email", models.EmailField(max_length=254)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("submitted", "Submitted"), ("review", "Under review"), ("approved", "Approved"), ("rejected", "Rejected")], default="draft", max_length=20)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("grant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="grants.grant")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

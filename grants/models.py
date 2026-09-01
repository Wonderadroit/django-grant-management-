from django.db import models


class Grant(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateField(null=True, blank=True)
    is_open = models.BooleanField(default=True)

    class Meta:
        ordering = ["deadline", "name"]

    def __str__(self):
        return self.name


class Application(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        REVIEW = "review", "Under review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    grant = models.ForeignKey(Grant, on_delete=models.CASCADE, related_name="applications")
    applicant_name = models.CharField(max_length=200)
    applicant_email = models.EmailField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.applicant_name} — {self.grant.name}"

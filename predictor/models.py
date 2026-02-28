from django.db import models

class DonationRecord(models.Model):
    age = models.IntegerField()
    weight = models.IntegerField()
    hemoglobin = models.FloatField()
    last_donation_days = models.IntegerField()
    is_eligible = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Age {self.age} | Eligible: {self.is_eligible}"

from django.db import models

class DonorHistory(models.Model):
    city = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=5)

    donation_count = models.IntegerField()
    total_blood_donated = models.FloatField()

    months_since_first_donation = models.IntegerField()
    recency_months = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donations: {self.donation_count}, Recency: {self.recency_months} months"
    #------------SMART MATCHING LOGS--------#

class SmartMatchingLog(models.Model):
    donor_history = models.ForeignKey(
        DonorHistory,
        on_delete=models.CASCADE,
        related_name="matching_logs"
    )

    ml_probability = models.FloatField()
    engagement_score = models.FloatField()
    match_score = models.FloatField()

    priority = models.CharField(max_length=10)

    city = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=5)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.priority} | {self.match_score}"
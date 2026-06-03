from django.db import models

# Create your models here.


class FraudAnalysisResult(models.Model):

    RISK_CHOICES = [
        ("LOW",      "Low"),
        ("MEDIUM",   "Medium"),
        ("HIGH",     "High"),
        ("CRITICAL", "Critical"),
    ]

    PREDICTION_CHOICES = [
        ("FRAUD",      "Fraud"),
        ("LEGITIMATE", "Legitimate"),
    ]

    # ── Core references ───────────────────────────────────────────
    job     = models.OneToOneField(
        "service.JobsHistory",
        on_delete=models.CASCADE,
        related_name="fraud_analysis",
        null=True, blank=True
    )
    task    = models.ForeignKey(
        "service.BuyerTasks",
        on_delete=models.CASCADE,
        related_name="fraud_analyses"
    )
    seller  = models.ForeignKey(
        "service.SellerProfile",
        on_delete=models.CASCADE,
        related_name="fraud_analyses"
    )

    # ── Layer 1 ───────────────────────────────────────────────────
    is_duplicate_screenshot = models.BooleanField(default=False)

    # ── Layer 2 — Timing ──────────────────────────────────────────
    completion_duration     = models.FloatField(default=0)
    timing_risk_score       = models.IntegerField(default=0)
    timing_classification   = models.CharField(max_length=50, blank=True)

    # ── Layer 2 — Behavior ────────────────────────────────────────
    std_dev                  = models.FloatField(default=0)
    z_score                  = models.FloatField(default=0)
    population_score         = models.IntegerField(default=0)
    timing_consistency_score = models.IntegerField(default=0)
    validity_score           = models.IntegerField(default=0)
    logical_behavior_flag    = models.BooleanField(default=False)
    repetitive_behavior_flag = models.BooleanField(default=False)
    overall_behavior_label   = models.CharField(max_length=50, blank=True)

    # ── Layer 2 — Device/IP ───────────────────────────────────────
    ip_address           = models.GenericIPAddressField(null=True, blank=True)
    device_id            = models.CharField(max_length=255, blank=True)
    device_seller_count  = models.IntegerField(default=1)
    ip_seller_count      = models.IntegerField(default=1)
    device_sharing_score = models.FloatField(default=0)
    ip_reuse_score       = models.FloatField(default=0)
    device_sharing_label = models.CharField(max_length=50, blank=True)
    ip_reuse_label       = models.CharField(max_length=50, blank=True)

    # ── Layer 3 — ML Result ───────────────────────────────────────
    prediction        = models.CharField(max_length=20, choices=PREDICTION_CHOICES, default="LEGITIMATE")
    fraud_probability = models.FloatField(default=0)
    risk_level        = models.CharField(max_length=20, choices=RISK_CHOICES, default="LOW")
    is_fraud          = models.BooleanField(default=False)

    # ── SHAP Signals (stored as JSON) ─────────────────────────────
    fraud_reasons      = models.JSONField(default=list)   # top signals when fraud
    suspicious_signals = models.JSONField(default=list)   # all signals regardless

    # ── Seller snapshot at time of analysis ───────────────────────
    seller_type        = models.CharField(max_length=20, blank=True)
    seller_age_days    = models.IntegerField(default=0)
    seller_trust_score = models.FloatField(default=0)

    # ── Meta ──────────────────────────────────────────────────────
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-analyzed_at"]
        indexes  = [
            models.Index(fields=["seller", "is_fraud"]),
            models.Index(fields=["task", "analyzed_at"]),
            models.Index(fields=["risk_level"]),
        ]

    def __str__(self):
        return f"Fraud Analysis — Seller {self.seller_id} | Task {self.task_id} | {self.prediction} {self.fraud_probability}%"
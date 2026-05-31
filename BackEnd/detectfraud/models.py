from django.db import models

# Create your models here.


class submittedTask(models.Model):
    taskId = models.CharField(max_length=100)
    taskType = models.CharField(max_length=50, default="unknown")
    completionTime = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    timingClassification = models.CharField(max_length=20, default="unknown")
    supecious_timing_flag = models.BooleanField(default=False)
    timing_risk_score = models.DecimalField(max_digits=10, decimal_places=2, default=0)
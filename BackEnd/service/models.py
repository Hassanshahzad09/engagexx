from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    totalSpend = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    totalEarnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ratings = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])


class BuyerTasks(models.Model):
    buyer = models.ForeignKey(BuyerProfile, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=100, default="New Task")
    platform = models.CharField(max_length=50)
    taskType = models.CharField(max_length=50)
    url = models.URLField()
    progressed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    goal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pricePerAction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="pending")
    approval_status = models.CharField(max_length=20, default="pending")
    startDate = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    endDate = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_tasks",
    )
    rejection_reason = models.TextField(blank=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.platform}"

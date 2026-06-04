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

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('escrow_in', 'Escrow In'),
        ('escrow_release', 'Escrow Release'),
        ('refund', 'Refund'),
        ('penalty', 'Penalty'),
        ('withdraw', 'Withdraw'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount}"


class EasypaisaTransaction(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    )

    buyer = models.ForeignKey("BuyerProfile", on_delete=models.CASCADE, related_name="easypaisa_transactions")
    order_id = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    ep_txn_id = models.CharField(max_length=100, blank=True)
    response_code = models.CharField(max_length=10, blank=True)
    response_desc = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_id} - {self.status} - {self.amount}"


class SellerWithdrawalRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("rejected", "Rejected"),
    )

    seller = models.ForeignKey("SellerProfile", on_delete=models.CASCADE, related_name="withdrawal_requests")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    easypaisa_number = models.CharField(max_length=15)
    account_title = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reference = models.CharField(max_length=60, unique=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.seller.user.username} - {self.amount} - {self.status}"


class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    totalSpend = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class SellerProfile(models.Model):
    unethical_reports = models.IntegerField(default=0)
    trust_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    totalEarnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ratings = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    avgCompletionTime = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sucessRate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

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


class VirtualWallet(models.Model):
    STATUS_CHOICES = (
        ('holding', 'Holding'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
    )

    task = models.OneToOneField(BuyerTasks, on_delete=models.CASCADE, related_name="virtual_wallet")
    buyer = models.ForeignKey(BuyerProfile, on_delete=models.CASCADE, related_name="escrow_payments")
    seller = models.ForeignKey(SellerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="escrow_earnings")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='holding')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task {self.task.id} - {self.amount} - {self.status}"


class JobsHistory(models.Model):
    PROOF_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("valid", "Valid"),
        ("invalid", "Invalid"),
    )
    AUDIT_STATUS_CHOICES = (
        ("not_checked", "Not Checked"),
        ("passed", "Passed"),
        ("failed", "Failed"),
    )
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name="jobs")
    fraud_id = models.IntegerField(default=0)
    task = models.ForeignKey(BuyerTasks, on_delete=models.CASCADE, related_name="jobs")
    progress = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    priceEarned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="pending")
    startDate = models.DateTimeField(auto_now_add=True)
    endDate = models.DateTimeField(null=True, blank=True)
    completionTime = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proofUrl = models.URLField(blank=True)
    proofStatus = models.CharField(max_length=20, choices=PROOF_STATUS_CHOICES, default="pending")
    proofReviewedDate = models.DateTimeField(null=True, blank=True)
    auditStatus = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES, default="not_checked")
    auditReviewedDate = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    taskId = models.IntegerField(default=0)
    proofImage = models.ImageField(
    upload_to="proof_screenshots/",
    blank=True,
    null=True
)

    proofSha256 = models.CharField(
    max_length=64,
    blank=True,
    db_index=True
)
    proofPhash = models.CharField(
    max_length=64,
    blank=True,
    db_index=True
)

    class Meta:
        pass


class SellerBehaviorLog(models.Model):
    job = models.ForeignKey(JobsHistory, on_delete=models.CASCADE, related_name="behavior_logs", null=True, blank=True)
    task_id = models.CharField(max_length=100)
    seller_id = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_id = models.CharField(max_length=255, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Seller {self.seller_id} - Task {self.task_id} - {self.created_at}"

# current indexes of each rating seller

class RatingIndexes(models.Model):
    rate1 = models.IntegerField(default=-1)
    rate2 = models.IntegerField(default=-1)
    rate3 = models.IntegerField(default=-1)
    rate4 = models.IntegerField(default=-1)
    rate5 = models.IntegerField(default=-1)





class SocialAccount(models.Model):
   # user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20)
    username = models.CharField(max_length=255)
    social_id = models.CharField(max_length=255)
    access_token = models.TextField()
    sellerId = models.IntegerField(default=0)


class SocialAuth(models.Model):
    PROVIDER_CHOICES = (
        ('google', 'Google'),
        ('facebook', 'Facebook'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20)
    provider_id = models.CharField(max_length=255)  # Google/Facebook unique ID

    created_at = models.DateTimeField(auto_now_add=True)



class TestAccount(models.Model):
    user_id = models.CharField(max_length=100,unique = True)
    created_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.user_id




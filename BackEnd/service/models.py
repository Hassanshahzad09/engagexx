from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('buyer','Buyer'),
        ('seller','Seller'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10,choices=ROLE_CHOICES)
    wallet_balance = models.DecimalField(max_digits=10,decimal_places=2,default=0)

class BuyerProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    totalSpend = models.DecimalField(max_digits=10,decimal_places=2,default=0)

class SellerProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    totalEarnings = models.DecimalField(max_digits=10,decimal_places=2,default=0)

    #Ratings will be provided by using Machine Learning Algorithm based on the reviews system
    
    ratings = models.IntegerField(default=1,validators=[MinValueValidator(1),MaxValueValidator(5)])

class BuyerTasks(models.Model):
    buyer = models.ForeignKey(BuyerProfile,on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)
    taskType = models.CharField(max_length=50)
    url = models.URLField()
    progressed = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    goal = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    status = models.CharField(max_length=20,default="pending") # pending, in_progress, completed
    pricePerAction = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    startDate = models.DateTimeField(auto_now_add=True)

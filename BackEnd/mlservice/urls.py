from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('allocate-jobs/', views.allocate_jobs, name='allocate_jobs'),
]
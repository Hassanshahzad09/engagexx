from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('analyzeTiming/', views.suspiciousTimingAnalysis, name='suspiciousTimingAnalysis'),
    path('analyzeRepetitiveTasks/', views.analyzeRepetitiveBehavior, name='analyze_repetitive_behavior'),
    path('detectIpAnomalies/', views.detect_ip_anomalies, name='detect_ip_anomalies'),
    path('predictFraud/', views.predict_fraud, name='predict_fraud')
]
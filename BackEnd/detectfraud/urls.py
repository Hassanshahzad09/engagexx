from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
   # path('analyzeTiming/', views.suspiciousTimingAnalysis, name='suspiciousTimingAnalysis'),
    #path('analyzeRepetitiveTasks/', views.analyzeRepetitiveBehavior, name='analyze_repetitive_behavior'),
    #path('detectIpAnomalies/', views.detect_ip_anomalies, name='detect_ip_anomalies'),
    #path('predictFraud/', views.predict_fraud, name='predict_fraud'),
    #path(
     #   "upload-job-screenshot/<int:task_id>/<int:seller_id>/",
      #  views.upload_job_screenshot_proof,
       # name="upload-job-screenshot"
    #),
   path('analyze-submission/', views.analyze_seller_submission, name='analyze-submission'),
   
]
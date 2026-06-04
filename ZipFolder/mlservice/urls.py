from django.urls import path
from . import views

urlpatterns = [
    path('allocate-jobs/', views.allocate_jobs, name='allocate_jobs'),
    path('log-seller-data/', views.log_seller_data, name='log_seller_data'),
    path('retrain/', views.retrain_model, name='retrain_model'),
]
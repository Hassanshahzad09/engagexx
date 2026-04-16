from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.signup, name="signup"),
    path('login/', views.login, name="login"),
    path('create-task/', views.create_task, name="create-task"),
    path('buyer-dashboard-stats/<int:user_id>/', views.buyer_dashboard_stats, name="buyer-dashboard-stats"),
    path('admin-pending-tasks/', views.admin_pending_tasks, name="admin-pending-tasks"),
    path('approved-tasks/', views.approved_tasks, name="approved-tasks"),
    path('approve-task/<int:task_id>/', views.approve_task, name="approve-task"),
    path('reject-task/<int:task_id>/', views.reject_task, name="reject-task"),
]

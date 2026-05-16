from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name="signup"),
    path('login/', views.login, name="login"),
    path('wallet-balance/<int:user_id>/', views.get_wallet_balance, name="wallet-balance"),
    path('add-funds/', views.add_funds, name="add-funds"),
    path('transactions/<int:user_id>/', views.get_transactions, name="transactions"),
    path('create-task/', views.create_task, name="create-task"),
    path('buyer-dashboard-stats/<int:user_id>/', views.buyer_dashboard_stats, name="buyer-dashboard-stats"),
    path('admin-pending-tasks/', views.admin_pending_tasks, name="admin-pending-tasks"),
    path('admin-active-tasks/', views.admin_active_tasks, name="admin-active-tasks"),
    path('admin-dashboard-summary/', views.admin_dashboard_summary, name="admin-dashboard-summary"),
    path('approved-tasks/', views.approved_tasks, name="approved-tasks"),
    path('seller-dashboard-stats/<int:user_id>/', views.seller_dashboard_stats, name="seller-dashboard-stats"),
    path('submit-task/', views.submit_task, name="submit-task"),
    path('withdraw-funds/', views.withdraw_funds, name="withdraw-funds"),
    path('approve-task/<int:task_id>/', views.approve_task, name="approve-task"),
    path('reject-task/<int:task_id>/', views.reject_task, name="reject-task"),
    path('complete-task/<int:task_id>/', views.complete_task, name="complete-task"),
    path('report-unethical-task/<int:task_id>/', views.report_unethical_task, name="report-unethical-task"),
    path('seller-list/', views.SellerList, name="seller-list"),
    path('rating-indexes/', views.getRatingIndexes, name="rating-indexes"),
    path('assign-jobs/', views.assign_jobs_api, name="assign-jobs"),
    path('connections/', views.connections_status),
    path('disconnect/<str:platform>/', views.disconnect_platform),

]

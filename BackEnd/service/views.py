import json

from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import BuyerProfile, BuyerTasks, SellerProfile, User


@csrf_exempt
def signup(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("userEmail")
    password = data.get("userPass")
    username = data.get("userName")
    user_role = data.get("user_Type")

    if not first_name or not last_name:
        return JsonResponse({"error": "First name and last name required"}, status=400)

    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    if not username:
        return JsonResponse({"error": "Username is required"}, status=400)

    if not password:
        return JsonResponse({"error": "Password is required"}, status=400)

    if user_role not in ["buyer", "seller"]:
        return JsonResponse({"error": "Invalid role"}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already exists"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username already exists"}, status=400)

    user = User.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        username=username,
        role=user_role,
        password=make_password(password),
        date_joined=timezone.now(),
    )

    if user_role == "buyer":
        BuyerProfile.objects.create(user=user)
    elif user_role == "seller":
        SellerProfile.objects.create(user=user)

    return JsonResponse(
        {
            "message": f"Signup successful for role: {user_role}",
            "username": user.username,
            "email": user.email,
        },
        status=201,
    )


@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    email = data.get("userEmail")
    password = data.get("userPass")
    user_type = data.get("user_Type")

    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    if not password:
        return JsonResponse({"error": "Password is required"}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({"error": "Invalid email or password"}, status=400)

    if not check_password(password, user.password):
        return JsonResponse({"error": "Invalid email or password"}, status=400)

    is_admin_user = user.is_staff or user.is_superuser

    if user_type == "admin":
        if not is_admin_user:
            return JsonResponse({"error": "This account is not an admin account"}, status=400)
    elif user.role != user_type:
        return JsonResponse({"error": "User role mismatch"}, status=400)

    return JsonResponse(
        {
            "message": "Login successful",
            "firstName": user.first_name,
            "email": user.email,
            "userId": user.id,
            "role": "admin" if is_admin_user else user.role,
            "isAdmin": is_admin_user,
        },
        status=200,
    )


@csrf_exempt
def create_task(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    user_id = data.get("userId")
    title = data.get("title")
    platform = data.get("platform")
    task_type = data.get("taskType")
    url = data.get("url")
    goal = data.get("goal")
    price_per_action = data.get("pricePerAction")

    if not user_id:
        return JsonResponse({"error": "userId is required"}, status=400)

    if not title or not platform or not task_type or not url:
        return JsonResponse({"error": "All task fields are required"}, status=400)

    if not goal or not price_per_action:
        return JsonResponse({"error": "Goal and price are required"}, status=400)

    try:
        buyer_profile = BuyerProfile.objects.get(user__id=user_id)
    except BuyerProfile.DoesNotExist:
        return JsonResponse({"error": "Buyer profile not found"}, status=404)

    task = BuyerTasks.objects.create(
        buyer=buyer_profile,
        title=title,
        platform=platform,
        taskType=task_type,
        url=url,
        goal=goal,
        pricePerAction=price_per_action,
        progressed=0,
        status="pending",
        approval_status="pending",
    )

    return JsonResponse(
        {
            "message": "Task created and sent for admin approval",
            "taskId": task.id,
        },
        status=201,
    )


def buyer_dashboard_stats(request, user_id):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    tasks = BuyerTasks.objects.filter(buyer__user__id=user_id)
    active_tasks = tasks.filter(approval_status="approved").exclude(status="completed").count()
    completed_tasks = tasks.filter(status="completed").count()
    all_tasks = tasks.count()
    total_engagement = sum(float(task.progressed) for task in tasks)

    performance = 0
    if all_tasks > 0:
        performance = round((completed_tasks / all_tasks) * 100)

    task_list = []
    for task in tasks:
        task_list.append(
            {
                "id": task.id,
                "title": task.title,
                "platform": task.platform.title(),
                "type": task.taskType.title(),
                "target": float(task.goal),
                "completed": float(task.progressed),
                "status": task.status,
                "approval_status": task.approval_status,
                "price": float(task.pricePerAction),
                "created": task.startDate.strftime("%Y-%m-%d %H:%M") if task.startDate else "",
                "rejection_reason": task.rejection_reason,
            }
        )

    return JsonResponse(
        {
            "activeTasks": active_tasks,
            "completedTasks": completed_tasks,
            "allTasks": all_tasks,
            "totalEngagement": total_engagement,
            "performance": performance,
            "tasks": task_list,
        },
        status=200,
    )


def admin_pending_tasks(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    tasks = BuyerTasks.objects.filter(approval_status="pending").select_related("buyer__user")

    data = []
    for task in tasks:
        data.append(
            {
                "id": task.id,
                "buyerName": task.buyer.user.username,
                "title": task.title,
                "platform": task.platform.title(),
                "taskType": task.taskType.title(),
                "goal": float(task.goal),
                "pricePerAction": float(task.pricePerAction),
                "url": task.url,
                "created": task.startDate.strftime("%Y-%m-%d %H:%M") if task.startDate else "",
            }
        )

    return JsonResponse({"tasks": data}, status=200)


def approved_tasks(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    tasks = BuyerTasks.objects.filter(approval_status="approved").exclude(status="completed")

    data = []
    for task in tasks:
        remaining = float(task.goal) - float(task.progressed)
        data.append(
            {
                "id": task.id,
                "title": task.title,
                "platform": task.platform.title(),
                "type": task.taskType.title(),
                "price": float(task.pricePerAction),
                "remaining": max(remaining, 0),
                "total": float(task.goal),
                "timeEstimate": "2 min",
                "difficulty": "Easy",
            }
        )

    return JsonResponse({"tasks": data}, status=200)


@csrf_exempt
def approve_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        task = BuyerTasks.objects.get(id=task_id)
    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    if task.approval_status != "pending":
        return JsonResponse({"error": "Task already reviewed"}, status=400)

    task.approval_status = "approved"
    task.status = "in_progress"
    task.reviewed_date = timezone.now()
    task.save()

    return JsonResponse({"message": "Task approved successfully"}, status=200)


@csrf_exempt
def reject_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        task = BuyerTasks.objects.get(id=task_id)
    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    if task.approval_status != "pending":
        return JsonResponse({"error": "Task already reviewed"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    reason = data.get("reason", "")
    task.approval_status = "rejected"
    task.rejection_reason = reason
    task.reviewed_date = timezone.now()
    task.save()

    return JsonResponse({"message": "Task rejected successfully"}, status=200)

import json
import base64
import uuid
from decimal import Decimal, InvalidOperation
import requests
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from BackEnd.utils import assign_jobs_round_robin
from .models import BuyerProfile, BuyerTasks, EasypaisaTransaction, RatingIndexes, SellerBehaviorLog, SellerProfile, SellerWithdrawalRequest, User,JobsHistory,TestAccount,SocialAccount,SocialAuth,Transaction,VirtualWallet
from .seller_rating import calculate_seller_rating, rating_dataset_summary, update_seller_rating
from django.db import transaction
from django.views.decorators.http import require_http_methods


def get_easypaisa_credentials_header():
    raw_credentials = f"{settings.EASYPAISA_USERNAME}:{settings.EASYPAISA_PASSWORD}"
    encoded_credentials = base64.b64encode(raw_credentials.encode()).decode()
    return {
        "Credentials": encoded_credentials,
        "Content-Type": "application/json",
    }


def generate_easypaisa_order_id():
    return f"EP{uuid.uuid4().hex[:12].upper()}"


def generate_withdrawal_reference():
    return f"WD{uuid.uuid4().hex[:12].upper()}"


def is_valid_easypaisa_mobile(value):
    return bool(value) and value.isdigit() and len(value) == 11 and value.startswith("03")


def get_easypaisa_error_message(code):
    errors = {
        "0001": "EasyPaisa system error. Please try again.",
        "0002": "Required payment field is missing or incorrect.",
        "0003": "Invalid EasyPaisa order ID.",
        "0004": "Invalid merchant account number.",
        "0005": "Merchant account is not active.",
        "0006": "Invalid EasyPaisa store ID.",
        "0007": "EasyPaisa store is not active.",
        "0008": "EasyPaisa payment method is not enabled.",
        "0010": "Invalid EasyPaisa credentials.",
        "0013": "Low balance in EasyPaisa account.",
        "0014": "EasyPaisa account does not exist.",
        "0015": "Invalid token expiry.",
        "0016": "Expiry date should be a future date.",
    }
    return errors.get(str(code or ""), "EasyPaisa payment failed. Please try again.")


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def create_seller_behavior_log(request, job):
    return SellerBehaviorLog.objects.create(
        job=job,
        task_id=str(job.task_id or job.task.id),
        seller_id=str(job.seller_id or job.seller.id),
        ip_address=get_client_ip(request),
        device_id=request.headers.get("X-Device-Id", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def initiate_easypaisa_ma_transaction(payload):
    if settings.EASYPAISA_MOCK_PAYMENTS:
        return {
            "orderId": payload["orderId"],
            "storeId": payload["storeId"],
            "transactionId": f"MOCK{uuid.uuid4().hex[:8].upper()}",
            "transactionDateTime": timezone.now().strftime("%d/%m/%Y %I:%M %p"),
            "responseCode": "0000",
            "responseDesc": "SUCCESS",
        }

    if not settings.EASYPAISA_USERNAME or not settings.EASYPAISA_PASSWORD:
        raise ValueError("EasyPaisa credentials are missing")

    response = requests.post(
        settings.EASYPAISA_MA_URL,
        json=payload,
        headers=get_easypaisa_credentials_header(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
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
def get_wallet_balance(request, user_id):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse(
        {
            "userId": user.id,
            "username": user.username,
            "role": user.role,
            "walletBalance": float(user.wallet_balance or 0),
        },
        status=200,
    )


@csrf_exempt
def add_funds(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    user_id = data.get("userId")
    amount = data.get("amount")
    default_payment_method = "easypaisa" if request.path.endswith("/easypaisa-pay/") else "manual"
    payment_method = data.get("paymentMethod", default_payment_method)
    description = data.get("description", "Wallet top up")

    if not user_id:
        return JsonResponse({"error": "userId is required"}, status=400)

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        return JsonResponse({"error": "Invalid amount"}, status=400)

    if amount <= 0:
        return JsonResponse({"error": "Amount must be greater than zero"}, status=400)

    if str(payment_method).lower() == "easypaisa":
        mobile_number = data.get("mobileNumber") or data.get("easypaisaAccount")

        if not is_valid_easypaisa_mobile(str(mobile_number or "")):
            return JsonResponse({"error": "Enter valid EasyPaisa number, for example 03xxxxxxxxx"}, status=400)

        try:
            user = User.objects.get(id=user_id)
            buyer = BuyerProfile.objects.get(user=user)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except BuyerProfile.DoesNotExist:
            return JsonResponse({"error": "Buyer profile not found"}, status=404)

        order_id = generate_easypaisa_order_id()
        email = data.get("email") or user.email
        payload = {
            "orderId": order_id,
            "storeId": settings.EASYPAISA_STORE_ID,
            "transactionAmount": str(amount),
            "transactionType": "MA",
            "mobileAccountNo": mobile_number,
            "emailAddress": email,
        }
        easypaisa_txn = EasypaisaTransaction.objects.create(
            buyer=buyer,
            order_id=order_id,
            amount=amount,
            mobile_number=mobile_number,
            email=email,
            status="pending",
        )

        try:
            result = initiate_easypaisa_ma_transaction(payload)
        except ValueError as error:
            easypaisa_txn.status = "failed"
            easypaisa_txn.response_desc = str(error)
            easypaisa_txn.save(update_fields=["status", "response_desc", "updated_at"])
            return JsonResponse({"error": str(error)}, status=500)
        except requests.RequestException:
            easypaisa_txn.status = "failed"
            easypaisa_txn.response_desc = "EasyPaisa server not reachable"
            easypaisa_txn.save(update_fields=["status", "response_desc", "updated_at"])
            return JsonResponse({"error": "EasyPaisa server not reachable"}, status=500)

        response_code = str(result.get("responseCode") or "")
        response_desc = result.get("responseDesc") or ""
        ep_txn_id = result.get("transactionId") or ""
        easypaisa_txn.response_code = response_code
        easypaisa_txn.response_desc = response_desc
        easypaisa_txn.ep_txn_id = ep_txn_id

        if response_code != "0000":
            easypaisa_txn.status = "failed"
            easypaisa_txn.save()
            return JsonResponse(
                {
                    "error": get_easypaisa_error_message(response_code),
                    "code": response_code,
                    "responseDesc": response_desc,
                },
                status=400,
            )

        with transaction.atomic():
            locked_user = User.objects.select_for_update().get(id=user.id)
            locked_txn = EasypaisaTransaction.objects.select_for_update().get(id=easypaisa_txn.id)

            if locked_txn.status == "pending":
                locked_user.wallet_balance = (locked_user.wallet_balance or Decimal("0.00")) + amount
                locked_user.save(update_fields=["wallet_balance"])
                locked_txn.status = "success"
                locked_txn.response_code = response_code
                locked_txn.response_desc = response_desc
                locked_txn.ep_txn_id = ep_txn_id
                locked_txn.save()
                Transaction.objects.create(
                    user=locked_user,
                    amount=amount,
                    type="deposit",
                    description=f"EasyPaisa wallet top up, order {order_id}",
                )

        return JsonResponse(
            {
                "message": "EasyPaisa payment successful. Wallet updated.",
                "walletBalance": float(locked_user.wallet_balance),
                "orderId": order_id,
                "transactionId": ep_txn_id,
                "mockPayment": settings.EASYPAISA_MOCK_PAYMENTS,
            },
            status=200,
        )

    try:
        with transaction.atomic():
            user = User.objects.select_for_update().get(id=user_id)
            user.wallet_balance = (user.wallet_balance or Decimal("0.00")) + amount
            user.save(update_fields=["wallet_balance"])

            Transaction.objects.create(
                user=user,
                amount=amount,
                type="deposit",
                description=f"{description} via {payment_method}",
            )
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse(
        {
            "message": "Funds added successfully",
            "walletBalance": float(user.wallet_balance),
        },
        status=200,
    )


@csrf_exempt
def get_transactions(request, user_id):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    transactions = Transaction.objects.filter(user=user).order_by("-created_at")
    data = []

    for item in transactions:
        data.append(
            {
                "id": item.id,
                "amount": float(item.amount),
                "type": item.type,
                "description": item.description,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

    return JsonResponse({"transactions": data}, status=200)


@csrf_exempt
def easypaisa_inquire(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    order_id = data.get("orderId")

    if not order_id:
        return JsonResponse({"error": "orderId is required"}, status=400)

    try:
        local_txn = EasypaisaTransaction.objects.select_related("buyer__user").get(order_id=order_id)
    except EasypaisaTransaction.DoesNotExist:
        return JsonResponse({"error": "EasyPaisa transaction not found"}, status=404)

    if settings.EASYPAISA_MOCK_PAYMENTS:
        result = {
            "orderId": order_id,
            "accountNum": settings.EASYPAISA_ACCOUNT_NUM,
            "storeId": settings.EASYPAISA_STORE_ID,
            "transactionStatus": "PAID" if local_txn.status == "success" else "PENDING",
            "transactionAmount": str(local_txn.amount),
            "responseCode": "0000",
            "responseDesc": "SUCCESS",
        }
    else:
        payload = {
            "orderId": order_id,
            "storeId": settings.EASYPAISA_STORE_ID,
            "accountNum": settings.EASYPAISA_ACCOUNT_NUM,
        }

        try:
            response = requests.post(
                settings.EASYPAISA_INQUIRE_URL,
                json=payload,
                headers=get_easypaisa_credentials_header(),
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except requests.RequestException:
            return JsonResponse({"error": "EasyPaisa server not reachable"}, status=500)

    transaction_status = result.get("transactionStatus")
    response_code = str(result.get("responseCode") or "")

    if transaction_status == "PAID" and response_code == "0000":
        with transaction.atomic():
            locked_txn = EasypaisaTransaction.objects.select_for_update().select_related("buyer__user").get(order_id=order_id)
            buyer_user = User.objects.select_for_update().get(id=locked_txn.buyer.user.id)

            if locked_txn.status == "pending":
                buyer_user.wallet_balance = (buyer_user.wallet_balance or Decimal("0.00")) + locked_txn.amount
                buyer_user.save(update_fields=["wallet_balance"])
                locked_txn.status = "success"
                locked_txn.response_code = response_code
                locked_txn.response_desc = result.get("responseDesc") or ""
                locked_txn.save()
                Transaction.objects.create(
                    user=buyer_user,
                    amount=locked_txn.amount,
                    type="deposit",
                    description=f"EasyPaisa wallet top up confirmed, order {order_id}",
                )

    return JsonResponse(
        {
            "orderId": order_id,
            "transactionStatus": transaction_status,
            "responseCode": response_code,
            "responseDesc": result.get("responseDesc"),
            "amount": result.get("transactionAmount"),
            "dateTime": result.get("transactionDateTime"),
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
        goal = Decimal(str(goal))
        price_per_action = Decimal(str(price_per_action))

        if goal <= 0 or price_per_action <= 0:
            return JsonResponse({"error": "Goal and price must be greater than zero"}, status=400)

        with transaction.atomic():
            buyer_user = User.objects.get(id=user_id)
            buyer_profile = BuyerProfile.objects.get(user=buyer_user)

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
    except BuyerProfile.DoesNotExist:
        return JsonResponse({"error": "Buyer profile not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

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

    try:
        buyer_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

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
            "walletBalance": float(buyer_user.wallet_balance or 0),
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


def admin_active_tasks(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    tasks = BuyerTasks.objects.filter(
        approval_status="approved"
    ).exclude(
        status="completed"
    ).select_related("buyer__user").prefetch_related("jobs")

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
                "progressed": float(task.progressed),
                "pricePerAction": float(task.pricePerAction),
                "url": task.url,
                "status": task.status,
                "assignedSellers": task.jobs.values("seller_id").distinct().count(),
                "created": task.startDate.strftime("%Y-%m-%d %H:%M") if task.startDate else "",
            }
        )

    return JsonResponse({"tasks": data}, status=200)


def admin_task_assigned_sellers(request, task_id):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    try:
        task = BuyerTasks.objects.get(id=task_id)
    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    jobs = (
        JobsHistory.objects
        .filter(task=task)
        .select_related("seller__user")
        .order_by("seller__user__username", "id")
    )

    sellers = []
    seen_seller_ids = set()

    for job in jobs:
        seller = job.seller
        if seller.id in seen_seller_ids:
            continue
        seen_seller_ids.add(seller.id)

        seller_user = seller.user
        rating_data = calculate_seller_rating(seller)

        sellers.append({
            "jobId": job.id,
            "sellerId": seller.id,
            "name": seller_user.get_full_name() or seller_user.username,
            "email": seller_user.email,
            "rating": rating_data["rating"],
            "trustScore": rating_data["trust_score"],
            "finalReputationScore": rating_data["final_reputation_score"],
            "jobStatus": job.status,
            "proofStatus": job.proofStatus,
            "auditStatus": job.auditStatus,
            "priceEarned": float(job.priceEarned or 0),
        })

    return JsonResponse({
        "task": {
            "id": task.id,
            "title": task.title,
            "platform": task.platform.title(),
            "taskType": task.taskType.title(),
        },
        "sellers": sellers,
    }, status=200)

def admin_dashboard_summary(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    total_revenue = Transaction.objects.filter(type="escrow_in").aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    monthly_revenue = Transaction.objects.filter(type="escrow_in").annotate(
        month=TruncMonth("created_at")
    ).values("month").annotate(
        revenue=Sum("amount")
    ).order_by("month")

    monthly_users = User.objects.annotate(
        month=TruncMonth("date_joined")
    ).values("month").annotate(
        users=Count("id")
    ).order_by("month")

    monthly_data = {}
    for item in monthly_revenue:
        if item["month"]:
            key = item["month"].strftime("%Y-%m")
            monthly_data[key] = {
                "name": item["month"].strftime("%b %Y"),
                "revenue": float(item["revenue"] or 0),
                "users": 0,
            }

    for item in monthly_users:
        if item["month"]:
            key = item["month"].strftime("%Y-%m")
            if key not in monthly_data:
                monthly_data[key] = {
                    "name": item["month"].strftime("%b %Y"),
                    "revenue": 0,
                    "users": 0,
                }
            monthly_data[key]["users"] = item["users"]

    task_distribution = []
    for item in BuyerTasks.objects.values("platform").annotate(value=Count("id")).order_by("-value"):
        task_distribution.append(
            {
                "name": (item["platform"] or "Unknown").title(),
                "value": item["value"],
            }
        )

    recent_users = []
    for user in User.objects.order_by("-date_joined")[:10]:
        user_type = "Admin" if user.is_staff or user.is_superuser else (user.role or "User").title()
        recent_users.append(
            {
                "id": user.id,
                "name": user.get_full_name() or user.username,
                "email": user.email,
                "type": user_type,
                "status": "Active" if user.is_active else "Suspended",
                "joined": user.date_joined.strftime("%Y-%m-%d") if user.date_joined else "",
            }
        )

    flagged_users = []
    flagged_sellers = SellerProfile.objects.filter(
        unethical_reports__gt=0
    ).select_related("user").order_by("-unethical_reports")

    for seller in flagged_sellers:
        flagged_users.append(
            {
                "id": seller.user.id,
                "name": seller.user.get_full_name() or seller.user.username,
                "email": seller.user.email,
                "type": "Seller",
                "status": "Active" if seller.user.is_active else "Suspended",
                "joined": seller.user.date_joined.strftime("%Y-%m-%d") if seller.user.date_joined else "",
                "reports": seller.unethical_reports,
            }
        )

    return JsonResponse(
        {
            "stats": {
                "totalUsers": User.objects.count(),
                "revenue": float(total_revenue),
                "activeTasks": BuyerTasks.objects.filter(
                    approval_status="approved"
                ).exclude(status="completed").count(),
                "pendingTasks": BuyerTasks.objects.filter(approval_status="pending").count(),
            },
            "revenueData": list(monthly_data.values()),
            "taskDistribution": task_distribution,
            "recentUsers": recent_users,
            "flaggedUsers": flagged_users,
        },
        status=200,
    )


def build_job_fraud_analysis(job):
    fraud_probability = 0
    causes = []

    if job.proofStatus == "invalid":
        fraud_probability += 40
        causes.append("Proof was marked invalid")

    if job.auditStatus == "failed":
        fraud_probability += 35
        causes.append("Delayed audit failed")

    if job.completionTime and job.completionTime > 0 and job.completionTime < Decimal("0.0167"):
        fraud_probability += 15
        causes.append("Task completed unusually fast")

    if job.proofUrl:
        duplicate_count = JobsHistory.objects.filter(proofUrl=job.proofUrl).exclude(id=job.id).count()
        if duplicate_count > 0:
            fraud_probability += 25
            causes.append("Same proof URL used in another submission")

    if job.seller.unethical_reports > 0:
        fraud_probability += min(job.seller.unethical_reports * 10, 20)
        causes.append("Seller has previous unethical reports")

    fraud_probability = min(fraud_probability, 100)

    if not causes:
        causes.append("No strong fraud signals")

    return {
        "fraudProbability": fraud_probability,
        "fraudCauses": causes,
    }


def admin_seller_monitor(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    sellers = SellerProfile.objects.select_related("user").prefetch_related("jobs__task").all()
    seller_rows = []

    for seller in sellers:
        rating_data = calculate_seller_rating(seller)
        seller_rows.append({
            "id": seller.id,
            "userId": seller.user.id,
            "name": seller.user.get_full_name() or seller.user.username,
            "email": seller.user.email,
            "isOnline": seller.user.is_active,
            "trustScore": rating_data["trust_score"],
            "rating": rating_data["rating"],
            "ratingLabel": rating_data["rating_label"],
            "performanceScore": rating_data["performance_score"],
            "finalReputationScore": rating_data["final_reputation_score"],
            "successRate": rating_data["success_rate"],
            "completedTasks": rating_data["completed_tasks"],
            "validProofs": rating_data["valid_proofs"],
            "invalidProofs": rating_data["invalid_proofs"],
            "auditPassedTasks": rating_data["audit_passed_tasks"],
            "auditFailedTasks": rating_data["audit_failed_tasks"],
        })

    proof_jobs = (
        JobsHistory.objects
        .exclude(proofUrl="")
        .select_related("seller__user", "task")
        .order_by("-endDate", "-startDate")[:100]
    )

    proof_rows = []
    for job in proof_jobs:
        rating_data = calculate_seller_rating(job.seller)
        fraud_data = build_job_fraud_analysis(job)
        proof_rows.append({
            "jobId": job.id,
            "sellerId": job.seller.id,
            "sellerName": job.seller.user.get_full_name() or job.seller.user.username,
            "sellerEmail": job.seller.user.email,
            "taskTitle": job.task.title,
            "platform": job.task.platform.title(),
            "taskType": job.task.taskType.title(),
            "proofUrl": job.proofUrl,
            "proofStatus": job.proofStatus,
            "auditStatus": job.auditStatus,
            "submittedAt": job.endDate.strftime("%Y-%m-%d %H:%M") if job.endDate else "",
            "completionTimeHours": float(job.completionTime or 0),
            "trustScore": rating_data["trust_score"],
            "rating": rating_data["rating"],
            "ratingLabel": rating_data["rating_label"],
            **fraud_data,
        })

    return JsonResponse({
        "onlineSellers": [seller for seller in seller_rows if seller["isOnline"]],
        "sellers": seller_rows,
        "proofs": proof_rows,
    }, status=200)


def get_seller_profile_from_user_id(user_id):
    try:
        return SellerProfile.objects.get(user_id=user_id)
    except SellerProfile.DoesNotExist:
        return SellerProfile.objects.get(id=user_id)


def assign_task_to_available_sellers(task):
    sellers = SellerProfile.objects.all()
    assigned_count = 0

    for seller in sellers:
        _, created = JobsHistory.objects.get_or_create(
            task=task,
            seller=seller,
            defaults={"taskId": task.id, "status": "pending"},
        )
        if created:
            assigned_count += 1

    return assigned_count


def get_connected_platforms_for_seller(seller_profile):
    seller_ids = {seller_profile.user_id, seller_profile.id}
    platforms = SocialAccount.objects.filter(
        sellerId__in=seller_ids
    ).values_list("platform", flat=True)

    return {
        (platform or "").strip().lower()
        for platform in platforms
        if platform
    }


def approved_tasks(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    userId = request.GET.get("userId")
    if not userId:
        return JsonResponse({"error": "userId is required"}, status=400)

    try:
        seller_profile = get_seller_profile_from_user_id(userId)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)

    connected_platforms = get_connected_platforms_for_seller(seller_profile)
    if not connected_platforms:
        return JsonResponse({"tasks": []}, status=200)

    jobs = JobsHistory.objects.filter(
        status="pending",
        seller=seller_profile,
        task__approval_status="approved",
        task__virtual_wallet__status="holding",
    ).select_related("task")

    data = []

    for job in jobs:
        task = job.task
        platform = (task.platform or "").strip()
        if platform.lower() not in connected_platforms:
            continue

        goal = float(task.goal or 0)
        progressed = float(task.progressed or 0)
        price = float(task.pricePerAction or 0)
        remaining = goal - progressed

        data.append({
            "id": task.id,
            "jobId": job.id,
            "title": task.title,
            "platform": platform.title(),
            "type": (task.taskType or "").title(),
            "url": task.url,
            "price": price,
            "remaining": max(remaining, 0),
            "total": goal,
            "timeEstimate": "2 min",
            "difficulty": "Easy",
            "status": "assigned",
        })

    return JsonResponse({"tasks": data}, status=200)


@csrf_exempt
def submit_task(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    task_id = data.get("taskId")
    seller_id = data.get("sellerId")
    proof_url = data.get("proofUrl", "")
    notes = data.get("notes", "")
    time_spent_seconds = data.get("timeSpent", 0)

    if not task_id or not seller_id:
        return JsonResponse({"error": "taskId and sellerId are required"}, status=400)

    if not proof_url:
        return JsonResponse({"error": "Proof URL is required"}, status=400)

    try:
        time_spent_seconds = Decimal(str(time_spent_seconds))
    except (InvalidOperation, TypeError):
        time_spent_seconds = Decimal("0.00")

    if time_spent_seconds < 0:
        time_spent_seconds = Decimal("0.00")

    time_spent = (time_spent_seconds / Decimal("3600.00")).quantize(Decimal("0.0001"))

    try:
        with transaction.atomic():
            seller_profile = get_seller_profile_from_user_id(seller_id)
            task = BuyerTasks.objects.select_for_update().get(id=task_id)
            virtual_wallet = VirtualWallet.objects.select_for_update().get(task=task)
            job = JobsHistory.objects.select_for_update().get(
                task=task,
                seller=seller_profile,
                status="pending",
            )
            platform = (task.platform or "").strip().lower()
            connected_platforms = get_connected_platforms_for_seller(seller_profile)

            if platform not in connected_platforms:
                return JsonResponse(
                    {"error": f"Connect {task.platform} before submitting this task"},
                    status=400,
                )

            if virtual_wallet.status != "holding":
                return JsonResponse({"error": "Task payment is not available"}, status=400)

            remaining_actions = (task.goal or Decimal("0.00")) - (task.progressed or Decimal("0.00"))
            if remaining_actions <= 0:
                return JsonResponse({"error": "Task goal is already completed"}, status=400)

            payment_amount = task.pricePerAction or Decimal("0.00")
            if payment_amount <= 0:
                return JsonResponse({"error": "Task price is not valid"}, status=400)

            if virtual_wallet.amount < payment_amount:
                return JsonResponse({"error": "Task payment wallet does not have enough balance"}, status=400)

            seller_user = seller_profile.user
            seller_user.wallet_balance = (seller_user.wallet_balance or Decimal("0.00")) + payment_amount
            seller_user.save(update_fields=["wallet_balance"])

            seller_profile.totalEarnings = (seller_profile.totalEarnings or Decimal("0.00")) + payment_amount
            seller_profile.avgCompletionTime = time_spent
            seller_profile.save(update_fields=["totalEarnings", "avgCompletionTime"])

            job.proofUrl = proof_url
            job.proofStatus = "valid"
            job.proofReviewedDate = timezone.now()
            job.notes = notes
            job.completionTime = time_spent
            job.status = "completed"
            job.progress = Decimal("1.00")
            job.priceEarned = payment_amount
            job.endDate = timezone.now()
            job.save(update_fields=[
                "proofUrl",
                "proofStatus",
                "proofReviewedDate",
                "notes",
                "completionTime",
                "status",
                "progress",
                "priceEarned",
                "endDate",
            ])

            task.progressed = (task.progressed or Decimal("0.00")) + Decimal("1.00")
            if task.progressed >= task.goal:
                task.status = "completed"
                task.endDate = timezone.now()
            else:
                task.status = "in_progress"

            task.save(update_fields=["status", "progressed", "endDate"])

            virtual_wallet.amount = virtual_wallet.amount - payment_amount
            virtual_wallet.seller = seller_profile
            if task.status == "completed" or virtual_wallet.amount <= 0:
                virtual_wallet.status = "released"
            virtual_wallet.save(update_fields=["amount", "status", "seller", "updated_at"])

            Transaction.objects.create(
                user=seller_user,
                amount=payment_amount,
                type="escrow_release",
                description=f"Seller action completed: {task.title}",
            )

            rating_data = update_seller_rating(seller_profile)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)
    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except JobsHistory.DoesNotExist:
        return JsonResponse({"error": "This task is not assigned to this seller"}, status=400)
    except VirtualWallet.DoesNotExist:
        return JsonResponse({"error": "Task payment wallet not found"}, status=404)

    return JsonResponse({
        "message": "Task submitted successfully and one action payment released",
        "sellerRating": rating_data,
    }, status=200)


def seller_dashboard_stats(request, user_id):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    try:
        seller_profile = get_seller_profile_from_user_id(user_id)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)

    seller_user = seller_profile.user
    jobs = JobsHistory.objects.filter(seller=seller_profile).select_related("task")
    completed_jobs = jobs.filter(status="completed")
    pending_jobs = jobs.filter(status="pending", task__virtual_wallet__status="holding")
    total_jobs = jobs.count()
    completed_count = completed_jobs.count()
    success_rate = round((completed_count / total_jobs) * 100, 2) if total_jobs else 0

    my_tasks = []
    payable_jobs = (completed_jobs | pending_jobs).order_by("-startDate")[:10]
    for job in payable_jobs:
        my_tasks.append({
            "id": job.id,
            "title": job.task.title,
            "platform": job.task.platform.title(),
            "price": float(job.task.pricePerAction or 0),
            "status": "assigned" if job.status == "pending" else job.status,
            "submitted": job.endDate.strftime("%Y-%m-%d %H:%M") if job.endDate else job.startDate.strftime("%Y-%m-%d %H:%M"),
            "earnings": float(job.priceEarned or 0),
        })

    rating_data = calculate_seller_rating(seller_profile)

    return JsonResponse({
        "walletBalance": float(seller_user.wallet_balance or 0),
        "totalEarnings": float(seller_profile.totalEarnings or 0),
        "tasksCompleted": completed_count,
        "inProgress": pending_jobs.count(),
        "successRate": success_rate,
        "avgCompletionTime": float(seller_profile.avgCompletionTime or 0),
        "rating": rating_data["rating"],
        "ratingLabel": rating_data["rating_label"],
        "performanceScore": rating_data["performance_score"],
        "finalReputationScore": rating_data["final_reputation_score"],
        "trustScore": rating_data["trust_score"],
        "myTasks": my_tasks,
    }, status=200)


def seller_rating_detail(request, user_id):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    try:
        seller_profile = get_seller_profile_from_user_id(user_id)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)

    return JsonResponse(calculate_seller_rating(seller_profile), status=200)


@csrf_exempt
def refresh_seller_rating(request, user_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        seller_profile = get_seller_profile_from_user_id(user_id)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)

    return JsonResponse(update_seller_rating(seller_profile), status=200)


def seller_rating_dataset_summary(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    return JsonResponse(rating_dataset_summary(), status=200)


@csrf_exempt
def review_seller_proof(request, job_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    proof_status = data.get("proofStatus")
    if proof_status not in ["valid", "invalid"]:
        return JsonResponse({"error": "proofStatus must be valid or invalid"}, status=400)

    try:
        with transaction.atomic():
            job = JobsHistory.objects.select_for_update().select_related("seller", "task").get(id=job_id)
            job.proofStatus = proof_status
            job.proofReviewedDate = timezone.now()
            if proof_status == "invalid":
                job.status = "rejected"
            elif job.status == "rejected":
                job.status = "completed"
            job.save(update_fields=["proofStatus", "proofReviewedDate", "status"])
            behavior_log = None
            if proof_status == "valid":
                behavior_log = create_seller_behavior_log(request, job)
            rating_data = update_seller_rating(job.seller)
    except JobsHistory.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)

    return JsonResponse({
        "message": "Proof reviewed successfully",
        "jobId": job.id,
        "proofStatus": job.proofStatus,
        "behaviorLogId": behavior_log.id if behavior_log else None,
        "sellerRating": rating_data,
    }, status=200)


@csrf_exempt
def review_seller_audit(request, job_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    audit_status = data.get("auditStatus")
    if audit_status not in ["passed", "failed"]:
        return JsonResponse({"error": "auditStatus must be passed or failed"}, status=400)

    try:
        with transaction.atomic():
            job = JobsHistory.objects.select_for_update().select_related("seller").get(id=job_id)
            job.auditStatus = audit_status
            job.auditReviewedDate = timezone.now()
            if audit_status == "failed":
                job.status = "rejected"
                job.seller.unethical_reports = (job.seller.unethical_reports or 0) + 1
                job.seller.save(update_fields=["unethical_reports"])
            job.save(update_fields=["auditStatus", "auditReviewedDate", "status"])
            rating_data = update_seller_rating(job.seller)
    except JobsHistory.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)

    return JsonResponse({
        "message": "Audit reviewed successfully",
        "jobId": job.id,
        "auditStatus": job.auditStatus,
        "sellerRating": rating_data,
    }, status=200)


@csrf_exempt
def withdraw_funds(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    seller_id = data.get("sellerId")
    amount = data.get("amount")
    easypaisa_number = data.get("easypaisaNumber") or data.get("mobileNumber")
    account_title = data.get("accountTitle") or ""

    if not seller_id:
        return JsonResponse({"error": "sellerId is required"}, status=400)

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        return JsonResponse({"error": "Invalid amount"}, status=400)

    if amount <= 0:
        return JsonResponse({"error": "Amount must be greater than zero"}, status=400)

    if not is_valid_easypaisa_mobile(str(easypaisa_number or "")):
        return JsonResponse({"error": "Enter valid EasyPaisa number, for example 03xxxxxxxxx"}, status=400)

    if not account_title.strip():
        return JsonResponse({"error": "EasyPaisa account title is required"}, status=400)

    try:
        with transaction.atomic():
            seller_profile = get_seller_profile_from_user_id(seller_id)
            seller_user = User.objects.select_for_update().get(id=seller_profile.user.id)

            if (seller_user.wallet_balance or Decimal("0.00")) < amount:
                return JsonResponse({"error": "Not enough wallet balance"}, status=400)

            seller_user.wallet_balance = (seller_user.wallet_balance or Decimal("0.00")) - amount
            seller_user.save(update_fields=["wallet_balance"])

            Transaction.objects.create(
                user=seller_user,
                amount=amount,
                type="withdraw",
                description=f"EasyPaisa withdrawal request to {easypaisa_number}",
            )

            withdrawal = SellerWithdrawalRequest.objects.create(
                seller=seller_profile,
                amount=amount,
                easypaisa_number=easypaisa_number,
                account_title=account_title.strip(),
                reference=generate_withdrawal_reference(),
            )
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)

    return JsonResponse({
        "message": "EasyPaisa withdrawal request submitted",
        "walletBalance": float(seller_user.wallet_balance),
        "withdrawalReference": withdrawal.reference,
        "withdrawalStatus": withdrawal.status,
    }, status=200)


@csrf_exempt
def approve_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        with transaction.atomic():
            task = BuyerTasks.objects.select_for_update().get(id=task_id)

            if task.approval_status == "approved":
                return JsonResponse({"message": "Task already approved"}, status=200)

            if task.approval_status != "pending":
                return JsonResponse({"error": "Task already reviewed"}, status=400)

            total_cost = task.goal * task.pricePerAction
            virtual_wallet = VirtualWallet.objects.filter(task=task).first()

            if virtual_wallet is None:
                buyer_user = User.objects.select_for_update().get(id=task.buyer.user.id)

                if (buyer_user.wallet_balance or Decimal("0.00")) < total_cost:
                    return JsonResponse(
                        {"error": "Buyer does not have enough wallet balance to approve this task"},
                        status=400,
                    )

                buyer_user.wallet_balance = (buyer_user.wallet_balance or Decimal("0.00")) - total_cost
                buyer_user.save(update_fields=["wallet_balance"])

                VirtualWallet.objects.create(
                    task=task,
                    buyer=task.buyer,
                    amount=total_cost,
                    status="holding",
                )

                Transaction.objects.create(
                    user=buyer_user,
                    amount=total_cost,
                    type="escrow_in",
                    description=f"Escrow locked after admin approval for task: {task.title}",
                )

            task.approval_status = "approved"
            task.status = "in_progress"
            task.reviewed_date = timezone.now()
            task.save(update_fields=["approval_status", "status", "reviewed_date"])

    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

#Job Assignment Logic will be adding here
    return JsonResponse({"message": "Task approved successfully and amount deducted from buyer wallet"}, status=200)


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

@csrf_exempt
def complete_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    seller_id = data.get("sellerId")
    if not seller_id:
        return JsonResponse({"error": "sellerId is required"}, status=400)

    try:
        with transaction.atomic():
            task = BuyerTasks.objects.select_for_update().get(id=task_id)
            seller_profile = SellerProfile.objects.select_for_update().get(id=seller_id)
            virtual_wallet = VirtualWallet.objects.select_for_update().get(task=task)

            if virtual_wallet.status != "holding":
                return JsonResponse({"error": "Wallet is not in holding state"}, status=400)

            job_exists = JobsHistory.objects.filter(task=task, seller=seller_profile).exists()
            if not job_exists:
                return JsonResponse({"error": "Seller is not assigned to this task"}, status=400)

            seller_user = seller_profile.user
            seller_user.wallet_balance = (seller_user.wallet_balance or Decimal("0.00")) + virtual_wallet.amount
            seller_user.save(update_fields=["wallet_balance"])

            seller_profile.totalEarnings = (seller_profile.totalEarnings or Decimal("0.00")) + virtual_wallet.amount
            seller_profile.save(update_fields=["totalEarnings"])

            virtual_wallet.status = "released"
            virtual_wallet.seller = seller_profile
            virtual_wallet.save(update_fields=["status", "seller", "updated_at"])

            task.status = "completed"
            task.endDate = timezone.now()
            task.save(update_fields=["status", "endDate"])

            JobsHistory.objects.filter(task=task, seller=seller_profile).update(
                status="completed",
                progress=task.goal,
                priceEarned=virtual_wallet.amount,
                endDate=timezone.now(),
            )

            Transaction.objects.create(
                user=seller_user,
                amount=virtual_wallet.amount,
                type="escrow_release",
                description=f"Task completed: {task.title}",
            )
    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller not found"}, status=404)
    except VirtualWallet.DoesNotExist:
        return JsonResponse({"error": "Virtual wallet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Task completed and money released to seller"}, status=200)


@csrf_exempt
def report_unethical_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    seller_id = data.get("sellerId")
    reason = data.get("reason", "Unethical task behavior")
    if not seller_id:
        return JsonResponse({"error": "sellerId is required"}, status=400)

    try:
        with transaction.atomic():
            task = BuyerTasks.objects.select_for_update().get(id=task_id)
            seller_profile = SellerProfile.objects.select_for_update().get(id=seller_id)
            virtual_wallet = VirtualWallet.objects.select_for_update().get(task=task)

            if virtual_wallet.status != "holding":
                return JsonResponse({"error": "Wallet is not in holding state"}, status=400)

            buyer_user = virtual_wallet.buyer.user
            refund_amount = virtual_wallet.amount

            buyer_user.wallet_balance = (buyer_user.wallet_balance or Decimal("0.00")) + refund_amount
            buyer_user.save(update_fields=["wallet_balance"])

            virtual_wallet.status = "refunded"
            virtual_wallet.save(update_fields=["status", "updated_at"])

            task.status = "rejected"
            task.approval_status = "rejected"
            task.rejection_reason = reason
            task.reviewed_date = timezone.now()
            task.save(update_fields=["status", "approval_status", "rejection_reason", "reviewed_date"])

            seller_profile.unethical_reports = (seller_profile.unethical_reports or 0) + 1
            seller_profile.save(update_fields=["unethical_reports"])

            if seller_profile.unethical_reports >= 3:
                seller_profile.user.is_active = False
                seller_profile.user.save(update_fields=["is_active"])

            JobsHistory.objects.filter(task=task, seller=seller_profile).update(
                status="rejected",
                endDate=timezone.now(),
            )

            Transaction.objects.create(
                user=buyer_user,
                amount=refund_amount,
                type="refund",
                description=f"Refund for unethical task: {task.title}",
            )

    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller not found"}, status=404)
    except VirtualWallet.DoesNotExist:
        return JsonResponse({"error": "Virtual wallet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Task marked unethical and refunded to buyer"}, status=200)



@csrf_exempt
def complete_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    seller_id = data.get("sellerId")
    if not seller_id:
        return JsonResponse({"error": "sellerId is required"}, status=400)

    try:
        with transaction.atomic():
            task = BuyerTasks.objects.select_for_update().get(id=task_id)
            seller_profile = SellerProfile.objects.select_for_update().get(id=seller_id)
            virtual_wallet = VirtualWallet.objects.select_for_update().get(task=task)

            if virtual_wallet.status != "holding":
                return JsonResponse({"error": "Wallet is not in holding state"}, status=400)

            job_exists = JobsHistory.objects.filter(task=task, seller=seller_profile).exists()
            if not job_exists:
                return JsonResponse({"error": "Seller is not assigned to this task"}, status=400)

            seller_user = seller_profile.user
            seller_user.wallet_balance = (seller_user.wallet_balance or Decimal("0.00")) + virtual_wallet.amount
            seller_user.save(update_fields=["wallet_balance"])

            seller_profile.totalEarnings = (seller_profile.totalEarnings or Decimal("0.00")) + virtual_wallet.amount
            seller_profile.save(update_fields=["totalEarnings"])

            virtual_wallet.status = "released"
            virtual_wallet.seller = seller_profile
            virtual_wallet.save(update_fields=["status", "seller", "updated_at"])

            task.status = "completed"
            task.endDate = timezone.now()
            task.save(update_fields=["status", "endDate"])

            JobsHistory.objects.filter(task=task, seller=seller_profile).update(
                status="completed",
                progress=task.goal,
                priceEarned=virtual_wallet.amount,
                endDate=timezone.now(),
            )

            Transaction.objects.create(
                user=seller_user,
                amount=virtual_wallet.amount,
                type="escrow_release",
                description=f"Task completed: {task.title}",
            )
    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller not found"}, status=404)
    except VirtualWallet.DoesNotExist:
        return JsonResponse({"error": "Virtual wallet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Task completed and money released to seller"}, status=200)


@csrf_exempt
def report_unethical_task(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    seller_id = data.get("sellerId")
    reason = data.get("reason", "Unethical task behavior")
    if not seller_id:
        return JsonResponse({"error": "sellerId is required"}, status=400)

    try:
        with transaction.atomic():
            task = BuyerTasks.objects.select_for_update().get(id=task_id)
            seller_profile = SellerProfile.objects.select_for_update().get(id=seller_id)
            virtual_wallet = VirtualWallet.objects.select_for_update().get(task=task)

            if virtual_wallet.status != "holding":
                return JsonResponse({"error": "Wallet is not in holding state"}, status=400)

            buyer_user = virtual_wallet.buyer.user
            refund_amount = virtual_wallet.amount

            buyer_user.wallet_balance = (buyer_user.wallet_balance or Decimal("0.00")) + refund_amount
            buyer_user.save(update_fields=["wallet_balance"])

            virtual_wallet.status = "refunded"
            virtual_wallet.save(update_fields=["status", "updated_at"])

            task.status = "rejected"
            task.approval_status = "rejected"
            task.rejection_reason = reason
            task.reviewed_date = timezone.now()
            task.save(update_fields=["status", "approval_status", "rejection_reason", "reviewed_date"])

            seller_profile.unethical_reports = (seller_profile.unethical_reports or 0) + 1
            seller_profile.save(update_fields=["unethical_reports"])

            if seller_profile.unethical_reports >= 3:
                seller_profile.user.is_active = False
                seller_profile.user.save(update_fields=["is_active"])

            JobsHistory.objects.filter(task=task, seller=seller_profile).update(
                status="rejected",
                endDate=timezone.now(),
            )

            Transaction.objects.create(
                user=buyer_user,
                amount=refund_amount,
                type="refund",
                description=f"Refund for unethical task: {task.title}",
            )

    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller not found"}, status=404)
    except VirtualWallet.DoesNotExist:
        return JsonResponse({"error": "Virtual wallet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Task marked unethical and refunded to buyer"}, status=200)

@csrf_exempt
def SellerList(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    sellers = SellerProfile.objects.select_related("user").all()

    data = []
    for seller in sellers:
        data.append(
            {
                "id": seller.id,
                "Rating": seller.ratings,
                "AvgTime": float(seller.avgCompletionTime),
                "SuccessRate": float(seller.sucessRate),
            }
        )

    return JsonResponse({"sellers": data}, status=200)

@csrf_exempt
def getRatingIndexes(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    try:
        indexes = RatingIndexes.objects.first()
        if not indexes:
            return JsonResponse({"error": "Rating indexes not found"}, status=404)

        data = {
            "rate1": indexes.rate1,
            "rate2": indexes.rate2,
            "rate3": indexes.rate3,
            "rate4": indexes.rate4,
            "rate5": indexes.rate5,
        }

        return JsonResponse({"ratingIndexes": data}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    


@csrf_exempt
def assign_jobs_api(request):
    print("API HIT")

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body)

        sellers_data = body.get("sellers", [])
        jobs_data = body.get("jobs", {})
        task_id = body.get("taskId")

        task = BuyerTasks.objects.get(id=task_id)
        if JobsHistory.objects.filter(task=task).exists():
            return JsonResponse({"status": "Jobs already assigned for this task"}, status=200)

        # ✅ Step 1: Validate & normalize sellers
        valid_sellers = []

        for seller in sellers_data:
            try:
                seller_id = int(seller.get("id"))
                rating = int(seller.get("Rating"))
                valid_sellers.append({"id": seller_id, "Rating": rating})
            except:
                continue  # skip bad data

        # ✅ Step 2: group sellers by rating
        sellers_by_rating = {
            "rate1": [],
            "rate2": [],
            "rate3": [],
            "rate4": [],
            "rate5": []
        }

        for seller in valid_sellers:
            rating_key = f"rate{seller['Rating']}"
            if rating_key in sellers_by_rating:
                sellers_by_rating[rating_key].append(seller["id"])

        print("Sellers by rating:", sellers_by_rating)
        print("Jobs data:", jobs_data)

        with transaction.atomic():
            tracker, _ = RatingIndexes.objects.select_for_update().get_or_create(id=1)

            for rating_key in sellers_by_rating.keys():
                seller_ids = sellers_by_rating[rating_key]
                jobs_count = int(jobs_data.get(rating_key, 0))

                if not seller_ids or jobs_count == 0:
                    continue

                # ✅ Step 3: fetch ONLY valid sellers from DB
                db_sellers = list(
                    SellerProfile.objects.filter(id__in=seller_ids).values_list("id", flat=True)
                )

                if not db_sellers:
                    print(f"No valid sellers in DB for {rating_key}")
                    continue

                jobs_count = min(jobs_count, len(db_sellers))
                last_index = getattr(tracker, rating_key)

                assigned_ids, new_index = assign_jobs_round_robin(
                    db_sellers,
                    jobs_count,
                    last_index
                )
                assigned_ids = list(dict.fromkeys(assigned_ids))

                print("---- DEBUG ----")
                print("Rating:", rating_key)
                print("DB Sellers:", db_sellers)
                print("Jobs Count:", jobs_count)
                print("Assigned IDs:", assigned_ids)
                print("----------------")

                # ✅ Step 4: create jobs safely
                jobs_to_create = [
                    JobsHistory(
                        seller_id=seller_id,
                        task=task,
                        taskId=task_id
                    )
                    for seller_id in assigned_ids
                ]

                print("Creating jobs:", len(jobs_to_create))

                # 🔥 SAFE INSERT
                for job in jobs_to_create:
                    job.save()

                # update index
                setattr(tracker, rating_key, new_index)

            tracker.save()

        return JsonResponse({"status": "Jobs assigned successfully"}, status=200)

    except Exception as e:
        print("ERROR:", str(e))
        return JsonResponse({"error": str(e)}, status=500)








def connections_status(request):
    platforms = ['facebook', 'instagram', 'twitter', 'youtube']
    seller_id = request.GET.get("sellerId")
    result = {}

    for platform in platforms:
        try:
            account = SocialAccount.objects.get(platform=platform, sellerId=seller_id)
            token = account.access_token
            is_valid = False

            if platform == 'facebook':
                response = requests.get(
                    "https://graph.facebook.com/me",
                    params={"access_token": token}
                ).json()
                is_valid = "id" in response

            elif platform == 'instagram':
                response = requests.get(
                    "https://graph.facebook.com/me",
                    params={"access_token": token}
                ).json()
                is_valid = "id" in response

            elif platform == 'twitter':
                response = requests.get(
                    "https://api.twitter.com/2/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                ).json()
                is_valid = "data" in response

            elif platform == 'youtube':
                response = requests.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "snippet", "mine": "true"},
                    headers={"Authorization": f"Bearer {token}"}
                ).json()
                is_valid = "items" in response and len(response["items"]) > 0

            if is_valid:
                result[platform] = {
                    "connected": True,
                    "username": account.username,
                }
            else:
                print("InvalidToken")
                account.delete()
                result[platform] = {"connected": False, "username": None}

        except SocialAccount.DoesNotExist:
            result[platform] = {"connected": False, "username": None}

    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["DELETE"])
def disconnect_platform(request, platform):
    try:
        seller_id = request.GET.get("sellerId")
        account = SocialAccount.objects.get(platform=platform, sellerId=seller_id)
        account.delete()
        return JsonResponse({"message": f"{platform} disconnected"})
    except SocialAccount.DoesNotExist:
        return JsonResponse({"error": "Not connected"}, status=404)

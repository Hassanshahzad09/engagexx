import json
import base64
import hashlib
import uuid
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import requests
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Count, Sum, Q, F, Max, Case, When, Value, IntegerField
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from BackEnd.utils import assign_jobs_round_robin, get_phash
from .models import BuyerProfile, BuyerTasks, EasypaisaTransaction, RatingIndexes, SellerBehaviorLog, SellerProfile, SellerWithdrawalRequest, User,JobsHistory,JobRatingQuota,TestAccount,SocialAccount,SocialAuth,Transaction,VirtualWallet
from .seller_rating import calculate_seller_rating, rating_dataset_summary, update_seller_rating
from detectfraud.image_analysis import analyze_proof_image_quality
from django.db import transaction
from django.views.decorators.http import require_http_methods

from django.db.models import F, Max

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
    ip_address = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    device_source = f"{ip_address or ''}|{user_agent}"
    device_id = hashlib.sha256(device_source.encode("utf-8")).hexdigest()

    return SellerBehaviorLog.objects.create(
        job=job,
        task_id=str(job.task_id or job.task.id),
        seller_id=str(job.seller_id or job.seller.id),
        ip_address=ip_address,
        device_id=device_id,
        user_agent=user_agent,
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
    # EasyPaisa integration is disabled during local testing.
    # default_payment_method = "easypaisa" if request.path.endswith("/easypaisa-pay/") else "manual"
    default_payment_method = "manual"
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

    # EasyPaisa integration is disabled during local testing.
    # if str(payment_method).lower() == "easypaisa":
    if False and str(payment_method).lower() == "easypaisa":
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
    ).select_related("buyer__user").prefetch_related("jobs").distinct()

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
        .filter(status="submitted", proofStatus="pending")
        .filter(Q(proofUrl__gt="") | Q(proofImage__isnull=False))
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
            "proofImageUrl": request.build_absolute_uri(job.proofImage.url) if job.proofImage else "",
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
    """
    Kept for old code compatibility only.
    New flow does NOT bulk-create JobsHistory rows.
    Jobs are created lazily from JobRatingQuota when a seller requests tasks.
    """
    return 0


def _normalize_platform_name(platform):
    """
    Normalize platform names so Instagram/insta and Twitter/X/x match correctly.
    """
    value = (platform or "").strip().lower()

    if value in ["instagram", "insta"]:
        return "instagram"

    if value in ["twitter", "x", "twitter/x", "x.com"]:
        return "twitter"

    if value in ["facebook", "fb"]:
        return "facebook"

    if value in ["youtube", "yt"]:
        return "youtube"

    return value


def get_connected_platforms_for_seller(seller_profile):
    """
    Returns platforms connected by THIS exact seller account only.

    IMPORTANT:
    SocialAccount.sellerId stores the seller user's User.id, not SellerProfile.id.
    Never check both SellerProfile.id and User.id here, because IDs can overlap
    and Seller 1's connection can wrongly appear on Seller 2.
    """
    platforms = SocialAccount.objects.filter(
        sellerId=seller_profile.user_id
    ).values_list("platform", flat=True)

    return {
        _normalize_platform_name(platform)
        for platform in platforms
        if platform
    }


def _get_seller_connected_platforms(seller_profile):
    """
    Get platforms connected to this exact seller account only.
    This is a helper alias used by the seller priority checks.
    """
    return get_connected_platforms_for_seller(seller_profile)


def _seller_has_connected_platform(seller_profile, task_platform):
    """
    Check if seller has connected the platform required by the task.
    """
    connected_platforms = _get_seller_connected_platforms(seller_profile)
    required_platform = _normalize_platform_name(task_platform)

    return required_platform in connected_platforms


def _seller_pending_buyer_ids(seller_profile):
    """
    Buyer IDs currently blocked for this seller.

    Seller may receive tasks from different buyers.

    But for the same buyer, block new assignment while seller has:
    - pending/assigned task not submitted yet
    - submitted proof still waiting for admin review

    After admin approves/rejects, that buyer becomes available again.
    """
    return set(
        JobsHistory.objects.filter(
            seller=seller_profile,
            task__approval_status="approved",
            task__virtual_wallet__status="holding",
        ).filter(
            Q(status="pending") |
            Q(status="assigned") |
            Q(status="submitted", proofStatus="pending")
        ).values_list("task__buyer_id", flat=True)
    )


def _seller_has_unsubmitted_job_from_same_buyer(seller_profile, buyer_id):
    """
    Buyer-level lock.

    A seller can hold tasks from different buyers at the same time.

    But if the seller already has an open or unreviewed job from Buyer 1,
    then he should not receive another Buyer 1 job until that first Buyer 1
    job is reviewed.

    Blocking statuses:
    - pending / assigned: seller has task but has not submitted proof yet
    - submitted + proof pending: seller submitted proof but admin has not reviewed yet

    After admin approves/rejects, the seller can receive another task from
    the same buyer again.
    """
    return JobsHistory.objects.filter(
        seller=seller_profile,
        task__buyer_id=buyer_id,
        task__approval_status="approved",
        task__virtual_wallet__status="holding",
    ).filter(
        Q(status="pending") |
        Q(status="assigned") |
        Q(status="submitted", proofStatus="pending")
    ).exists()


def _seller_has_pending_review_for_same_task(seller_profile, task):
    """
    Task-level lock.

    Seller cannot receive the SAME BuyerTask again while his previous proof
    for that same BuyerTask is waiting for admin approval/rejection.

    This mainly protects repeatable comment/view/watch tasks.
    """
    return JobsHistory.objects.filter(
        seller=seller_profile,
        task=task,
        status="submitted",
        proofStatus="pending",
    ).exists()


def _seller_rejected_task_twice(seller_profile, task):
    """
    If seller has already rejected/invalid proof twice for the same buyer task,
    do not assign this same task to him again.
    """
    return JobsHistory.objects.filter(
        seller=seller_profile,
        task=task,
    ).filter(
        Q(status="rejected") | Q(proofStatus="invalid")
    ).count() >= 2


def _serialize_seller_job(job):
    task = job.task
    goal = float(task.goal or 0)
    progressed = float(task.progressed or 0)
    price = float(task.pricePerAction or 0)
    remaining = goal - progressed

    return {
        "id": task.id,
        "jobId": job.id,
        "title": task.title,
        "platform": (task.platform or "").strip().title(),
        "type": (task.taskType or "").title(),
        "url": task.url,
        "price": price,
        "remaining": max(remaining, 0),
        "total": goal,
        "timeEstimate": "2 min",
        "difficulty": "Easy",
        "status": "assigned" if job.status == "pending" else job.status,
    }


def _seller_priority_tuple(seller_profile):
    """
    Lower tuple = higher seller priority.

    Priority logic:
    1. Sellers who never received a task get first chance.
    2. Then sellers with the oldest last assignment get priority.
    3. Then sellers who waited longer in queue get priority.
    4. Higher trust score wins only when fairness is equal.
    """

    now = timezone.now()

    if seller_profile.last_assigned_at is None:
        last_assigned_rank = 0
        last_assigned_time = timezone.datetime.min.replace(
            tzinfo=timezone.get_current_timezone()
        )
    else:
        last_assigned_rank = 1
        last_assigned_time = seller_profile.last_assigned_at

    queue_time = seller_profile.queue_joined_at or now

    try:
        trust_score = Decimal(seller_profile.trust_score or 0)
    except Exception:
        trust_score = Decimal("0")

    return (
        last_assigned_rank,
        last_assigned_time,
        queue_time,
        -trust_score,
        seller_profile.id,
    )


def _normalize_task_type(task_type):
    """
    Normalize task type names safely.

    Examples:
    - "Followers" -> "followers"
    - "watch_time" -> "watch time"
    - "youtube-like" -> "youtube like"
    """
    return (task_type or "").strip().lower().replace("-", " ").replace("_", " ")


def _is_one_time_task(task):
    """
    These task types should be performed only ONCE by the same seller
    for the same BuyerTask.

    Reason:
    - Same seller cannot like the same post twice.
    - Same seller cannot follow the same account twice.
    - Same seller cannot subscribe to the same channel twice.

    NOTE:
    Comments and views/watch tasks are intentionally NOT included here.
    Comments/views/watch may be assigned again to the same seller only after
    admin approves/rejects the seller's previous proof for that same job.
    """
    task_type = _normalize_task_type(task.taskType)

    one_time_keywords = [
        "like",
        "likes",
        "follow",
        "follows",
        "follower",
        "followers",
        "subscribe",
        "subscriber",
        "subscribers",
    ]

    return any(keyword == task_type or keyword in task_type for keyword in one_time_keywords)


def _seller_already_attempted_same_task(seller_profile, task):
    """
    For like/follow/subscribe tasks:
    if this seller already received this BuyerTask once, never assign
    the same BuyerTask to the same seller again.

    For comment/view/watch tasks:
    return False here, because those can repeat after admin review.
    """
    if not _is_one_time_task(task):
        return False

    return JobsHistory.objects.filter(
        seller=seller_profile,
        task=task,
    ).exists()


def _seller_is_eligible_for_quota(seller_profile, quota):
    """
    Check if this seller is eligible for this quota.

    Final rules:
    - rating must match
    - seller must be online
    - platform must be connected by this exact seller
    - seller cannot have another open/unreviewed task from the same buyer
    - seller cannot get same BuyerTask while previous proof is under review
    - like/follow/subscribe tasks can be assigned only once per seller
    - comment/view/watch tasks can repeat only after admin review
    - rejected twice on same task means skip that task
    """
    task = quota.task

    if seller_profile.ratings != quota.rating:
        return False

    if not getattr(seller_profile, "is_online", False):
        return False

    if not _seller_has_connected_platform(seller_profile, task.platform):
        return False

    # One open/unreviewed task from same buyer at a time.
    if _seller_has_unsubmitted_job_from_same_buyer(seller_profile, task.buyer_id):
        return False

    # Same BuyerTask cannot be assigned again until admin reviews previous proof.
    if _seller_has_pending_review_for_same_task(seller_profile, task):
        return False

    # Like/follow/subscribe tasks are one-time per seller per BuyerTask.
    # Comment/view/watch tasks are repeatable after admin review.
    if _seller_already_attempted_same_task(seller_profile, task):
        return False

    # If seller rejected twice on same task, skip this task.
    if _seller_rejected_task_twice(seller_profile, task):
        return False

    return True


def _get_highest_priority_seller_for_quota(quota):
    """
    Find the seller who deserves this quota the most right now.

    This prevents the fastest-refreshing seller from taking all jobs.
    """
    possible_sellers = (
        SellerProfile.objects
        .filter(
            ratings=quota.rating,
            is_online=True,
        )
        .select_related("user")
    )

    eligible_sellers = []

    for seller in possible_sellers:
        if _seller_is_eligible_for_quota(seller, quota):
            eligible_sellers.append(seller)

    if not eligible_sellers:
        return None

    eligible_sellers.sort(key=_seller_priority_tuple)
    return eligible_sellers[0]


def _get_next_quota_for_seller(seller_profile, connected_platforms, blocked_buyer_ids=None):
    """
    Pick next quota fairly for this seller.

    Final assignment rules:
    - Match seller rating.
    - Match this exact seller's connected OAuth platforms.
    - Seller can receive jobs from different buyers.
    - Seller cannot receive another unsubmitted/open job from same buyer.
    - Seller cannot receive same BuyerTask again while previous proof
      for same BuyerTask is pending admin review.
    - For like/follow/subscribe tasks, seller cannot receive
      the same BuyerTask again ever.
    - Comment/view/watch tasks can repeat only after admin review.
    - Seller rejected twice on same BuyerTask will not receive it again.
    - New/idle sellers get priority over recently assigned sellers.
    - Fast-refresh seller cannot steal all jobs.
    """

    normalized_platforms = {
        _normalize_platform_name(platform)
        for platform in connected_platforms
        if platform
    }

    if not normalized_platforms:
        return None

    blocked_buyer_ids = set(blocked_buyer_ids or [])

    candidate_quotas = (
        JobRatingQuota.objects
        .select_for_update()
        .select_related("task", "task__buyer")
        .filter(
            rating=seller_profile.ratings,
            task__approval_status="approved",
            task__status__in=["active", "in_progress"],
            task__virtual_wallet__status="holding",
            total_quota__gt=F("assigned_count") + F("completed_count"),
        )
        .annotate(last_served_at=Max("jobs__startDate"))
    )

    valid_quotas = []

    for quota in candidate_quotas:
        task = quota.task
        task_platform = _normalize_platform_name(task.platform)

        # Seller must have connected account for this platform.
        if task_platform not in normalized_platforms:
            continue

        # One open/unreviewed task per buyer at a time.
        if task.buyer_id in blocked_buyer_ids:
            continue

        # Same BuyerTask pending review rule.
        if _seller_has_pending_review_for_same_task(seller_profile, task):
            continue

        # Like/follow/subscribe are one-time per seller per BuyerTask.
        # Comment/view/watch can repeat after admin review.
        if _seller_already_attempted_same_task(seller_profile, task):
            continue

        # Rejected twice rule.
        if _seller_rejected_task_twice(seller_profile, task):
            continue

        # Priority rule:
        # Even if this seller requested first, only assign this quota
        # if this seller is currently the highest priority eligible seller.
        highest_priority_seller = _get_highest_priority_seller_for_quota(quota)

        if not highest_priority_seller:
            continue

        if highest_priority_seller.id != seller_profile.id:
            continue

        valid_quotas.append(quota)

    if not valid_quotas:
        return None

    def quota_priority(quota):
        """
        Lower tuple = higher quota priority.

        Priority:
        1. Quota with lower served count first.
        2. Never-served quota first.
        3. Least recently served quota next.
        4. Newer task gets slight priority if everything else is equal.
        """
        total_served = (quota.assigned_count or 0) + (quota.completed_count or 0)

        if quota.last_served_at is None:
            last_served_rank = 0
            last_served_time = timezone.datetime.min.replace(
                tzinfo=timezone.get_current_timezone()
            )
        else:
            last_served_rank = 1
            last_served_time = quota.last_served_at

        created_time = quota.created_at or timezone.now()

        return (
            total_served,
            last_served_rank,
            last_served_time,
            -created_time.timestamp(),
            quota.id,
        )

    valid_quotas.sort(key=quota_priority)

    return valid_quotas[0]


def _create_next_job_for_seller(seller_profile, connected_platforms, blocked_buyer_ids=None):
    """
    Lazy assignment:
    - creates only ONE JobsHistory row per call
    - does not wait for admin approval of submitted proofs globally
    - blocks only buyers where seller already has an open/unreviewed job
    - blocks the same BuyerTask while seller's previous proof is pending admin review
    - respects seller priority so new/idle sellers get fair opportunity
    """
    if not connected_platforms:
        return None

    quota = _get_next_quota_for_seller(
        seller_profile,
        connected_platforms,
        blocked_buyer_ids=blocked_buyer_ids,
    )

    if not quota:
        seller_profile.is_available = True
        seller_profile.save(update_fields=["is_available"])
        return None

    job = JobsHistory.objects.create(
        seller=seller_profile,
        task=quota.task,
        quota=quota,
        taskId=quota.task.id,
        status="pending",
        proofStatus="pending",
        auditStatus="not_checked",
        priceEarned=quota.task.pricePerAction or Decimal("0.00"),
        lock_expires_at=timezone.now() + timedelta(minutes=30),
    )

    quota.assigned_count += 1
    quota.save(update_fields=["assigned_count", "updated_at"])

    seller_profile.is_online = True
    # Boolean availability is no longer a hard global lock; seller may still get other buyers' jobs.
    seller_profile.is_available = True
    seller_profile.last_assigned_at = timezone.now()
    seller_profile.queue_joined_at = timezone.now()
    seller_profile.save(update_fields=["is_online", "is_available", "last_assigned_at", "queue_joined_at"])

    return job


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

    with transaction.atomic():
        seller_profile = SellerProfile.objects.get(id=seller_profile.id)

        # Show only pending/unsubmitted assigned jobs to the seller.
        # Submitted proofs are with admin, but they no longer block jobs from other buyers.
        active_jobs = list(
            JobsHistory.objects
            .filter(
                seller=seller_profile,
                status="pending",
                task__approval_status="approved",
                task__virtual_wallet__status="holding",
            )
            .select_related("task", "task__buyer")
            .order_by("startDate", "id")
        )

        # Block another assignment from the same buyer if this seller already has
        # either an unsubmitted job OR a submitted proof still pending admin review.
        blocked_buyer_ids = _seller_pending_buyer_ids(seller_profile)

        now = timezone.now()
        was_offline = not getattr(seller_profile, "is_online", False)

        seller_profile.is_online = True
        seller_profile.is_available = True

        # If seller just came online or has no queue time, start a fresh queue wait time.
        if was_offline or seller_profile.queue_joined_at is None:
            seller_profile.queue_joined_at = now

        seller_profile.save(update_fields=["is_online", "is_available", "queue_joined_at"])

        # Create ONE more task per poll/call, but only from a buyer that is not already open/unreviewed.
        # This lets a seller receive tasks from multiple buyers without waiting for admin review,
        # while still preventing the same seller from repeatedly taking the same buyer/task.
        new_job = _create_next_job_for_seller(
            seller_profile,
            connected_platforms,
            blocked_buyer_ids=blocked_buyer_ids,
        )
        if new_job:
            active_jobs.append(new_job)

    data = []
    for job in active_jobs:
        if not job or job.status != "pending":
            continue

        platform = _normalize_platform_name(job.task.platform)
        if platform not in connected_platforms:
            continue

        data.append(_serialize_seller_job(job))

    return JsonResponse({"tasks": data}, status=200)


def calculate_file_sha256(uploaded_file):
    sha256 = hashlib.sha256()

    for chunk in uploaded_file.chunks():
        sha256.update(chunk)

    uploaded_file.seek(0)

    return sha256.hexdigest()


def calculate_file_phash(uploaded_file):
    if not uploaded_file:
        return ""
    try:
        uploaded_file.seek(0)
        phash_value = get_phash(uploaded_file)
        uploaded_file.seek(0)
        return phash_value or ""
    except Exception:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return ""


def approve_seller_job(job, task, seller_profile, virtual_wallet, payment_amount):
    if job.status == "completed" and job.proofStatus == "valid":
        return update_seller_rating(seller_profile)

    if virtual_wallet.status != "holding":
        raise ValueError("Task payment is not available")

    if payment_amount <= 0:
        raise ValueError("Task price is not valid")

    if virtual_wallet.amount < payment_amount:
        raise ValueError("Task payment wallet does not have enough balance")

    seller_user = seller_profile.user
    seller_user.wallet_balance = (seller_user.wallet_balance or Decimal("0.00")) + payment_amount
    seller_user.save(update_fields=["wallet_balance"])

    seller_profile.totalEarnings = (seller_profile.totalEarnings or Decimal("0.00")) + payment_amount
    seller_profile.save(update_fields=["totalEarnings"])

    job.proofStatus = "valid"
    job.proofReviewedDate = timezone.now()
    job.status = "completed"
    job.progress = Decimal("1.00")
    job.priceEarned = payment_amount
    job.endDate = timezone.now()
    job.save(update_fields=[
        "proofStatus",
        "proofReviewedDate",
        "status",
        "progress",
        "priceEarned",
        "endDate",
    ])

    if job.quota_id:
        quota = JobRatingQuota.objects.select_for_update().get(id=job.quota_id)
        quota.assigned_count = max(0, quota.assigned_count - 1)
        quota.completed_count += 1
        quota.save(update_fields=["assigned_count", "completed_count", "updated_at"])

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
        description=f"Seller job approved: {task.title}",
    )

    seller_profile.is_available = True
    seller_profile.queue_joined_at = timezone.now()
    seller_profile.save(update_fields=["is_available", "queue_joined_at"])

    return update_seller_rating(seller_profile)


@csrf_exempt
def submit_task(request):
    proof_image = None
    content_type = request.content_type or ""

    if content_type.startswith("multipart/form-data"):
        data = request.POST
        proof_image = request.FILES.get("proofImage")
    elif content_type.startswith("application/json"):
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
    else:
        return JsonResponse({"error": "Unsupported content type"}, status=400)

    task_id = data.get("taskId")
    seller_id = data.get("sellerId")
    proof_url = data.get("proofUrl", "")
    notes = data.get("notes", "")
    time_spent_seconds = data.get("timeSpent", 0)

    if not task_id or not seller_id:
        return JsonResponse({"error": "taskId and sellerId are required"}, status=400)

    try:
        time_spent_seconds = Decimal(str(time_spent_seconds))
    except (InvalidOperation, TypeError):
        time_spent_seconds = Decimal("0.00")

    if time_spent_seconds < 0:
        time_spent_seconds = Decimal("0.00")

    time_spent = (time_spent_seconds / Decimal("3600.00")).quantize(Decimal("0.0001"))
    proof_sha256 = calculate_file_sha256(proof_image) if proof_image else ""
    proof_phash = calculate_file_phash(proof_image) if proof_image else ""
    proof_image_analysis = analyze_proof_image_quality(proof_image) if proof_image else {}

    try:
        with transaction.atomic():
            seller_profile = get_seller_profile_from_user_id(seller_id)
            task = BuyerTasks.objects.select_for_update().get(id=task_id)
            virtual_wallet = VirtualWallet.objects.select_for_update().get(task=task)
            job = (
                JobsHistory.objects
                .select_for_update()
                .filter(
                    task=task,
                    seller=seller_profile,
                    status="pending",
                )
                .order_by("startDate")
                .first()
            )

            if not job:
                return JsonResponse(
                    {"error": "This task is not assigned to this seller"},
                    status=400
                )

            platform = (task.platform or "").strip().lower()
            is_youtube_auto = platform == "youtube" and proof_url == "watched_70_percent"

            if not is_youtube_auto and not proof_url and not proof_image:
                return JsonResponse({"error": "Proof URL or screenshot image is required"}, status=400)

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

            seller_profile.avgCompletionTime = time_spent
            seller_profile.save(update_fields=["avgCompletionTime"])

            job.proofUrl = proof_url
            job.proofImage = proof_image
            job.proofSha256 = proof_sha256
            job.proofPhash = proof_phash
            job.notes = notes
            job.completionTime = time_spent
            job.endDate = timezone.now()

            if is_youtube_auto:
                job.save(update_fields=[
                    "proofUrl",
                    "proofImage",
                    "proofSha256",
                    "proofPhash",
                    "notes",
                    "completionTime",
                    "endDate",
                ])

                behavior_log = create_seller_behavior_log(request, job)
                rating_data = approve_seller_job(job, task, seller_profile, virtual_wallet, payment_amount)

                return JsonResponse({
                    "message": "YouTube task auto-approved after 70% watch",
                    "jobStatus": job.status,
                    "proofStatus": job.proofStatus,
                    "behaviorLogId": behavior_log.id,
                    "sellerRating": rating_data,
                    "proofImageAnalysis": proof_image_analysis,
                }, status=200)

            job.status = "submitted"
            job.proofStatus = "pending"
            job.proofReviewedDate = None
            job.save(update_fields=[
                "proofUrl",
                "proofImage",
                "proofSha256",
                "proofPhash",
                "proofStatus",
                "proofReviewedDate",
                "notes",
                "completionTime",
                "status",
                "endDate",
            ])

            # Seller has submitted proof, so he is free for new assignment.
            # Admin review will happen later, but it should not globally block the seller.
            seller_profile.is_available = True
            seller_profile.queue_joined_at = timezone.now()
            seller_profile.save(update_fields=["is_available", "queue_joined_at"])

            behavior_log = create_seller_behavior_log(request, job)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)
    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except VirtualWallet.DoesNotExist:
        return JsonResponse({"error": "Task payment wallet not found"}, status=404)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)

    return JsonResponse({
        "message": "Task submitted successfully and sent to admin for approval",
        "jobStatus": job.status,
        "proofStatus": job.proofStatus,
        "behaviorLogId": behavior_log.id,
        "proofImageAnalysis": proof_image_analysis,
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
            job = (
                JobsHistory.objects
                .select_for_update()
                .select_related("seller", "seller__user", "task")
                .get(id=job_id)
            )
            task = BuyerTasks.objects.select_for_update().get(id=job.task.id)
            virtual_wallet = VirtualWallet.objects.select_for_update().get(task=task)
            payment_amount = task.pricePerAction or Decimal("0.00")

            if proof_status == "valid":
                rating_data = approve_seller_job(job, task, job.seller, virtual_wallet, payment_amount)
                message = "Seller proof approved and payment released"
            else:
                job.proofStatus = "invalid"
                job.proofReviewedDate = timezone.now()
                job.status = "rejected"
                job.save(update_fields=["proofStatus", "proofReviewedDate", "status"])

                if job.quota_id:
                    quota = JobRatingQuota.objects.select_for_update().get(id=job.quota_id)
                    quota.assigned_count = max(0, quota.assigned_count - 1)
                    quota.rejected_count += 1
                    quota.save(update_fields=["assigned_count", "rejected_count", "updated_at"])

                job.seller.is_available = True
                job.seller.queue_joined_at = timezone.now()
                job.seller.save(update_fields=["is_available", "queue_joined_at"])

                rating_data = update_seller_rating(job.seller)
                message = "Seller proof rejected"
    except JobsHistory.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)
    except VirtualWallet.DoesNotExist:
        return JsonResponse({"error": "Task payment wallet not found"}, status=404)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)

    return JsonResponse({
        "message": message,
        "jobId": job.id,
        "jobStatus": job.status,
        "proofStatus": job.proofStatus,
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
    return JsonResponse({"message": "Task approved successfully and amount deducted from buyer wallet","goal": task.goal}, status=200)


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
    """
    Called after admin approves a BuyerTasks row and ML returns rating-wise allocation.
    This endpoint now creates JobRatingQuota rows only.
    It does NOT directly assign JobsHistory rows to sellers.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body)
        jobs_data = body.get("jobs", {})
        task_id = body.get("taskId")

        if not task_id:
            return JsonResponse({"error": "taskId is required"}, status=400)

        task = BuyerTasks.objects.get(id=task_id)

        with transaction.atomic():
            task = BuyerTasks.objects.select_for_update().get(id=task_id)

            if JobRatingQuota.objects.filter(task=task).exists():
                return JsonResponse({"status": "Quota already created for this task"}, status=200)

            total_created_quota = 0

            for rating in range(1, 6):
                rating_key = f"rate{rating}"
                try:
                    quota_count = int(float(jobs_data.get(rating_key, 0) or 0))
                except (TypeError, ValueError):
                    quota_count = 0

                if quota_count <= 0:
                    continue

                JobRatingQuota.objects.create(
                    task=task,
                    rating=rating,
                    total_quota=quota_count,
                    assigned_count=0,
                    completed_count=0,
                    rejected_count=0,
                )
                total_created_quota += quota_count

            task.status = "active"
            task.save(update_fields=["status"])

        return JsonResponse({
            "status": "Job quotas created successfully",
            "taskId": task.id,
            "total_created_quota": total_created_quota,
        }, status=200)

    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Buyer task not found"}, status=404)
    except Exception as e:
        print("ASSIGN JOB QUOTA ERROR:", str(e))
        return JsonResponse({"error": str(e)}, status=500)



def connections_status(request):
    platforms = ['facebook', 'instagram', 'twitter', 'youtube']
    seller_id = request.GET.get("sellerId")

    if not seller_id:
        return JsonResponse({"error": "sellerId is required"}, status=400)

    try:
        seller = get_seller_profile_from_user_id(seller_id)
        canonical_seller_user_id = seller.user_id
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)

    result = {}
    for platform in platforms:
        account = (
            SocialAccount.objects
            .filter(platform=platform, sellerId=canonical_seller_user_id)
            .order_by("-id")
            .first()
        )

        result[platform] = {
            "connected": bool(account),
            "username": account.username if account else None,
        }

    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["DELETE"])
def disconnect_platform(request, platform):
    try:
        seller_id = request.GET.get("sellerId")
        seller = get_seller_profile_from_user_id(seller_id)
        account = SocialAccount.objects.get(platform=platform, sellerId=seller.user_id)
        account.delete()
        return JsonResponse({"message": f"{platform} disconnected"})
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)
    except SocialAccount.DoesNotExist:
        return JsonResponse({"error": "Not connected"}, status=404)












# detectfraud/views.py — add this view

from detectfraud.models import FraudAnalysisResult
from django.db.models import Count, Avg, Q

@csrf_exempt
def fraud_dashboard_api(request):
    """
    Returns all fraud analysis data for admin dashboard.
    GET /fraud/dashboard/
    """
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    # ── Filters from query params ──────────────────────────────
    risk_filter    = request.GET.get("risk_level", "")
    prediction     = request.GET.get("prediction", "")
    seller_id      = request.GET.get("seller_id", "")
    task_id        = request.GET.get("task_id", "")
    limit          = int(request.GET.get("limit", 50))

    qs = FraudAnalysisResult.objects.select_related(
        "seller__user", "task", "job"
    ).order_by("-analyzed_at")

    if risk_filter:
        qs = qs.filter(risk_level=risk_filter.upper())
    if prediction:
        qs = qs.filter(prediction=prediction.upper())
    if seller_id:
        qs = qs.filter(seller__user_id=seller_id)
    if task_id:
        qs = qs.filter(task_id=task_id)

    qs = qs[:limit]

    # ── Stats summary ──────────────────────────────────────────
    all_results = FraudAnalysisResult.objects.all()
    total       = all_results.count()
    fraud_count = all_results.filter(is_fraud=True).count()
    legit_count = total - fraud_count
    avg_prob    = all_results.aggregate(avg=Avg("fraud_probability"))["avg"] or 0

    risk_breakdown = {
        "LOW":      all_results.filter(risk_level="LOW").count(),
        "MEDIUM":   all_results.filter(risk_level="MEDIUM").count(),
        "HIGH":     all_results.filter(risk_level="HIGH").count(),
        "CRITICAL": all_results.filter(risk_level="CRITICAL").count(),
    }

    # ── Serialize results ──────────────────────────────────────
    results = []
    for r in qs:
        results.append({
            "id":               r.id,
            "job_id":           r.job_id,
            "analyzed_at":      r.analyzed_at.isoformat(),

            # Seller
            "seller_id":        r.seller.user_id,
            "seller_name":      r.seller.user.get_full_name() or r.seller.user.username,
            "seller_type":      r.seller_type,
            "seller_age_days":  r.seller_age_days,
            "seller_trust":     r.seller_trust_score,

            # Task
            "task_id":          r.task_id,
            "task_title":       r.task.title,
            "task_platform":    r.task.platform,
            "task_type":        r.task.taskType,

            # Layer 1
            "is_duplicate_screenshot": r.is_duplicate_screenshot,

            # Layer 2 — Timing
            "completion_duration":   r.completion_duration,
            "timing_risk_score":     r.timing_risk_score,
            "timing_classification": r.timing_classification,

            # Layer 2 — Behavior
            "std_dev":                  r.std_dev,
            "z_score":                  r.z_score,
            "timing_consistency_score": r.timing_consistency_score,
            "validity_score":           r.validity_score,
            "repetitive_behavior_flag": r.repetitive_behavior_flag,
            "overall_behavior_label":   r.overall_behavior_label,

            # Layer 2 — Device / IP
            "ip_address":           r.ip_address,
            "device_id":            r.device_id,
            "device_seller_count":  r.device_seller_count,
            "ip_seller_count":      r.ip_seller_count,
            "device_sharing_score": r.device_sharing_score,
            "ip_reuse_score":       r.ip_reuse_score,
            "device_sharing_label": r.device_sharing_label,
            "ip_reuse_label":       r.ip_reuse_label,

            # Layer 3 — ML
            "prediction":        r.prediction,
            "fraud_probability": r.fraud_probability,
            "risk_level":        r.risk_level,
            "is_fraud":          r.is_fraud,
            # fraud_reasons are shown whenever suspicious signals exist, not only at 100% probability.
            "fraud_reasons":     r.fraud_reasons or r.suspicious_signals or [],
            "suspicious_signals": r.suspicious_signals or r.fraud_reasons or [],
            "human_summary": (
                f"{r.prediction.title()} with {round(float(r.fraud_probability or 0), 2)}% probability ({r.risk_level} risk). "
                f"Device sellers: {r.device_seller_count}, IP sellers: {r.ip_seller_count}."
            ),
            "admin_recommendation": (
                "Reject or manually verify before approval." if float(r.fraud_probability or 0) >= 70 else
                "Manually check the proof carefully." if float(r.fraud_probability or 0) >= 40 else
                "Looks safe, but still verify the screenshot before approval."
            ),
        })

    return JsonResponse({
        "summary": {
            "total":       total,
            "fraud":       fraud_count,
            "legitimate":  legit_count,
            "avg_probability": round(avg_prob, 2),
            "risk_breakdown":  risk_breakdown,
        },
        "results": results,
    })
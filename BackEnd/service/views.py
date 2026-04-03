import json
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from .models import User, BuyerProfile, SellerProfile
from django.contrib.auth.hashers import check_password

@csrf_exempt
def signup(request):

    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    # Extract fields
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("userEmail")
    password = data.get("userPass")
    username = data.get("userName")
    user_role = data.get("user_Type")

    # Validation checks

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

    # Check duplicate email
    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already exists"}, status=400)

    # Check duplicate username
    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username already exists"}, status=400)

    
    # Create user
    
    user = User.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        username=username,
        role=user_role,
        password=make_password(password),  # hashed password
        date_joined=timezone.now()
    )

   
    # Create profile
   
    if user_role == "buyer":
        BuyerProfile.objects.create(user=user)

    elif user_role == "seller":
        SellerProfile.objects.create(user=user)

    return JsonResponse({
        "message": f"Signup successful for role: {user_role}",
        "username": user.username,
        "email": user.email
    }, status=201)

@csrf_exempt
def login(request):

    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    # Extract fields
    email = data.get("userEmail")
    password = data.get("userPass")
    userType = data.get("user_Type")

    # Validation
    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    if not password:
        return JsonResponse({"error": "Password is required"}, status=400)

    # Check if user exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({"error": "Invalid email or password"}, status=400)

    # Check password
    if not check_password(password, user.password):
        return JsonResponse({"error": "Invalid email or password"}, status=400)

    # Optional: check user role/profile
    role = user.role
    if role != userType:
        return JsonResponse({"error": "User role mismatch"}, status=400)

    return JsonResponse({
        "message": "Login successful",
        "firstName": user.first_name,
        "email": user.email,
        "userId":user.id
    }, status=200)


    
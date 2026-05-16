# users/views.py

from django.shortcuts import redirect
from django.conf import settings
import urllib.parse
import base64
import hashlib
import os



def connect_facebook(request):
    base_url = "https://www.facebook.com/v18.0/dialog/oauth"

    params = {
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "scope": "public_profile",
        "response_type": "code",
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)


import requests
from django.shortcuts import redirect
from django.conf import settings
from service.models import SocialAccount,User,BuyerProfile,SellerProfile,SocialAuth

def facebook_callback(request):
    code = request.GET.get("code")

    # 1. Exchange code for token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"

    token_response = requests.get(token_url, params={
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "client_secret": settings.FACEBOOK_CLIENT_SECRET,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "code": code,
    })

    access_token = token_response.json().get("access_token")

    # 2. Get user info
    user_info = requests.get(
        "https://graph.facebook.com/me",
        params={
            "fields": "id,name",
            "access_token": access_token
        }
    ).json()

    # 3. Save data
    print(user_info.get("name"),user_info.get("id"))
    SocialAccount.objects.update_or_create(
        #user=request.user,
        platform="facebook",
        defaults={
            "username": user_info.get("name"),
            "social_id": user_info.get("id"),
            "access_token": access_token
        }
    )

    return redirect("http://localhost:3000/connect-facebook")







def connect_instagram(request):
    base_url = "https://www.facebook.com/v18.0/dialog/oauth"
    params = {
    "client_id": settings.INSTAGRAM_CLIENT_ID,
    "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
    "scope": "pages_show_list,pages_read_engagement,instagram_basic",
    "response_type": "code",
    "auth_type": "rerequest",   # 🔥 IMPORTANT
}

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    print("INSTAGRAM URL:", url)
    return redirect(url)

def instagram_callback(request):
    code = request.GET.get("code")

    if not code:
        print("❌ No code received")
        return redirect("http://localhost:3000/error?msg=no_code")

    # 🔹 Exchange code for access token
    token_response = requests.get(
        "https://graph.facebook.com/v18.0/oauth/access_token",
        params={
            "client_id": settings.INSTAGRAM_CLIENT_ID,
            "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
            "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
            "code": code,
        }
    ).json()

    print("🔹 TOKEN RESPONSE:", token_response)

    access_token = token_response.get("access_token")

    if not access_token:
        print("❌ No access token")
        return redirect("http://localhost:3000/error?msg=no_token")

    # 🔹 DEBUG TOKEN → get granular scopes
    debug_data = requests.get(
        "https://graph.facebook.com/debug_token",
        params={
            "input_token": access_token,
            "access_token": access_token
        }
    ).json()

    print("🔹 DEBUG DATA:", debug_data)

    granular_scopes = debug_data.get("data", {}).get("granular_scopes", [])

    # 🔹 Extract page IDs
    page_ids = []
    for scope in granular_scopes:
        if scope.get("scope") == "pages_show_list":
            page_ids.extend(scope.get("target_ids", []))

    print("🔹 PAGE IDS:", page_ids)

    if not page_ids:
        print("❌ No page IDs found")
        return redirect("http://localhost:3000/error?msg=no_pages")

    # 🔹 Loop through pages
    for page_id in page_ids:
        print(f"➡️ Checking Page ID: {page_id}")

        page_data = requests.get(
            f"https://graph.facebook.com/v18.0/{page_id}",
            params={
                "fields": "id,name,access_token,instagram_business_account",
                "access_token": access_token
            }
        ).json()

        print("🔹 PAGE DATA:", page_data)

        page_token = page_data.get("access_token")
        ig_account = page_data.get("instagram_business_account")

        if not page_token:
            print("❌ No page token")
            continue

        if ig_account:
            ig_id = ig_account.get("id")
            print(f"✅ IG ACCOUNT FOUND: {ig_id}")

            ig_user = requests.get(
                f"https://graph.facebook.com/v18.0/{ig_id}",
                params={
                    "fields": "id,username",
                    "access_token": page_token
                }
            ).json()

            print("🔹 IG USER:", ig_user)

            SocialAccount.objects.update_or_create(
                social_id=ig_user.get("id"),
                platform="instagram",
                defaults={
                    "username": ig_user.get("username"),
                    "access_token": page_token
                }
            )

            print("✅ SAVED TO DATABASE")

            return redirect("http://localhost:3000/connect-instagram?success=true")

    print("❌ No Instagram account linked")
    return redirect("http://localhost:3000/error?msg=no_instagram")

def connect_twitter(request):
    # 🔹 Generate code verifier
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")

    # 🔹 Generate code challenge
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode("utf-8").rstrip("=")

    # 🔥 STORE IN SESSION (this is what you are missing)
    request.session["twitter_code_verifier"] = code_verifier

    base_url = "https://twitter.com/i/oauth2/authorize"

    params = {
        "response_type": "code",
        "client_id": settings.TWITTER_CLIENT_ID,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "scope": "tweet.read users.read offline.access",
        "state": "engagex_state",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)


def twitter_callback(request):
    code = request.GET.get("code")
    error = request.GET.get("error")

    # 🔴 Handle OAuth error
    if error:
        print("❌ Twitter OAuth Error:", error)
        return redirect("http://localhost:3000/error?msg=twitter_auth_failed")

    if not code:
        print("❌ No authorization code received")
        return redirect("http://localhost:3000/error?msg=no_code")

    # 🔹 Get PKCE verifier from session
    code_verifier = request.session.get("twitter_code_verifier")

    if not code_verifier:
        print("❌ Missing code_verifier in session")
        return redirect("http://localhost:3000/error?msg=pkce_missing")

    # 🔹 Exchange code for access token
    token_response = requests.post(
        "https://api.twitter.com/2/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "client_id": settings.TWITTER_CLIENT_ID,
            "redirect_uri": settings.TWITTER_REDIRECT_URI,
            "code": code,
            "code_verifier": code_verifier,
        },
        auth=(
            settings.TWITTER_CLIENT_ID,
            settings.TWITTER_CLIENT_SECRET
        ),
    ).json()

    print("🔹 TOKEN RESPONSE:", token_response)

    access_token = token_response.get("access_token")

    if not access_token:
        print("❌ No access token received")
        return redirect("http://localhost:3000/error?msg=no_token")

    # 🔹 Fetch user profile
    user_response = requests.get(
        "https://api.twitter.com/2/users/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    ).json()

    print("🔹 USER RESPONSE:", user_response)

    user_data = user_response.get("data", {})

    if not user_data:
        print("❌ No user data received")
        return redirect("http://localhost:3000/error?msg=no_user")

    # 🔹 Save to DB
    SocialAccount.objects.update_or_create(
        social_id=user_data.get("id"),
        platform="twitter",
        defaults={
            "username": user_data.get("username"),
            "access_token": access_token
        }
    )

    print("✅ Twitter account saved successfully")

    return redirect("http://localhost:3000/connect-facebook?success=true")





def connect_youtube(request):
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"

    params = {
        "client_id": settings.YOUTUBE_CLIENT_ID,
        "redirect_uri": settings.YOUTUBE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.readonly",
        "access_type": "offline",
        "prompt": "consent"
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)


def youtube_callback(request):
    code = request.GET.get("code")

    if not code:
        return redirect("http://localhost:3000/error?msg=no_code")

    # 🔹 Exchange code for token
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": settings.YOUTUBE_CLIENT_ID,
            "client_secret": settings.YOUTUBE_CLIENT_SECRET,
            "redirect_uri": settings.YOUTUBE_REDIRECT_URI,
            "grant_type": "authorization_code",
            "code": code,
        }
    ).json()

    print("TOKEN:", token_response)

    access_token = token_response.get("access_token")

    if not access_token:
        return redirect("http://localhost:3000/error?msg=no_token")

    # 🔹 Get channel info (USERNAME)
    channel_response = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={
            "part": "snippet",
            "mine": "true"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    ).json()

    print("CHANNEL:", channel_response)

    items = channel_response.get("items", [])

    if not items:
        return redirect("http://localhost:3000/error?msg=no_channel")

    channel = items[0]

    username = channel["snippet"]["title"]
    channel_id = channel["id"]

    # 🔹 Save in DB
    SocialAccount.objects.update_or_create(
        social_id=channel_id,
        platform="youtube",
        defaults={
            "username": username,
            "access_token": access_token
        }
    )

    return redirect("http://localhost:3000/connect-youtube?success=true")



def google_login(request):
    user_type = request.GET.get("type", "buyer")

    # store userType temporarily
    request.session["pending_user_type"] = user_type

    base_url = "https://accounts.google.com/o/oauth2/v2/auth"

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)




def google_callback(request):
    code = request.GET.get("code")

    if not code:
        return redirect("http://localhost:3000/error?msg=no_code")

    # 🔹 Exchange code for token
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        }
    ).json()

    access_token = token_response.get("access_token")

    # 🔹 Get user info (OIDC identity)
    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    print("GOOGLE USER:", user_info)

    email = user_info.get("email")
    google_id = user_info.get("sub")
    name = user_info.get("name")

    user_type = request.session.get("pending_user_type", "buyer")

    # 🔹 STEP 1: Find or create user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "first_name": name,
            "role": user_type,
        }
    )

    # 🔹 STEP 2: Ensure correct role profile
    if user_type == "buyer":
        BuyerProfile.objects.get_or_create(user=user)
    else:
        SellerProfile.objects.get_or_create(user=user)

    # 🔹 STEP 3: Link SocialAuth
    SocialAuth.objects.update_or_create(
        provider="google",
        provider_id=google_id,
        defaults={"user": user}
    )

    return redirect("http://localhost:3000/dashboard")





import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

def connections_status(request):
    platforms = ['facebook', 'instagram', 'twitter', 'youtube']
    result = {}

    for platform in platforms:
        try:
            account = SocialAccount.objects.get(platform=platform)
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
                account.delete()
                result[platform] = {"connected": False, "username": None}

        except SocialAccount.DoesNotExist:
            result[platform] = {"connected": False, "username": None}

    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["DELETE"])
def disconnect_platform(request, platform):
    try:
        account = SocialAccount.objects.get(platform=platform)
        account.delete()
        return JsonResponse({"message": f"{platform} disconnected"})
    except SocialAccount.DoesNotExist:
        return JsonResponse({"error": "Not connected"}, status=404)







from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from service.models import TestAccount
from django.views.decorators.csrf import csrf_exempt

@api_view(['POST'])
@csrf_exempt
def login_view(request):
    user_id = request.data.get('user_id')

    if not user_id:
        return Response(
            {"error": "user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get or create account in database
    account, created = TestAccount.objects.get_or_create(user_id=user_id)

    # Generate JWT token
    refresh = RefreshToken()
    refresh['user_id'] = user_id

    # ✅ Return token in response BODY (not cookie)
    return Response({
        "message": "Login successful",
        "user_id": user_id,
        "first_time": created,
        "access_token": str(refresh.access_token),   # ← frontend saves this
        "refresh_token": str(refresh),               # ← frontend saves this
    })


@api_view(['GET'])
@csrf_exempt
def check_login(request):
    # Read token from Authorization header
    auth  = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '')

    if not token:
        return Response({"logged_in": False})

    try:
        decoded = AccessToken(token)
        user_id = decoded.get('user_id')
        return Response({
            "logged_in": True,
            "user_id": user_id
        })
    except Exception:
        return Response({"logged_in": False})


@api_view(['POST'])
@csrf_exempt
def logout_view(request):
    # Nothing to do on backend
    # Frontend handles clearing localStorage
    return Response({"message": "Logged out"})
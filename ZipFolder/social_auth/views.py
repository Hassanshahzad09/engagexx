# users/views.py

import urllib.parse
import base64
import hashlib
import os


import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

import requests
from django.shortcuts import redirect
from django.conf import settings
from service.models import SocialAccount,User,BuyerProfile,SellerProfile,SocialAuth


def _canonical_seller_user_id(raw_seller_id):
    """
    SocialAccount.sellerId MUST store the logged-in User.id of the seller.
    Do not store/match SellerProfile.id here, otherwise Seller 1 can appear
    connected inside Seller 2 when IDs overlap.
    """
    if raw_seller_id is None or str(raw_seller_id).strip() == "":
        return None

    raw_seller_id = int(raw_seller_id)

    # Frontend sends userId, so this should normally pass.
    if User.objects.filter(id=raw_seller_id, role="seller").exists():
        return raw_seller_id

    # Fallback only for old callers that accidentally send SellerProfile.id.
    try:
        return SellerProfile.objects.get(id=raw_seller_id).user_id
    except SellerProfile.DoesNotExist:
        return raw_seller_id


def _build_state_with_seller(raw_seller_id, extra=None):
    payload = {"seller_id": _canonical_seller_user_id(raw_seller_id)}
    if extra:
        payload.update(extra)
    return base64.b64encode(json.dumps(payload).encode()).decode()

def connect_facebook(request):
    base_url = "https://www.facebook.com/v18.0/dialog/oauth"
    seller_id = request.GET.get('seller_id')
    state = _build_state_with_seller(seller_id)
    params = {
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "scope": "public_profile",
        "response_type": "code",
        "state": state
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)



def facebook_callback(request):
    code = request.GET.get("code")

    if not code:
        return HttpResponse("No code received from Facebook")

    # Decode state
    state = request.GET.get('state')

    try:
        data = json.loads(base64.b64decode(state).decode())
        seller_id = _canonical_seller_user_id(data.get('seller_id'))
    except Exception as e:
        return HttpResponse(f"Invalid state: {str(e)}")

    # Exchange code for token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"

    token_response = requests.get(token_url, params={
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "client_secret": settings.FACEBOOK_CLIENT_SECRET,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "code": code,
    }).json()

    print("TOKEN RESPONSE:", token_response)

    access_token = token_response.get("access_token")

    if not access_token:
        return HttpResponse("Failed to get access token")

    # Get Facebook user info
    user_info = requests.get(
        "https://graph.facebook.com/me",
        params={
            "fields": "id,name",
            "access_token": access_token
        }
    ).json()

    print("USER INFO:", user_info)

    username = user_info.get("name")
    social_id = user_info.get("id")

    if not username or not social_id:
        return HttpResponse("Facebook did not return complete user data")

    # Save/update account. One seller should have only one row per platform.
    SocialAccount.objects.update_or_create(
        platform="facebook",
        sellerId=seller_id,
        defaults={
            "username": username,
            "social_id": social_id,
            "access_token": access_token,
        }
    )

    return redirect("http://localhost:3000/connect-facebook")






def connect_instagram(request):
    base_url = "https://www.facebook.com/v18.0/dialog/oauth"
    seller_id = request.GET.get('seller_id')
    state = _build_state_with_seller(seller_id)
    params = {
    "client_id": settings.INSTAGRAM_CLIENT_ID,
    "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
    "scope": "pages_show_list,pages_read_engagement,instagram_basic",
    "response_type": "code",
    "auth_type": "rerequest",   # 🔥 IMPORTANT
    "state": state
}

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    print("INSTAGRAM URL:", url)
    return redirect(url)

def instagram_callback(request):
    code = request.GET.get("code")
    state = request.GET.get('state')
    data = json.loads(base64.b64decode(state).decode())
    seller_id = _canonical_seller_user_id(data.get('seller_id'))
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
                platform="instagram",
                sellerId=seller_id,
                defaults={
                    "social_id": ig_user.get("id"),
                    "username": ig_user.get("username"),
                    "access_token": page_token,
                }
            )

            print("✅ SAVED TO DATABASE")

            return redirect("http://localhost:3000/connect-instagram?success=true")

    print("❌ No Instagram account linked")
    return redirect("http://localhost:3000/error?msg=no_instagram")

def connect_twitter(request):

    seller_id = request.GET.get("seller_id")

    # =========================================
    # 1. GENERATE PKCE
    # =========================================

    code_verifier = base64.urlsafe_b64encode(
        os.urandom(32)
    ).decode().rstrip("=")

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")

    # =========================================
    # 2. STORE EVERYTHING IN STATE (NO SESSION)
    # =========================================

    state_payload = {
        "seller_id": _canonical_seller_user_id(seller_id),
        "code_verifier": code_verifier
    }

    state = base64.urlsafe_b64encode(
        json.dumps(state_payload).encode()
    ).decode()

    # =========================================
    # 3. BUILD AUTH URL
    # =========================================

    params = {
        "response_type": "code",
        "client_id": settings.TWITTER_CLIENT_ID,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "scope": "tweet.read users.read offline.access",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    url = "https://twitter.com/i/oauth2/authorize?" + urllib.parse.urlencode(params)

    return redirect(url)

def twitter_callback(request):

    code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")

    # =========================================
    # HANDLE ERRORS
    # =========================================

    if error:
        return redirect("http://localhost:3000/error?msg=twitter_auth_failed")

    if not code or not state:
        return redirect("http://localhost:3000/error?msg=missing_params")

    # =========================================
    # DECODE STATE
    # =========================================

    try:
        decoded = json.loads(
            base64.urlsafe_b64decode(state).decode()
        )

        seller_id = _canonical_seller_user_id(decoded.get("seller_id"))
        code_verifier = decoded.get("code_verifier")

        print("SELLER:", seller_id)
        print("VERIFIER:", code_verifier)

    except Exception as e:
        print("STATE ERROR:", e)
        return redirect("http://localhost:3000/error?msg=state_error")

    # =========================================
    # TOKEN EXCHANGE
    # =========================================

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

    print("TOKEN:", token_response)

    access_token = token_response.get("access_token")

    if not access_token:
        return redirect("http://localhost:3000/error?msg=token_failed")

    # =========================================
    # GET USER INFO
    # =========================================

    user_data = requests.get(
        "https://api.twitter.com/2/users/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    ).json().get("data", {})

    if not user_data:
        return redirect("http://localhost:3000/error?msg=no_user")

    # =========================================
    # SAVE TO DB (NO UPDATE, ALWAYS INSERT)
    # =========================================

    SocialAccount.objects.update_or_create(
        platform="twitter",
        sellerId=seller_id,
        defaults={
            "social_id": user_data.get("id"),
            "username": user_data.get("username"),
            "access_token": access_token,
        }
    )

    return redirect("http://localhost:3000/success")




def connect_youtube(request):
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    seller_id = request.GET.get('seller_id')
    state = _build_state_with_seller(seller_id)
    params = {
        "client_id": settings.YOUTUBE_CLIENT_ID,
        "redirect_uri": settings.YOUTUBE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(url)


def youtube_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")
    data = json.loads(base64.b64decode(state).decode())
    seller_id = _canonical_seller_user_id(data.get('seller_id'))
    
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

    # 🔹 Save/update in DB
    SocialAccount.objects.update_or_create(
        platform="youtube",
        sellerId=seller_id,
        defaults={
            "social_id": channel_id,
            "username": username,
            "access_token": access_token,
        }
    )

    return redirect("http://localhost:3000/connect-youtube?success=true")

















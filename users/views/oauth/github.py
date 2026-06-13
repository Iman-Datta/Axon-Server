import hashlib
import requests
import secrets

from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken


from django.shortcuts import redirect
from urllib.parse import urlencode

from django.conf import settings

from ...models import User

@api_view(["GET"])
def github_login_view(request):
    github_url = (
        "https://github.com/login/oauth/authorize?"
        +
        urlencode(
            {
                "client_id": settings.GITHUB_CLIENT_ID,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
                "scope": "read:user user:email",
            }
        )
    )

    return redirect(github_url)

@api_view(["GET"])
def github_callback_view(request):
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not code:
        return redirect(f"{settings.FRONTEND_URL}/auth")
    
    try:
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=10
        )

        if token_response.status_code != 200:
            return redirect(f"{settings.FRONTEND_URL}/auth")
        
        token_data = token_response.json()

        github_access_token = token_data.get("access_token")
        
        if not github_access_token:
            return redirect(f"{settings.FRONTEND_URL}/auth")
        
        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_access_token}"},
            timeout=10
        )

        if user_response.status_code != 200:
            return redirect(f"{settings.FRONTEND_URL}/auth")
        
        github_user = user_response.json()

        github_id = str(github_user.get("id"))
        github_username = github_user.get("login")
        avatar = github_user.get("avatar_url", "")
        github_profile = github_user.get("html_url", "")

        if state:
            hashed_state = hashlib.sha256(state.encode()).hexdigest()
            user = User.objects.filter(oauth_state=hashed_state).first()
            if not user:
                return redirect(f"{settings.FRONTEND_URL}/auth")
            
            if (not user.oauth_state_expire or user.oauth_state_expire < timezone.now()):
                user.oauth_state = None
                user.oauth_state_expire = None
                user.save(
                    update_fields=[
                        "oauth_state",
                        "oauth_state_expire"
                    ]
                )
                return redirect(f"{settings.FRONTEND_URL}/auth")
            
            github_exists = (User.objects.filter(github_id = github_id).exclude(id = user.id).exists())
            if github_exists:
                user.oauth_state = None
                user.oauth_state_expire = None
                user.save(
                    update_fields=[
                        "oauth_state",
                        "oauth_state_expire"
                    ]
                )

                return redirect(f"{settings.FRONTEND_URL}/auth")
            
            user.github_id = github_id
            user.github_username = github_username
            user.github_profile = github_profile
            user.oauth_state = None
            user.oauth_state_expire = None

            update_fields = [
                "github_id",
                "github_username",
                "github_profile",
                "oauth_state",
                "oauth_state_expire"
            ]

            if not user.avatar:
                user.avatar = avatar
                update_fields.append("avatar")

            user.save(update_fields=update_fields)

            return redirect(f"{settings.FRONTEND_URL}/onboarding")
        
        else:

            email = None

            email_response = requests.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {github_access_token}"},
                timeout=10
            )
            if email_response.status_code == 200:
                emails = email_response.json()
                for item in emails:
                    if (item.get("primary") and item.get("verified")):
                        email = item.get("email")
                        break

            user = User.objects.filter(github_id = github_id).first()
            
            if not user and email:
                user = User.objects.filter(email = email).first()

            if user:
                update_fields = []

                if not user.github_id:
                    user.github_id = github_id
                    update_fields.append("github_id")

                if not user.github_username:
                    user.github_username = github_username
                    update_fields.append("github_username")
                
                if not user.github_profile:
                    user.github_profile = github_profile
                    update_fields.append("github_profile")

                if email and user.email != email:
                    exists = (User.objects.filter(email = email)).exclude(id = user.id).exists()

                    if not exists:
                        user.email = email
                        update_fields.append("email")

                if email and not user.is_email_verified:
                    user.is_email_verified = True
                    update_fields.append("is_email_verified")

                if not user.avatar:
                    user.avatar = avatar
                    update_fields.append("avatar")

                if update_fields:
                    user.save(update_fields=update_fields)
            
            else:
                temp_username = (f"github_{secrets.token_hex(8)}")
                user = User.objects.create(
                    username=temp_username,
                    email=email,

                    github_id=github_id,
                    github_username=github_username,
                    github_profile=github_profile,

                    avatar=avatar,

                    is_username_set=False,
                    is_email_verified=True if email else False,
                    is_profile_completed=False
                )
            
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh)

            hashed_refresh = hashlib.sha256(refresh_token.encode()).hexdigest()
            user.refresh_token_hash = hashed_refresh

            user.save(
                update_fields=[
                    "refresh_token_hash"
                ]
            )

            response = redirect(f"{settings.FRONTEND_URL}/dashboard")
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False, # True on HTTPS production
                samesite="Lax",
                max_age=7*24*60*60
            )
            return response
    
    except Exception as error:
        print(error)
        return redirect(f"{settings.FRONTEND_URL}/auth")

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def github_connect_view(request):
    user = request.user

    if user.github_id:
        return redirect(f"{settings.FRONTEND_URL}/dashboard")
    
    state = secrets.token_urlsafe(32)

    user.oauth_state  = hashlib.sha256(state.encode()).hexdigest()
    user.oauth_state_expire = (timezone.now() + timedelta(minutes=5))

    user.save(
        update_fields=[
            "oauth_state",
            "oauth_state_expire"
        ]
    )

    github_url = (
        "https://github.com/login/oauth/authorize?"
        +
        urlencode(
            {
                "client_id": settings.GITHUB_CLIENT_ID,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
                "scope": "read:user user:email",
                "state": state,
            }
        )
    )

    return redirect(github_url)

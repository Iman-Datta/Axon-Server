import hashlib
import requests
import secrets

from rest_framework.decorators import (api_view)
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import redirect
from urllib.parse import urlencode

from django.conf import settings
from ...models import User

@api_view(['GET'])
def google_login_view(request):
    google_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        +
        urlencode(
            {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "select_account",
            }
        )
    )
    return redirect(google_url)

@api_view(["GET"])
def google_callback_view(request):
    code = request.GET.get("code")
    if not code:
        return redirect(f"{settings.FRONTEND_URL}/auth")

    try:
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",

            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },

            timeout=10
        )
        if token_response.status_code != 200:
            return redirect(f"{settings.FRONTEND_URL}/auth")

        token_data = token_response.json()
        google_access_token = token_data.get("access_token")

        if not google_access_token:
           return redirect(f"{settings.FRONTEND_URL}/auth")

        user_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",

            headers={
                "Authorization": (f"Bearer {google_access_token}")
            },
            timeout=10
        )
        if user_response.status_code != 200:
            return redirect(f"{settings.FRONTEND_URL}/auth")
        
        google_user = user_response.json()

        if not google_user.get("verified_email"):
            return redirect(f"{settings.FRONTEND_URL}/auth")

        
        google_id = google_user.get("id")
        email = google_user.get("email")
        first_name = google_user.get("given_name", "")
        last_name = google_user.get("family_name", "")
        avatar = google_user.get("picture", "")

        user = User.objects.filter(google_id=google_id).first() # check Google identity

        if not user and email: # email fallback
            user = User.objects.filter(email=email).first()

        if user:
            update_fields = []

            if not user.google_id:
                user.google_id = google_id
                update_fields.append("google_id")

            if email and user.email != email: # Google id match but email doesnot
                email_exists = User.objects.filter(email=email).exclude(id=user.id).exists()
                if not email_exists:
                    user.email = email
                    update_fields.append("email")
                else:
                    # TODO: Handle OAuth email conflict case (provider ID matches but new email already belongs to another Axon account)
                    pass

            if not user.is_email_verified:
                user.is_email_verified = True
                update_fields.append("is_email_verified")

            if not user.avatar:
                user.avatar = avatar
                update_fields.append("avatar")

            if update_fields:
                user.save(update_fields=update_fields)

        else: # New Google account:

            temp_username = f"user_{secrets.token_hex(8)}"

            user = User.objects.create(
                username=temp_username,
                email=email,
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                avatar=avatar,
                is_email_verified=True,
                is_profile_completed=False,
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
            secure=False,   # True in production HTTPS
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,

        )
        return response

    except Exception as error:
        print(error)
        return redirect(f"{settings.FRONTEND_URL}/auth")

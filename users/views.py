from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.shortcuts import redirect

from .serializers import RegisterSerializer

import secrets
import hashlib

from django.utils import timezone
from datetime import timedelta

from django.conf import settings
from .models import User
from .utils.send_email import send_email
from .emails.verify_email_template import (verify_email_template)

@api_view(['POST'])
def register_view(request):

    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():

        user = serializer.save()

        raw_token = secrets.token_urlsafe(32) # raw token generate
        hash_token = hashlib.sha256(raw_token.encode()).hexdigest() # hash token for db
        
        user.email_verification_token = hash_token # hash token store in DB
        user.email_verification_expire = (timezone.now() + timedelta(minutes=15))

        user.save()

        verification_url = (f"{settings.BACKEND_URL}" f"/verify-email/?token={raw_token}")

        send_email(user.email,"Verify your email",verify_email_template(verification_url))

        return Response(
            {
                "message": (
                    "Account created. "
                    "Please verify your email."
                ),
                "verification_url": verification_url,
                "success": True
            },
            status=201
        )

    return Response(serializer.errors,status=400)

@api_view(['GET'])
def verify_email_view(request):
    raw_token = request.GET.get("token")

    if not raw_token:
        return Response(
            {
                "message": "Token missing",
                "success": False
            },
            status=400
        )
    
    hash_token = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        user = User.objects.get(email_verification_token = hash_token)
    except User.DoesNotExist:
        return Response(
            {
                "message": "Invalid token",
                "success": False
            },
            status=400
        )
    
    if(user.is_email_verified and user.email_verification_expire<timezone.now()):
        return Response(
            {
                "message": "Token expired",
                "success": False
            }
        )
    
    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expire = None

    refresh = RefreshToken.for_user(user)
    refresh_token = str(refresh)
    hashed_refresh = hashlib.sha256(refresh_token.encode()).hexdigest
    user.refresh_token_hash = hashed_refresh

    user.save()

    response = redirect(f"{settings.FRONTEND_URL}/auth/callback")

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # True in production
        samesite="Lax"
    )

    return response

@api_view(['POST'])
def refresh_token_view(request):
    refresh_token = request.COOKIES.get("refresh_token")

    if not refresh_token:
        return Response({"message": "Refresh token missing", "success": False}, status=401)
    
    try:
        token = RefreshToken(refresh_token)
        if token["token_type"] != "refresh":
            return Response({"message": "Invalid token type","success": False}, status=401)
        
        user_id = token["user_id"]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found", "success": False}, status=404)
        
        hashed_refresh= hashlib.sha256(refresh_token.encode()).hexdigest()

        if user.refresh_token_hash != hashed_refresh:
            user.refresh_token_hash = None
            user.save()
            return Response({"message": "Invalid refresh token","success": False}, status=401)
        
        # Generate new Refresh token (Rotation)
        new_refresh = RefreshToken.for_user(user)
        new_refresh_token = str(new_refresh)
        new_hashed_refresh = hashlib.sha256(new_refresh_token.encode()).hexdigest() # Hash new refresh token

        user.refresh_token_hash = new_hashed_refresh
        user.save()

        new_access_token = str(new_refresh.access_token)
        
        response =  Response({ "access_token": new_access_token, "success": True},status=200)

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=False,  # True in production
            samesite="Lax"
        )
        return response
    except TokenError:
         return Response({"message": "Invalid or expired refresh token", "success": False},status=401)
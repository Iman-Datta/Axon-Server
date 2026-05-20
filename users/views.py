from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.shortcuts import redirect
from django.contrib.auth import authenticate

from .serializers import RegisterSerializer, LoginSerializer

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
    
    if user.is_email_verified:
        return Response({"message": "Email already verified","success": False},status=400)
    
    if(user.email_verification_expire and user.email_verification_expire<timezone.now()):
        return Response({"message": "Token expired","success": False},status=400)
    
    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expire = None

    refresh = RefreshToken.for_user(user)
    refresh_token = str(refresh)
    hashed_refresh = hashlib.sha256(refresh_token.encode()).hexdigest()
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
        
        response =  Response({"access_token": new_access_token, "success": True},status=200)

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

@api_view(['POST'])
def login_view(request):    
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=400
        )

    validated_data = serializer.validated_data

    email = validated_data.get("email")
    username = validated_data.get("username")
    password = validated_data.get("password")

    user = None

    # Login with email
    if email:

        try:
            user_obj = User.objects.get(email=email)

            user = authenticate(username=user_obj.username,password=password
            )

        except User.DoesNotExist:

            return Response({"message": "Invalid credentials", "success": False}, status=400)

    # Login with username
    elif username:
        user = authenticate(username=username, password=password)

    # Invalid password / auth failed
    if not user:

        return Response({"message": "Invalid credentials", "success": False}, status=401)
    
    # Email verification check
    if not user.is_email_verified:

        return Response(
            {"message": "Please verify your email", "success": False}, status=403)

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    refresh_token = str(refresh)
    access_token = str(refresh.access_token)

    # Hash refresh token
    hashed_refresh = hashlib.sha256(refresh_token.encode()).hexdigest()

    # Save hashed refresh token
    user.refresh_token_hash = hashed_refresh

    user.save()

    response = Response(
        {"access_token": access_token, "message": "Login successful","success": True },status=200)

    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,   # True in production
        samesite="Lax"
    )

    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_viwe(request):
    user = request.user

    user.refresh_token_hash = None
    user.save()

    response = Response({"message": "Logout successful","success": True},status=200)

    response.delete_cookie("refresh_token")
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):

    try:
        user = request.user
        if not user:
            return Response({"message": "User not found","success": False}, status=404)
        
        avatar_url = None

        if user.avatar:
            avatar_url = request.build_absolute_uri(
                user.avatar.url
            )

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,

            "first_name": user.first_name,
            "last_name": user.last_name,

            "avatar": avatar_url,
            "bio": user.bio,

            "is_email_verified": user.is_email_verified,
            "is_profile_completed": user.is_profile_completed,

            "google_id": user.google_id,

            "github_profile": user.github_profile,
            "linkedin_profile": user.linkedin_profile,
            "portfolio_website": user.portfolio_website,

            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        return Response({"user": user_data,"success": True}, status=200)
    
    except Exception as e:
        return Response(
            {"message": str(e),"success": False},status=500)


import hashlib
import requests
import secrets

from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status

from django.shortcuts import redirect
from django.contrib.auth import authenticate
from urllib.parse import urlencode

from .serializers import RegisterSerializer, LoginSerializer

from django.utils import timezone

from django.conf import settings
from .models import User
from .utils.email_verification import send_verification_email


@api_view(['POST'])
def register_view(request):

    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():

        user = serializer.save()

        send_verification_email(user)

        return Response({"message": "Account created. Please verify your email.", "success": True},status=201)
            
    return Response(serializer.errors,status=400)

@api_view(["GET"])
def verify_email_view(request):

    raw_token = request.GET.get("token")


    def redirect_callback(status, message):
        params = urlencode({
            "status": status,
            "message": message
        })

        return redirect(
            f"{settings.FRONTEND_URL}/email-callback?{params}"
        )


    # Token missing
    if not raw_token:
        return redirect_callback(
            "failed",
            "Verification token is missing."
        )


    hashed_token = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()


    # Find user
    try:
        user = User.objects.get(
            email_verification_token=hashed_token
        )

    except User.DoesNotExist:

        return redirect_callback(
            "failed",
            "Verification link is invalid or already used."
        )


    # Already verified
    if user.is_email_verified:

        return redirect_callback(
            "success",
            "Your email is already verified."
        )


    # Token expired
    if (
        user.email_verification_expire
        and user.email_verification_expire < timezone.now()
    ):

        user.email_verification_token = None
        user.email_verification_expire = None

        user.save(
            update_fields=[
                "email_verification_token",
                "email_verification_expire"
            ]
        )


        return redirect_callback(
            "expired",
            "Verification link expired. Please request a new one."
        )


    # Verify user
    user.is_email_verified = True

    user.email_verification_token = None

    user.email_verification_expire = None



    # Create JWT refresh token
    refresh = RefreshToken.for_user(user)

    refresh_token = str(refresh)


    # Store hashed refresh token
    user.refresh_token_hash = hashlib.sha256(
        refresh_token.encode()
    ).hexdigest()


    user.save(
        update_fields=[
            "is_email_verified",
            "email_verification_token",
            "email_verification_expire",
            "refresh_token_hash"
        ]
    )



    response = redirect_callback(
        "success",
        "Email verified successfully."
    )


    # Store refresh cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,     # True on HTTPS production
        samesite="Lax",
        max_age=7 * 24 * 60 * 60
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
        return Response({"success": False,"errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data

    identifier = validated_data.get("identifier")
    password = validated_data.get("password")

    user = None
    if "@" in identifier:

        try:
            user_obj = User.objects.get(email=identifier)

            if not user_obj.is_email_verified:
                send_verification_email(user_obj)
                return Response(
                    {
                        "success": False,
                        "message": (
                            "Email not verified. "
                            "Verification email sent again."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            user = authenticate(
                username=user_obj.username,
                password=password
            )

        except User.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Invalid credentials."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

    else:

        try:
            user_obj = User.objects.get(username=identifier)

            if not user_obj.is_email_verified:
                send_verification_email(user_obj)

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Email not verified. "
                            "Verification email sent again."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            user = authenticate(
                username=identifier,
                password=password
            )

        except User.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Invalid credentials."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

    if not user:

        return Response(
            {
                "success": False,
                "message": "Invalid credentials."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(user)

    refresh_token = str(refresh)
    access_token = str(refresh.access_token)

    hashed_refresh_token = hashlib.sha256(
        refresh_token.encode()
    ).hexdigest()

    user.refresh_token_hash = hashed_refresh_token
    user.save()

    response = Response(
        {
            "success": True,
            "message": "Login successful.",
            "access_token": access_token,

            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": (
                    user.avatar.url
                    if user.avatar
                    else None
                ),
                "bio": user.bio,
                "is_email_verified": user.is_email_verified,
                "is_profile_completed": user.is_profile_completed,
            }
        },
        status=status.HTTP_200_OK
    )

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
def logout_view(request):
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

@api_view(['GET'])
def google_login_view():
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

        
        email = google_user.get("email")
        first_name = google_user.get("given_name", "")
        last_name = google_user.get("family_name", "")

        user = User.objects.filter( email=email).first()

        if user:
            user.is_email_verified = True
            user.save(
                update_fields=[
                    "is_email_verified"
                ]
            )

        else: # New Google account:

            temp_username = f"user_{secrets.token_hex(8)}"

            user = User.objects.create(
                username=temp_username,
                email=email,
                first_name=first_name,
                last_name=last_name,
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
    
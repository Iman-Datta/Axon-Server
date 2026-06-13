import hashlib

from django.utils import timezone
from django.shortcuts import redirect
from django.conf import settings
from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from urllib.parse import urlencode

from ...serializers import (EmailOTPRequestSerializer, EmailOTPVerifySerializer)
from ...utils.email_verification import send_email_otp
from ...models import User

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_otp_view(request):
    user = request.user

    serializer = EmailOTPRequestSerializer(data = request.data)
    if not serializer.is_valid():
        return Response(
            {
            "success": False,
            "errors": serializer.errors
            },
            status=400
        )
    
    send_email_otp(user,serializer.validated_data["email"])
    return Response({
        "success": True,
        "message": "OTP sent successfully."
    },status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_email_otp_view(request):
    user = request.user

    serializer = EmailOTPVerifySerializer(data = request.data)
    if not serializer.is_valid():
        return Response(
            {
            "success": False,
            "errors": serializer.errors
            },
            status=400
        )
    
    otp_hash = hashlib.sha256(serializer.validated_data["otp"].encode()).hexdigest()
    if user.email_otp_hash != otp_hash:
        return Response(
            {
            "success": False,
            "errors": "Invalid OTP."
            },
            status=400
        )
    
    if (not user.email_otp_expire or user.email_otp_expire < timezone.now()):
        user.email_otp_hash = None
        user.email_otp_expire = None
        user.pending_email = None

        user.save(
            update_fields=[
                "email_otp_hash",
                "email_otp_expire",
                "pending_email"
            ]
        )

        return Response(
            {
                "success": False,
                "message": "OTP expired."
            },
            status=400
        )
    
    user.email = user.pending_email
    user.pending_email = None
    user.is_email_verified = True
    user.email_otp_hash = None
    user.email_otp_expire = None

    user.save(
        update_fields=[
            "email",
            "pending_email",
            "is_email_verified",
            "email_otp_hash",
            "email_otp_expire"
        ]
    )

    return Response(
        {
            "success": True,
            "message": "Email verified successfully."
        },
        status=200
    )

@api_view(["GET"])
def verify_magiclink_view(request):

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

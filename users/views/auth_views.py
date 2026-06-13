import hashlib
from django.contrib.auth import authenticate
from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status

from ..serializers import RegisterSerializer, LoginSerializer

from ..models import User
from ..utils.email_verification import send_magicLink_email

@api_view(['POST'])
def register_view(request):

    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():

        user = serializer.save()

        send_magicLink_email(user)

        return Response({"message": "Account created. Please verify your email.", "success": True},status=201)
            
    return Response(serializer.errors,status=400)

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
        user.save(update_fields=["refresh_token_hash"])

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
                send_magicLink_email(user_obj)
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
                send_magicLink_email(user_obj)

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

                "is_username_set": user.is_username_set,
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

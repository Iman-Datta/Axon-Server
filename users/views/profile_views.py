from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import User
from ..serializers import UsernameUpdateSerializer, UsernameSerializer, CompleteProfileSerializer,PublicProfileSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user

    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,

        "first_name": user.first_name,
        "last_name": user.last_name,

        "avatar": user.avatar,
        "bio": user.bio,

        "is_username_set": user.is_username_set,
        "is_email_verified": user.is_email_verified,
        "is_profile_completed": user.is_profile_completed,

        "github_profile": user.github_profile,
        "linkedin_profile": user.linkedin_profile,
        "portfolio_website": user.portfolio_website,

        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }

    return Response(
        {
            "user": user_data,
            "success": True
        },
        status=200
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_status_view(request):
    user = request.user

    username_status = user.is_username_set
    email_status = bool(user.email) and user.is_email_verified
    github_status = bool(user.github_id)
    profile_status = user.is_profile_completed

    identity_status = (
        username_status
        and email_status
        and github_status
    )
    return Response(
        {
            "success": True,

            "identity": {
                "status": identity_status,

                "requirements": {
                    "username": username_status,
                    "email": email_status,
                    "github": github_status,
                },
                "data": {
                    "username": user.username if username_status else None,

                    "email": user.email if email_status else None,

                    "github": {
                        "id": user.github_id,
                        "username": user.github_username,
                        "profile": user.github_profile,
                        "avatar": user.avatar,
                    } if github_status else None,
                },
            },

            "profile": {
                "status": profile_status,

                "data": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                } if profile_status else None,
            },
        },
        status=200,
    )

@api_view(["GET"])
def check_username_view(request):
    serializer = UsernameSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=400
        )
    username = serializer.validated_data["username"]
    
    username_exists = User.objects.filter(username__iexact=username).exists()
    return Response({
            "success": True,
            "available": not username_exists
        },
        status=200
    )

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_username_view(request):
    user = request.user

    serializer = UsernameUpdateSerializer(data=request.data, context={"user": user})

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=400
        )

    user.username = serializer.validated_data["username"]
    user.is_username_set = True
    user.save(update_fields=["username","is_username_set"])

    return Response(
        {
            "success": True,
            "message": "Username updated successfully."
        },
        status=200
    )

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def complete_profile_view(request):

    user = request.user
    # identity must be completed first
    if (
        not user.is_username_set
        or not user.is_email_verified
        or not user.github_id
    ):

        return Response(
            {
                "success": False,
                "message": "Complete identity setup first."
            },
            status=400
        )

    serializer = CompleteProfileSerializer(
        user,
        data=request.data,
        partial=True
    )

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=400
        )

    if not (user.first_name or serializer.validated_data.get("first_name")) or not  (user.last_name or serializer.validated_data.get("last_name")):
        return Response(
            {
                "success": False,
                "message": "First name and last name required."
            },
            status=400
        )

    serializer.save()

    return Response(
        {
            "success": True,
            "message": "Profile completed successfully."
        },
        status=200
    )

@api_view(["GET"])
def public_profile_view(request,username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"message":"User not found"},status=404)

        serializer = PublicProfileSerializer(user)

        return Response({
            "success": True,
            "data": serializer.data
        },status=200)
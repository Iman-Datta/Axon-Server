from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import User

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

    identity_status = username_status and email_status and github_status

    return Response(
        {
            "success": True,
            "identity": {
                "status": identity_status,
                "requirements": {
                    "username": username_status,
                    "email": email_status,
                    "github": github_status,
                }
            },
            "profile": {
                "status": profile_status
            }
        },
        status=200
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_username_view(request):
    username = request.GET.get("username")


    if not username:
        return Response({
                "success": False,
                "message": "Username is required."
            },
            status=400
        )
    
    username = username.strip()

    if(len(username) < 4):
         return Response({            
                "success": False,
                "message": "Username must contain at least 4 characters."
            },
            status=400
        )
    
    username_exists = User.objects.filter(username__iexact=username).exists()

    return Response({
            "success": True,
            "available": not username_exists
        },
        status=200
    )


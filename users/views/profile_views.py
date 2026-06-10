from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):

    try:
        user = request.user
        if not user:
            return Response({"message": "User not found","success": False}, status=404)

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,

            "first_name": user.first_name,
            "last_name": user.last_name,

            "avatar": user.avatar,
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

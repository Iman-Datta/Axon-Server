from rest_framework.decorators import (api_view,permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User

from ..models import (Organization,OrganizationMember)
from ..permissions import (is_org_member,has_admin_permission)

def list_members(request, slug):
    try:
        organization = Organization.objects.get(slug = slug)

    except Organization.DoesNotExist:
        return Response({
            "success": False,
            "message": "Organization not found."
        }, status=404)
    
    if not is_org_member(request.user, organization):
        return Response({
            "success": False,
            "message": "You are not a member of this organization."
        },status=403)
    
    members = OrganizationMember.objects.filter(organization = organization)

    data = []

    for member in members:
        data.append({
            "id": member.id,
            "username": member.user.username,
            "email": member.user.email,
            "role": member.role,
            "joined_at": member.joined_at,
        })

    return Response({
        "success": True,
        "members": data
    },status=200)
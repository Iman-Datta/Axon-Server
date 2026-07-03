from rest_framework.decorators import (api_view,permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (Organization,OrganizationMember)
from ..permissions import (is_org_member,has_admin_permission, is_org_owner)
from ..serializers import OrganizationMemberSerializer, AddMemberSerializer, UpdateMemberRoleSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
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
    serializer = OrganizationMemberSerializer(members, many=True)

    return Response({
        "success": True,
        "members": serializer.data
    },status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_member(request, slug):
    try:
        organization = Organization.objects.get(slug = slug)

    except Organization.DoesNotExist:
        return Response({
            "success": False,
            "message": "Organization not found."
        }, status=404)
    
    if not has_admin_permission(request.user, organization):
        return Response({
            "success": False,
            "message": "Permission denied."
        },status=403)
    
    serializer = AddMemberSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)
    
    user = serializer.validated_data["username"]
    role = serializer.validated_data["role"]
    if (role != OrganizationMember.Role.MEMBER and not is_org_owner(request.user, organization)):
        return Response({
                "success": False,
                "message": "Only owner can add admin or owner."
            },status=403)
    
    already_member = OrganizationMember.objects.filter(organization = organization, user = user).exists()
    if already_member:
         return Response({
                "success": False,
                "message": "User already exists in organization."
            },status=400)
    
    member = OrganizationMember.objects.create(
        organization = organization,
        user = user,
        role = role,
    )

    return Response({
            "success": True,
            "message": "Member added successfully.",
            "member": OrganizationMemberSerializer(member).data
        },status=201)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_member_role(request, slug, member_id):
    try:
        organization = Organization.objects.get(slug = slug)
    except Organization.DoesNotExist:
        return Response({
            "success": False,
            "message": "Organization not found."
        }, status=404)
    
    if not is_org_owner(request.user, organization):
         return Response({
            "success": False,
            "message": "Only owner can change roles."
        },status=403)
    
    try:
        member = OrganizationMember.objects.get(id = member_id, organization = organization)
    except OrganizationMember.DoesNotExist:
        return Response({
                "success": False,
                "message": "Member not found."
            },status=404)

    serializer = UpdateMemberRoleSerializer(data = request.data)
    if not serializer.is_valid():
        return Response({
            "success": False,
            "errors": serializer.errors
        },status=400)
    
    new_role = serializer.validated_data["role"]
    if (member.role == OrganizationMember.Role.OWNER and new_role != OrganizationMember.Role.OWNER):
        owner_count = OrganizationMember.objects.filter(
            organization=organization,
            role=OrganizationMember.Role.OWNER
        ).count()

        if owner_count <= 1:
            return Response({
                    "success": False,
                    "message": "Organization must have at least one owner."
                },status=400)
        
    member.role = new_role
    member.save(update_fields=["role"])
    return Response({
        "success": True,
        "message": "Role updated successfully.",
        "member": OrganizationMemberSerializer(member).data
    },status=200)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_member(request, slug, member_id):
    try:
        organization = Organization.objects.get(slug=slug)
    except Organization.DoesNotExist:
        return Response({
            "success": False,
            "message": "Organization not found."
        }, status=404)

    try:
        member = OrganizationMember.objects.get(
            id=member_id,
            organization=organization
        )

    except OrganizationMember.DoesNotExist:
        return Response({
            "success": False,
            "message": "Member not found."
        }, status=404)

    if not is_org_owner(request.user,organization):
        return Response({
            "success": False,
            "message": "Only owner can remove members."
        }, status=403)

    if member.role == OrganizationMember.Role.OWNER:
        owner_count = OrganizationMember.objects.filter(organization=organization,role=OrganizationMember.Role.OWNER).count()        
        if owner_count == 1:
            return Response({
                "success": False,
                "message": "Organization must have at least one owner."
            }, status=400)

    member.delete()

    return Response({
        "success": True,
        "message": "Member removed successfully."
    }, status=200)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def leave_org(request, slug):
    try:
        organization = Organization.objects.get(slug = slug)
    except Organization.DoesNotExist:
        return Response({
            "success": False,
            "message": "Organization not found."
        }, status=404)
    
    try:
        member = OrganizationMember.objects.get(organization = organization, user = request.user)
    except OrganizationMember.DoesNotExist:
        return Response({
            "success": False,
            "message": "You are not a member of this organization."
        }, status=403)
    
    if member.role == OrganizationMember.Role.OWNER:
        owner_count = OrganizationMember.objects.filter(organization=organization,role=OrganizationMember.Role.OWNER).count()        
        if owner_count == 1:
            return Response({
                "success": False,
                "message": "Organization must have at least one owner."
            }, status=400)
        
    member.delete()
    return Response({
        "success": True,
        "message": "You left the organization successfully."
    }, status=200)
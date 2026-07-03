# TODO

from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..serializers.member import AddMemberSerializer, ProjectMemberListSerializer,UpdateMemberRoleSerializer
from ..decorators import resolve_project, resolve_workspace
from ..models import ProjectMember
from organizations.models import OrganizationMember
from organizations.permissions import get_org_member
from ..permissions import has_lead_permission,is_project_member

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def add_member(request, slug, project_slug):
    if not has_lead_permission(user = request.user, project = request.project):
        return Response({
            "success": False,
            "message": "You do not have permission to add members to this project."
        }, status=403)
    

    serializer = AddMemberSerializer(data=request.data,context={"project": request.project})

    if not serializer.is_valid():
        return Response({
            "success": False,
            "errors": serializer.errors,
        }, status=400)
    
    user = serializer.validated_data["username"]
    role = serializer.validated_data["role"]
    
    organization = request.workspace.organization
    if organization:
        if not OrganizationMember.objects.filter(organization=organization, user = user).exists():
            return Response({
                    "success": False,
                    "message": "User is not a member of this organization.",
                },status=403,)
    
    member = ProjectMember.objects.create(
        project=request.project,
        user=user,
        role=role,
    )

    return Response({
            "success": True,
            "message": "Member added successfully.",
            "member": {
                "username": member.user.username,
                "role": member.role,
                "joined_at": member.joined_at,
            },
        },status=201,)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def list_member(request, slug, project_slug):
    organization = request.workspace.organization
    if organization:
        if not get_org_member(request.user, organization):
            return Response({
                "success": False,
                "message": "User is not a member of this organization.",
            },status=403,)
    
    if not is_project_member(request.user, request.project):
        return Response({
            "success": False,
            "message": "User is not a member of this project.",
        },status=403,)
    
    members = ProjectMember.objects.select_related("user").filter(project=request.project)
    serializer = ProjectMemberListSerializer(members, many=True)
    
    return Response({
        "success": True,
        "members": serializer.data
    },status=200)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def update_member_role(request, slug, project_slug, member_id):
    organization = request.workspace.organization
    if organization:
        if not get_org_member(request.user, organization):
            return Response({
                    "success": False,
                    "message": "User is not a member of this organization.",
                },status=403,)

    requester = is_project_member(request.user, request.project)

    if requester is None:
        return Response({
                "success": False,
                "message": "User is not a member of this project.",
            }, status=403)

    try:
        member = ProjectMember.objects.get(id=member_id,project=request.project)
    except ProjectMember.DoesNotExist:
        return Response({
                "success": False,
                "message": "Member not found.",
            },status=404)
    
    serializer = UpdateMemberRoleSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
                "success": False,
                "errors": serializer.errors,
            },status=400)
    
    new_role = serializer.validated_data["role"]

    # Developers and Viewers cannot change roles
    if requester.role in [ProjectMember.Role.DEVELOPER,ProjectMember.Role.VIEWER]:    
        return Response({
                "success": False,
                "message": "You do not have permission to update roles.",
            },status=403,)
    
    # Lead cannot edit Owner or another Lead
    if requester.role == ProjectMember.Role.LEAD:

        if member.role in [ProjectMember.Role.OWNER,ProjectMember.Role.LEAD]:
            return Response({
                    "success": False,
                    "message": "Lead cannot modify this member.",
                },status=403)

        if new_role == ProjectMember.Role.LEAD:
            return Response({
                    "success": False,
                    "message": "Lead cannot promote members to Lead.",
                },status=403,)

    # Owner cannot demote themselves
    if (requester.user == member.user and requester.role == ProjectMember.Role.OWNER):
        return Response({
                "success": False,
                "message": "Owner cannot change their own role.",
            },status=400,)
    
    member.role = new_role
    member.save(update_fields=["role"])

    return Response({
            "success": True,
            "message": "Role updated successfully.",
            "member": {
                "username": member.user.username,
                "role": member.role,
            },
        },status=200,)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def remove_member(request, slug, project_slug, member_id):
    organization = request.workspace.organization
    if organization:
        if not get_org_member(request.user, organization):
            return Response({
                    "success": False,
                    "message": "User is not a member of this organization."
                },status=403)
        
    requester = is_project_member(request.user, request.project)

    if requester is None:
        return Response({
                "success": False,
                "message": "User is not a member of this project.",
            },status=403,)

    try:
        member = ProjectMember.objects.get(id=member_id,project=request.project)
    except ProjectMember.DoesNotExist:
        return Response({
                "success": False,
                "message": "Member not found.",
            },status=404)

    # Developer & Viewer cannot remove anyone
    if requester.role in [
        ProjectMember.Role.DEVELOPER,ProjectMember.Role.VIEWER]:
        return Response({
                "success": False,
                "message": "You do not have permission to remove members.",
            },status=403)

    # Lead restrictions
    if requester.role == ProjectMember.Role.LEAD:
        if member.role in [ProjectMember.Role.OWNER,ProjectMember.Role.LEAD,]:
            return Response({
                    "success": False,
                    "message": "Lead cannot remove this member.",
                },status=403)

    # Owner cannot remove themselves
    if (requester.user == member.user and requester.role == ProjectMember.Role.OWNER):
        return Response({
                "success": False,
                "message": "Project owner cannot remove themselves.",
            },status=400)

    # Project owner cannot be removed
    if member.role == ProjectMember.Role.OWNER:
        return Response({
                "success": False,
                "message": "Project owner cannot be removed.",
            },status=400)

    username = member.user.username
    member.delete()

    return Response({
            "success": True,
            "message": f"{username} removed successfully.",
        },status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def leave_project(request, slug, project_slug):

    organization = request.workspace.organization

    if organization:
        if not get_org_member(request.user, organization):
            return Response(
                {
                    "success": False,
                    "message": "User is not a member of this organization.",
                },
                status=403,
            )

    member = is_project_member(request.user, request.project)

    if member is None:
        return Response(
            {
                "success": False,
                "message": "User is not a member of this project.",
            },
            status=403,
        )

    if member.role == ProjectMember.Role.OWNER:
        return Response(
            {
                "success": False,
                "message": "Project owner cannot leave the project. Transfer ownership first.",
            },
            status=400,
        )

    member.delete()

    return Response(
        {
            "success": True,
            "message": "You have left the project successfully.",
        },
        status=200,
    )

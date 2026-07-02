from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..serializers.member import AddMemberSerializer, ProjectMemberListSerializer
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


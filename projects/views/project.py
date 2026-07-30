from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from ..serializers.project import ProjectCreateSerializer, ProjectListSerializer, ProjectDetailSerializer, ProjectUpdateSerializer
from ..decorators import resolve_workspace, resolve_project
from ..models import Project, ProjectMember
from organizations.permissions import has_admin_permission, get_org_member
from ..permissions import is_project_member
from users.models import Workspace


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@resolve_workspace
def create_project_view(request, slug):
    serializer = ProjectCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    workspace = request.workspace

    # Personal Workspace Permission
    if workspace.type == "personal":
        if workspace.owner != request.user:
            return Response({"message": "Permission denied."},status=403)

    # Organization Workspace Permission
    else:
        if not has_admin_permission(request.user,workspace.organization):
            return Response({"message": "Only organization admins can create projects."},status=403)
        

    with transaction.atomic():    
        project = Project.objects.create(
            workspace=workspace,
            created_by=request.user,
            **serializer.validated_data
        )

        ProjectMember.objects.create(
            project=project,
            user=request.user,
            role=ProjectMember.Role.OWNER
        )
    return Response({
            "message": "Project created successfully.",
            "project": {
                "id": project.id,
                "name": project.name,
                "slug": project.slug,
            }
        },status=201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
def my_projects_view(request, slug):
    workspace = request.workspace
    # Personal Workspace
    if workspace.type == workspace.Type.PERSONAL:
        projects = Project.objects.filter(
            workspace__type=Workspace.Type.PERSONAL,
            members__user=request.user,
            is_archived=False,
        ).select_related("workspace", "created_by").distinct()
        serializer = ProjectListSerializer(projects, many=True)
        return Response({
            "success": True,
            "projects": serializer.data,
        })

    else:
        if not get_org_member(request.user, workspace.organization):
            return Response({
                "success": False,
                "message": "User is not a member of this organization.",
            },status=403,)
        
        projects = (Project.objects.filter(workspace=workspace,is_archived=False,).select_related("created_by"))
        serializer = ProjectListSerializer(projects, many=True)

        return Response({
            "success": True,
            "message": "Projects fetched successfully.",
            "projects": serializer.data,
        },status=200,)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def project_detail_view(request, slug, project_slug):

    workspace = request.workspace

    # Personal Workspace
    if workspace.type == Workspace.Type.PERSONAL:
        if workspace.owner != request.user:
            return Response(
                {
                    "success": False,
                    "message": "Permission denied.",
                },
                status=403,
            )

    # Organization Workspace
    else:
        if not get_org_member(request.user, workspace.organization):
            return Response(
                {
                    "success": False,
                    "message": "User is not a member of this organization.",
                },
                status=403,
            )

    # Project Permission
    if not is_project_member(request.user, request.project):
        return Response(
            {
                "success": False,
                "message": "User is not a member of this project.",
            },
            status=403,
        )

    serializer = ProjectDetailSerializer(request.project)

    return Response(
        {
            "success": True,
            "message": "Project fetched successfully.",
            "project": serializer.data,
        },
        status=200,
    )

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def project_update_view(request, slug, project_slug):
    organization = request.workspace.organization

    # Organization permission
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

    if member.role != ProjectMember.Role.OWNER:
        return Response(
            {
                "success": False,
                "message": "Only the project owner can update the project.",
            },
            status=403,
        )

    serializer = ProjectUpdateSerializer(
        request.project,
        data=request.data,
        partial=True,
    )

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=400,
        )

    serializer.save()

    return Response(
        {
            "success": True,
            "message": "Project updated successfully.",
            "project": serializer.data,
        },
        status=200,
    )

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def delete_project(request, slug, project_slug):

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

    if member.role != ProjectMember.Role.OWNER:
        return Response(
            {
                "success": False,
                "message": "Only the project owner can delete the project.",
            },
            status=403,
        )

    request.project.is_archived = True
    request.project.save(update_fields=["is_archived"])

    return Response(
        {
            "success": True,
            "message": "Project archived successfully.",
        },
        status=200,
    )

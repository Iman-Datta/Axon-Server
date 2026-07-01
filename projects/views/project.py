from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from ..serializers.project import ProjectCreateSerializer, ProjectListSerializer, ProjectDetailSerializer
from ..decorators import resolve_workspace, resolve_project
from ..models import Project, ProjectMember
from organizations.permissions import has_admin_permission


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
@resolve_workspace
def list_projects_view(request, slug):
    workspace = request.workspace
    
    projects = (Project.objects.filter(workspace=workspace, is_archived=False).select_related("created_by"))

    serializer = ProjectListSerializer(projects, many=True)
    return Response({
                "message": "Projects fetched successfully.",
                "projects": serializer.data,
            },status=200)

@api_view(["GET"])
@resolve_workspace
@resolve_project
def project_detail_view(request, slug, project_slug):

    serializer = ProjectDetailSerializer(request.project)

    return Response(
        {
            "message": "Project fetched successfully.",
            "project": serializer.data,
        }
    )
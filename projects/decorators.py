from functools import wraps

from rest_framework.response import Response
from rest_framework import status

from users.models import User
from .models import Project
from organizations.models import Organization

def resolve_workspace(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        slug = kwargs.get("slug")
        if not slug:
            return Response({"message": "Workspace slug is required."},status=status.HTTP_400_BAD_REQUEST,)
                
        try:
            user = User.objects.select_related("workspace").get(username = slug)
            workspace = user.workspace
        except User.DoesNotExist:
            try:
                organization = Organization.objects.select_related("workspace").get(slug=slug)
                workspace = organization.workspace
            except Organization.DoesNotExist:
                return Response(
                    {
                        "message": "Workspace not found.",
                        "success": False,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
        request.workspace = workspace
        return view_func(request, *args, **kwargs)
    return wrapper

def resolve_project(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        project_slug = kwargs.get("project_slug")

        try:
            project = Project.objects.select_related(
                "workspace",
                "created_by",
            ).get(
                workspace=request.workspace,
                slug=project_slug,
                is_archived=False,
            )

        except Project.DoesNotExist:
            return Response(
                {
                    "message": "Project not found.",
                    "success": False,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        request.project = project

        return view_func(request, *args, **kwargs)

    return wrapper
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from users.decorators import github_connected
from ..decorators import resolve_project, resolve_workspace
from ..models import GitHubIntegration
from ..serializers.github import GitHubIntegrationSerializer, GitHubConnectSerializer

from projects.permissions import is_project_owner

from activity.services import log_activity
from activity.models import Activity

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@github_connected
def github_repo_view(request):
    user = request.user
    try:    
        response = requests.get(
            "https://api.github.com/user/repos",
            headers = {
                "Authorization": f"Bearer {user.github_access_token}",
                "Accept": "application/vnd.github+json",
            },
            params = {
                "visibility": "all",
                "affiliation": "owner,collaborator,organization_member",
                "sort": "updated",
                "per_page": 100,
            },
            timeout = 10,
        )
    except requests.RequestException:
        return Response({
                "success": False,
                "message": "Unable to connect to GitHub.",
            },status=503)
    
    if response.status_code == 401:
        return Response({
                "success": False,
                "message": "GitHub access token is invalid or expired. Please reconnect your GitHub account.",
            },status=400,)

    if response.status_code == 403:
        return Response({
                "success": False,
                "message": "GitHub denied the request. Please check your GitHub permissions or try again later.",
            },status=403)
    
    if response.status_code != 200:
        return Response({
            "success": False,
            "message": "Failed to fetch repositories from GitHub."
        },status=response.status_code)

    repositories = []

    for repo in response.json():
        repositories.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "private": repo["private"],
                "default_branch": repo["default_branch"],
            }
        )

    return Response({
        "success": True,
        "repositories": repositories,
    },status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
@github_connected
def github_connect_view(request, slug, project_slug):
    serializer = GitHubConnectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    repository_id = serializer.validated_data["repository_id"]

    try:
        response = requests.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {request.user.github_access_token}",
                "Accept": "application/vnd.github+json",
            },
            params={
                "visibility": "all",
                "affiliation": "owner,collaborator,organization_member",
                "sort": "updated",
                "per_page": 100,
            },
            timeout=10,
        )
    except requests.RequestException:
        return Response({
            "success": False,
            "message": "Unable to connect to GitHub.",
        },status=503)

    if response.status_code == 401:
        return Response({
            "success": False,
            "message": "GitHub access token is invalid or expired.",
        },status=401)

    if response.status_code != 200:
            return Response({
                "success": False,
                "message": "Failed to fetch repositories from GitHub."
            },status=response.status_code)

    selected_repo = None

    for repo in response.json():
        if repo["id"] == repository_id:
            selected_repo = repo
            break

    if not selected_repo:
        return Response({
            "success": False,
            "message": "Repository not found or access denied.",
        },status=404)

    with transaction.atomic:
        integration, created = GitHubIntegration.objects.update_or_create(
                project=request.project,
                defaults={
                    "created_by": request.user,
                    "repository_id": selected_repo["id"],
                    "repository_name": selected_repo["name"],
                    "repository_full_name": selected_repo["full_name"],
                    "default_branch": selected_repo["default_branch"],
                    "is_active": True,
                },
            )

        log_activity(
            project=request.project,
            verb=Activity.Verb.GITHUB_CONNECTED,
            actor=request.user,
            metadata={
                "repo_id": selected_repo["id"],
                "repo_name": selected_repo["name"],
                "repo_full_name": selected_repo["full_name"],
                "default_branch": selected_repo["default_branch"],
                "repo_url": selected_repo.get("html_url", ""),
            }
        )


    serializer = GitHubIntegrationSerializer(integration)
    return Response(
        {
            "success": True,
            "message": (
                "GitHub repository connected successfully."
                if created
                else "GitHub repository updated successfully."
            ),
            "integration": serializer.data,
        },
        status=200,
    )

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
@github_connected
def disconnect_github_view(request, slug, project_slug):
    try:
        integration = GitHubIntegration.objects.get(project=request.project)
    except GitHubIntegration.DoesNotExist:
        return Response({
            "success": False,
            "message": "No GitHub repository is connected to this project.",
        }, status=404)

    owner, repo = integration.repository_full_name.split("/")

    # Delete webhook from GitHub
    if integration.webhook_id:
        try:
            response = requests.delete(
                f"https://api.github.com/repos/{owner}/{repo}/hooks/{integration.webhook_id}",
                headers={
                    "Authorization": f"Bearer {request.user.github_access_token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10,
            )

            # Ignore if the webhook is already gone
            if response.status_code not in (204, 404):
                return Response({
                    "success": False,
                    "message": response.json().get(
                        "message",
                        "Failed to delete GitHub webhook.",
                    ),
                }, status=response.status_code)

        except requests.RequestException:
            return Response({
                "success": False,
                "message": "Unable to connect to GitHub.",
            }, status=503)

    with transaction.atomic():
        repo_name = integration.repository_name
        repo_full_name = integration.repository_full_name

        integration.delete()

        log_activity(
            project=request.project,
            verb=Activity.Verb.GITHUB_DISCONNECTED,
            actor=request.user,
            metadata={
                "repo_name": repo_name,
                "repo_full_name": repo_full_name,
            }
        )

    return Response({
        "success": True,
        "message": "GitHub repository disconnected successfully.",
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def github_integration_status_view(request, slug, project_slug):
    has_access = bool(is_project_owner(request.user, request.project))
    
    github_connected = False
    github_token_expired = False

    if request.user.github_access_token:
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {request.user.github_access_token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=5,
            )

            if response.status_code == 200:
                github_connected = True
            elif response.status_code == 401:
                github_token_expired = True

        except requests.RequestException:
            pass
    integration = GitHubIntegration.objects.filter(project = request.project).first()
    if integration is None:
        return Response({
            "success": True,
            "access" : has_access,
            "github_connected": github_connected,
            "github_token_expired" : github_token_expired,
            "repository_connected": False,
            "webhook_connected": False,
            "integration": None,
        }, status=200)

    return Response({
        "success": True,
        "access" : has_access,
        "github_connected": github_connected,
        "github_token_expired": github_token_expired,
        "repository_connected": True,
        "webhook_connected": bool(integration.webhook_id),
        "integration": {
            "repository_name": integration.repository_name,
            "repository_full_name": integration.repository_full_name,
            "default_branch": integration.default_branch,
            "webhook_id": integration.webhook_id,
        }
    }, status=200)

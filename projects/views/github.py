import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.decorators import github_connected
from ..decorators import resolve_project, resolve_workspace
from ..models import GitHubIntegration
from ..serializers.github import GitHubIntegrationSerializer, GitHubConnectSerializer

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
            },status=401,)

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
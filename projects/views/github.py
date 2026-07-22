import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.decorators import github_connected

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
import requests
import secrets

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

from users.decorators import github_connected
from ..decorators import resolve_project, resolve_workspace
from ..models import GitHubIntegration
from ..serializers.github import GitHubIntegrationSerializer, GitHubConnectSerializer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
@github_connected
def create_github_webhook_view(request, slug, project_slug):
    try:
        integration = GitHubIntegration.objects.get(project=request.project)
    except GitHubIntegration.DoesNotExist:
        return Response({
            "success": False,
            "message": "No GitHub repository connected.",
        },status=404)

    if integration.webhook_id:
        return Response({
            "success": False,
            "message": "Webhook already exists."
        },status=400)

    webhook_secret = secrets.token_hex(32)

    owner, repo = integration.repository_full_name.split("/")

    try:
        response = requests.post(f"https://api.github.com/repos/{owner}/{repo}/hooks",
            headers={
                    "Authorization": f"Bearer {request.user.github_access_token}",
                    "Accept": "application/vnd.github+json",
                },
            json={
                "name": "web",
                "active": True,
                "events" : [
                    "push",
                    "pull_request",
                ],
                "config" : {
                    "url": settings.GITHUB_WEBHOOK_URL,
                    "content_type": "json",
                    "secret": webhook_secret,
                    "insecure_ssl": "0",
                }
            },
            timeout=10,
        )
    except requests.RequestException:
        return Response({
                "success": False,
                "message": "Unable to connect to GitHub.",
            },status=503)
    
    if response.status_code != 201:
        return Response({
                "success": False,
                "message": response.json().get("message", "Failed to create webhook."),
            },status=response.status_code)

    data = response.json()

    integration.webhook_secret = webhook_secret
    integration.webhook_id = data["id"]
    integration.save(update_fields=["webhook_id", "webhook_secret"])
    
    return Response({
        "success": True,
        "message": "Webhook created successfully.",
        "webhook_id": integration.webhook_id,
    })
import requests
import secrets
import hashlib
import hmac

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

from users.decorators import github_connected
from ..decorators import resolve_project, resolve_workspace
from ..models import GitHubIntegration
from ..serializers.github import GitHubIntegrationSerializer, GitHubConnectSerializer

from tickets.services import handle_pull_request_closed,handle_pull_request_opened,handle_push_event,handle_create_event

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
                    "create",
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

@api_view(["POST"])
def github_webhook_view(request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return Response({
                "success": False,
                "message": "Missing GitHub signature.",
            },status=401)

    event = request.headers.get("X-GitHub-Event")
    if not event:
        return Response({
                "success": False,
                "message": "Missing GitHub event.",
            },status=400)
    
    raw_body = request.body

    payload = request.data

    repository = payload.get("repository", {})
    repository_full_name = repository.get("full_name")

    if not repository_full_name:
        return Response({
            "success": False,
            "message": "Repository information missing.",
        },status=400)

    try:
        integration = GitHubIntegration.objects.select_related("project").get(repository_full_name=repository_full_name) 
    except GitHubIntegration.DoesNotExist:
        return Response({
            "success": False,
            "message": "Repository is not connected to Axon.",
        },status=404)

    if not integration.webhook_secret:
        return Response({
            "success": False,
            "message": "Webhook secret not configured.",
        },status=500)

    expected_signature = (
        "sha256=" +
        hmac.new(
            key=integration.webhook_secret.encode(),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
    )
    if not hmac.compare_digest(signature, expected_signature):
        return Response({
                "success": False,
                "message": "Invalid GitHub signature.",
            },status=403)

    if event == "ping":
        return Response({
                "success": True,
                "message": "GitHub webhook verified."
            },status=200)
    
    if event == "create":
        handle_create_event(integration, payload)
    elif event == "push":
        handle_push_event(integration,payload)
    elif event == "pull_request":
        action = payload.get("action")
        if action == "opened":
            handle_pull_request_opened(integration, payload)
        elif action == "closed":
            handle_pull_request_closed(integration, payload)
    return Response({"success": True},status=200)

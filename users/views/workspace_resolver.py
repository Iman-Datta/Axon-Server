from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.decorators import resolve_workspace
from organizations.models import OrganizationMember


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
def workspace_detail_view(request, slug):
    workspace = request.workspace

    return Response({
            "success": True,
            "workspace": {
                "slug": slug,
                "type": workspace.type,
            },},status=200,)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_workspaces(request):
    user = request.user
    workspaces = [
        {
            "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "slug": user.username,
            "type": "personal",
            "avatar": user.avatar,
        }
    ]

    memberships = OrganizationMember.objects.filter(user=user).select_related('organization')

    for membership in memberships:
        org = membership.organization
        workspaces.append({
            "name": org.name,
            "slug": org.slug,
            "type": "organization",
            "avatar": org.avatar,
        })


    return Response({
        "success": True,
        "workspaces": workspaces
    })
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.decorators import resolve_workspace


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
def workspace_detail_view(request, slug):
    workspace = request.workspace

    return Response(
        {
            "success": True,
            "type": workspace.type,
        }
    )
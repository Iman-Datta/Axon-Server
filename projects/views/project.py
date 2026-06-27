from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..serializers.project import ProjectCreateSerializer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def project_personal_create_view(request):
    user = request.user
    serializer = ProjectCreateSerializer(
        data = request.data,
        context = {
            "user" :  user,
        }
    )

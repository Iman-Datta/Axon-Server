from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Epic

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_epic(request):
    pass
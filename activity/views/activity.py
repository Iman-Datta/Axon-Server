from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ..models import Ticket, Activity
from ..serializers import TicketActivitySerializer
from projects.permissions import is_project_member
from projects.decorators import resolve_workspace, resolve_project

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def ticket_activity_list(request, slug, project_slug, ticket_id):
    if not is_project_member(request.user, request.project):
        return Response({"success": False, "message": "Permission denied."}, status=403)

    try:
        ticket = Ticket.objects.get(id=ticket_id, project=request.project)
    except Ticket.DoesNotExist:
        return Response({"success": False, "message": "Ticket not found."}, status=404)

    activities = Activity.objects.filter(
        project=request.project,
        ticket=ticket
    ).select_related("actor").order_by("-created_at")

    paginator = StandardResultsSetPagination()
    paginated_activities = paginator.paginate_queryset(activities, request)
    serializer = TicketActivitySerializer(paginated_activities, many=True)

    return paginator.get_paginated_response({
        "success": True,
        "results": serializer.data
    })
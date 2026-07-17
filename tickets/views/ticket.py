from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.decorators import resolve_project, resolve_workspace
from projects.permissions import has_developer_permission, has_lead_permission, is_project_member
from projects.models import ProjectMember

from ..models import Ticket
from ..serializers.ticket import TicketSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def create_ticket(request, slug, project_slug):
    if not has_developer_permission(request.user, request.project):
        return Response({"success": False, "message": "Permission denied."}, status=403)

    serializer = TicketSerializer(
        data=request.data,
        context={
            "project": request.project,
            "user": request.user,
        }
    )

    if not serializer.is_valid():
        return Response({"success": False, "errors": serializer.errors}, status=400)

    ticket = serializer.save()

    return Response({
        "success": True,
        "message": "Ticket created successfully.",
        "ticket": TicketSerializer(ticket).data
    }, status=201)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def update_ticket(request, slug, project_slug, ticket_id):
    if not has_developer_permission(request.user, request.project):
        return Response({"success": False, "message": "Permission denied."}, status=403)

    try:
        ticket = Ticket.objects.get(id=ticket_id, project=request.project)
    except Ticket.DoesNotExist:
        return Response({"success": False, "message": "Ticket not found."}, status=404)

    serializer = TicketSerializer(
        ticket,
        data=request.data,
        partial=True,
        context={
            "project": request.project,
            "user": request.user,
        }
    )

    if not serializer.is_valid():
        return Response({"success": False, "errors": serializer.errors}, status=400)

    serializer.save()

    return Response({
        "success": True,
        "message": "Ticket updated successfully.",
        "ticket": serializer.data
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def list_tickets(request, slug, project_slug):
    if not is_project_member(request.user, request.project):
        return Response({"success": False, "message": "You are not a member of this project."}, status=403)

    tickets = Ticket.objects.filter(project=request.project)

    status_filter = request.query_params.get("status")
    epic_filter = request.query_params.get("epic")
    column_filter = request.query_params.get("column")

    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if epic_filter:
        tickets = tickets.filter(epic_id=epic_filter)
    if column_filter:
        tickets = tickets.filter(kanban_column = column_filter)

    serializer = TicketSerializer(tickets, many=True)

    return Response({
        "success": True,
        "count": tickets.count(),
        "tickets": serializer.data
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def retrieve_ticket(request, slug, project_slug, ticket_id):
    if not is_project_member(request.user, request.project):
        return Response({"success": False, "message": "You are not a member of this project."}, status=403)

    try:
        ticket = Ticket.objects.get(id=ticket_id, project=request.project)
    except Ticket.DoesNotExist:
        return Response({"success": False, "message": "Ticket not found."}, status=404)

    serializer = TicketSerializer(ticket)

    return Response({
        "success": True,
        "ticket": serializer.data
    }, status=200)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def delete_ticket(request, slug, project_slug, ticket_id):

    if not has_lead_permission(request.user, request.project):
        return Response({"success": False, "message": "Permission denied."}, status=403)

    try:
        ticket = Ticket.objects.get(id=ticket_id, project=request.project)
    except Ticket.DoesNotExist:
        return Response({"success": False, "message": "Ticket not found."}, status=404)

    ticket.delete()

    return Response({
        "success": True,
        "message": "Ticket deleted successfully."
    }, status=200)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def assign_ticket(request, slug, project_slug, ticket_id):
    if not has_lead_permission(request.user, request.project):
        return Response({"success": False, "message": "Permission denied."}, status=403)

    try:
        ticket = Ticket.objects.get(id=ticket_id, project=request.project)
    except Ticket.DoesNotExist:
        return Response({"success": False, "message": "Ticket not found."}, status=404)

    assignee_id = request.data.get("assignee")

    if assignee_id is None:
        ticket.assignee = None
        ticket.save()

        return Response({
            "success": True,
            "message": "Ticket unassigned successfully.",
            "ticket": TicketSerializer(ticket).data,
        }, status=200)

    try:
        member = ProjectMember.objects.get(
            project=request.project,
            user_id=assignee_id,
        )
    except ProjectMember.DoesNotExist:
        return Response({
            "success": False,
            "message": "Selected user is not a project member."
        }, status=400)

    ticket.assignee = member.user
    ticket.save()

    return Response({
        "success": True,
        "message": "Ticket assigned successfully.",
        "ticket": TicketSerializer(ticket).data,
    }, status=200)
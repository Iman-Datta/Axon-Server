from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db import transaction

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

    tickets = Ticket.objects.filter(project=request.project).order_by("-created_at")

    status_filter = request.query_params.get("status")
    epic_filter = request.query_params.get("epic")
    column_filter = request.query_params.get("column")
    assignee_filter = request.query_params.get("assignee")
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if epic_filter:
        tickets = tickets.filter(epic_id=epic_filter)
    if column_filter:
        tickets = tickets.filter(kanban_column=column_filter)
        
    if assignee_filter:
        if assignee_filter == "me":
            tickets = tickets.filter(assignee=request.user)
        else:
            tickets = tickets.filter(assignee_id=assignee_filter)

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

    # Unassign if no ID is sent
    if not assignee_id:
        ticket.assignee = None
        ticket.save()

        return Response({
            "success": True,
            "message": "Ticket unassigned successfully.",
            "ticket": TicketSerializer(ticket).data,
        }, status=200)

    # Search ProjectMember by Primary Key (id), NOT user!
    try:
        member = ProjectMember.objects.get(id=assignee_id, project=request.project)
    except ProjectMember.DoesNotExist:
        return Response({
            "success": False,
            "message": "Selected user is not a project member."
        }, status=400)

    # Successfully assign the actual user attached to that member row
    ticket.assignee = member.user
    ticket.save()

    return Response({
        "success": True,
        "message": "Ticket assigned successfully.",
        "ticket": TicketSerializer(ticket).data,
    }, status=200)

# TODO
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def update_board(request, slug, project_slug):
    if not has_developer_permission(request.user, request.project):
        return Response({
                "success": False,
                "message": "Permission denied."
            },status=403)

    tickets = request.data.get("tickets")

    if not isinstance(tickets, list):
        return Response({
                "success": False,
                "message": "Invalid payload. 'tickets' must be a list."
            },status=400)

    with transaction.atomic():
        for item in tickets:

            required_fields = ["id", "kanban_column", "order"]

            for field in required_fields:
                if field not in item:
                    return Response({
                            "success": False,
                            "message": f"'{field}' is required."
                        },status=400)

            try:
                ticket = Ticket.objects.get(id=item["id"],project=request.project,)
            except Ticket.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": f"Ticket with id {item['id']} not found."
                    },status=404)

            ticket.kanban_column = item["kanban_column"]
            ticket.order = item["order"]

            ticket.save(
                update_fields=[
                    "kanban_column",
                    "order",
                ]
            )

    return Response({
            "success": True,
            "message": "Kanban board updated successfully."
        },status=200)

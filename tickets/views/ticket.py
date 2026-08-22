from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db import transaction

from projects.decorators import resolve_project, resolve_workspace
from projects.permissions import has_developer_permission, has_lead_permission, is_project_member
from projects.models import ProjectMember

from ..models import Ticket
from ..serializers.ticket import TicketSerializer

from activity.services import log_activity
from activity.models import Activity


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

    with transaction.atomic():
        ticket = serializer.save()

        log_activity(
            project=request.project,
            ticket=ticket,
            verb=Activity.Verb.TICKET_CREATED,
            actor=request.user,
            metadata={
                "ticket_number": ticket.ticket_number,
                "ticket_title": ticket.title,
                "priority": ticket.priority,
            }
        )

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

    # 1. Capture old state before saving changes
    old_status = ticket.status
    

    with transaction.atomic():
        # 2. Save updated ticket instance
        updated_ticket = serializer.save()

        # 3. Log Status change if modified
        if old_status != updated_ticket.status:
            log_activity(
                project=request.project,
                ticket=updated_ticket,
                actor=request.user,
                verb=Activity.Verb.TICKET_STATUS_CHANGED,
                metadata={
                    "ticket_number": updated_ticket.ticket_number,
                    "ticket_title": updated_ticket.title,
                    "old_status": old_status,
                    "new_status": updated_ticket.status,
                }
            )

    return Response({
        "success": True,
        "message": "Ticket updated successfully.",
        "ticket": TicketSerializer(updated_ticket).data
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def list_tickets(request, slug, project_slug):
    if not is_project_member(request.user, request.project):
        return Response({"success": False, "message": "You are not a member of this project."}, status=403)

    edit_access = bool(has_developer_permission(request.user, request.project))

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
        "tickets": serializer.data,
        "can_edit": edit_access
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
    new_assignee_user = None

    if assignee_id:
        try:
            member = ProjectMember.objects.get(id=assignee_id, project=request.project)
            new_assignee_user = member.user
        except ProjectMember.DoesNotExist:
            return Response({
                "success": False,
                "message": "Selected user is not a project member."
            }, status=400)

    # Capture previous assignee details
    old_assignee_name = (
        ticket.assignee.get_full_name() or ticket.assignee.username
        if ticket.assignee else None
    )
    old_assignee_id = ticket.assignee.id if ticket.assignee else None

    with transaction.atomic():
        ticket.assignee = new_assignee_user
        ticket.save()

        new_assignee_name = (
            new_assignee_user.get_full_name() or new_assignee_user.username
            if new_assignee_user else None
        )
        
        verb = Activity.Verb.TICKET_ASSIGNED if new_assignee_user else Activity.Verb.TICKET_UNASSIGNED

        log_activity(
            project=request.project,
            ticket=ticket,
            actor=request.user,
            verb=verb,
            target_user=new_assignee_user,
            metadata={
                "ticket_number": ticket.ticket_number,
                "ticket_title": ticket.title,
                "old_assignee_id": old_assignee_id,
                "old_assignee_name": old_assignee_name,
                "new_assignee_id": new_assignee_user.id if new_assignee_user else None,
                "new_assignee_name": new_assignee_name,
            }
        )

    return Response({
        "success": True,
        "message": "Ticket assigned successfully." if new_assignee_user else "Ticket unassigned successfully.",
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
        }, status=403)

    tickets = request.data.get("tickets")

    if not isinstance(tickets, list):
        return Response({
            "success": False,
            "message": "Invalid payload. 'tickets' must be a list."
        }, status=400)

    with transaction.atomic():
        for item in tickets:
            required_fields = ["id", "kanban_column", "order"]

            for field in required_fields:
                if field not in item:
                    return Response({
                        "success": False,
                        "message": f"'{field}' is required."
                    }, status=400)

            try:
                ticket = Ticket.objects.get(id=item["id"], project=request.project)
            except Ticket.DoesNotExist:
                return Response({
                    "success": False,
                    "message": f"Ticket with id {item['id']} not found."
                }, status=404)

            # 1. Capture old column before saving changes
            old_column = ticket.kanban_column
            new_column = item["kanban_column"]

            # 2. Update values
            ticket.kanban_column = new_column
            ticket.order = item["order"]

            ticket.save(update_fields=["kanban_column", "order"])

            # 3. Log activity ONLY if the column actually changed
            if old_column != new_column:
                log_activity(
                    project=request.project,
                    ticket=ticket,
                    actor=request.user,
                    verb=Activity.Verb.TICKET_COLUMN_CHANGED,
                    metadata={
                        "ticket_number": ticket.ticket_number,
                        "ticket_title": ticket.title,
                        "old_column": old_column,
                        "new_column": new_column,
                    }
                )

    return Response({
        "success": True,
        "message": "Kanban board updated successfully."
    }, status=200)
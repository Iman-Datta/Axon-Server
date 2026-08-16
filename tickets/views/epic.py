from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from projects.permissions import has_lead_permission, is_project_member, is_project_owner
from projects.decorators import resolve_project,resolve_workspace
from ..serializers.epic import EpicSerializer, EpicDetailsSerializer
from ..models import Epic, Ticket


from django.db.models import Count, Q

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def create_epic(request, slug, project_slug):
    if not has_lead_permission(request.user, request.project):
        return Response({
            "success": False,
            "message": "Permission denied.",
        },status=403)

    serializer = EpicSerializer(
        data=request.data,
        context={
            "project": request.project,
            "user": request.user,
        },
    )

    serializer.is_valid(raise_exception=True)
    epic = serializer.save()

    # Fetch the created epic with annotations
    epic = (
        Epic.objects.filter(
            id=epic.id,
            project=request.project,
        )
        .annotate(
            ticket_count=Count("tickets"),
            completed_count=Count(
                "tickets",
                filter=Q(
                    tickets__kanban_column=Ticket.KanbanColumn.DONE,
                ),
            ),
        )
        .first()
    )

    response_serializer = EpicSerializer(
        epic,
        context={
            "project": request.project,
            "user": request.user,
        },
    )

    return Response({
        "success": True,
        "message": "Epic created successfully.",
        "epic": response_serializer.data,
    },status=201)
    
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def update_epic(request, slug, project_slug, epic_id):
    if not has_lead_permission(request.user, request.project):
        return Response({
            "success": False,
            "message": "Permission denied.",
        },status=403)

    try:
        epic = Epic.objects.get(id=epic_id,project=request.project,)
    except Epic.DoesNotExist:
        return Response({
            "success": False,
            "message": "Epic not found.",
        },status=404)

    serializer = EpicSerializer(
        epic,
        data=request.data,
        partial=True,
        context={
            "project": request.project,
            "user": request.user,
        },
    )

    if not serializer.is_valid():
        return Response({
            "success": False,
            "errors": serializer.errors,
        },status=400)

    serializer.save()

    # Fetch again with annotations
    epic = (
        Epic.objects.filter(
            id=epic_id,
            project=request.project,
        )
        .annotate(
            ticket_count=Count("tickets"),
            completed_count=Count(
                "tickets",
                filter=Q(
                    tickets__kanban_column=Ticket.KanbanColumn.DONE,
                ),
            ),
        )
        .first()
    )

    response_serializer = EpicSerializer(
        epic,
        context={
            "project": request.project,
            "user": request.user,
        },
    )

    return Response({
        "success": True,
        "message": "Epic updated successfully.",
        "epic": response_serializer.data,
    },status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def list_epics(request, slug, project_slug):
    if not is_project_member(request.user, request.project):
        return Response({
                "success": False,
                "message": "You are not a member of this project."
            },status=403)
    edit_access = bool(has_lead_permission(request.user, request.project))
    print(edit_access)
    
    epics = (
        Epic.objects.filter(project=request.project)
        .annotate(
            ticket_count=Count("tickets"),
            completed_count =Count(
                "tickets",
                filter=Q(tickets__kanban_column=Ticket.KanbanColumn.DONE),
            ),
        )
    )
    

    serializer = EpicSerializer(epics,many=True,)
    return Response({
        "success": True,
        "count": epics.count(),
        "epics": serializer.data,
        "can_edit": edit_access,
    },status=200)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def delete_epic(request, slug, project_slug, epic_id):

    if not is_project_owner(request.user, request.project):
        return Response({
            "success": False,
            "message": "Only the project owner can delete an epic."
        },status=403,)
    
    try:
        epic = Epic.objects.get(id=epic_id,project=request.project,)
    except Epic.DoesNotExist:
        return Response({
                "success": False,
                "message": "Epic not found."
            },status=404)
    epic.delete()

    return Response({
            "success": True,
            "message": "Epic deleted successfully."
        },status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
@resolve_project
def epic_details_view(request, slug, project_slug, epic_id):
    if not is_project_member(request.user, request.project):
        return Response(
            {
                "success": False,
                "message": "You do not have permission to view this epic.",
            },
            status=403,
        )

    try:
        epic = (
            Epic.objects.filter(
                id=epic_id,
                project=request.project,
            )
            .annotate(
                ticket_count=Count("tickets"),
                completed_count=Count(
                    "tickets",
                    filter=Q(
                        tickets__kanban_column=Ticket.KanbanColumn.DONE
                    ),
                ),
            )
            .prefetch_related(
                "tickets__assignee",
            )
            .get()
        )

    except Epic.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Epic not found.",
            },
            status=404,
        )

    serializer = EpicDetailsSerializer(
        epic,
        context={"project": request.project},
    )

    return Response(
        {
            "success": True,
            "epic": serializer.data,
        }
    )

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from projects.permissions import has_lead_permission, is_project_member, is_project_owner
from projects.decorators import resolve_project
from ..serializers.epic import EpicSerializer
from ..models import Epic


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@resolve_project
def create_epic(request):    
    if not has_lead_permission(request.user, request.project):
        return Response({
            "success": False,
            "message": "Permission denied."
            },status=403)

    serializer = EpicSerializer(
        data = request.data,
         context={
        "project": request.project,
        "user": request.user,
        }
    )

    serializer.is_valid(raise_exception=True)
    epic = serializer.save()
    serializer = EpicSerializer(epic) 

    return Response({
        "success": True,
        "message": "Epic created successfully.",
        "epic": serializer.data
    }, status=201)
    
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@resolve_project
def update_epic(request, epic_id):
    if not has_lead_permission(request.user, request.project):
        return Response({
                "success": False,
                "message": "Permission denied."
            },status=403,)
    
    try:
        epic = Epic.objects.get(id=epic_id,project=request.project,)
    except Epic.DoesNotExist:
        return Response({
                "success": False,
                "message": "Epic not found."
            },status=404,)

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
            }, status=400,)

    serializer.save()

    return Response({
            "success": True,
            "message": "Epic updated successfully.",
            "epic": serializer.data,
        },status=200,)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_project
def list_epics(request):
    if not is_project_member(request.user, request.project):
        return Response({
                "success": False,
                "message": "You are not a member of this project."
            },status=403)
    
    epics = Epic.objects.filter(project=request.project).order_by("name")

    serializer = EpicSerializer(epics,many=True,)
    return Response({
            "success": True,
            "count": epics.count(),
            "epics": serializer.data,
        },status=200)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@resolve_project
def delete_epic(request, epic_id):

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
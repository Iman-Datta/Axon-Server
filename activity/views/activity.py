from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models import Activity


@api_view(["GET"])
def get_all_activities(request):
    activities = Activity.objects.all()

    data = []

    for activity in activities:
        data.append({
            "id": activity.id,
            "actor": activity.actor_id,
            "action": activity.action,
            "created_at": activity.created_at,
        })

    return Response(data, status=status.HTTP_200_OK)
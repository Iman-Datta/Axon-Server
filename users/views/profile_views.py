from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from ..models import User
from ..serializers import UsernameUpdateSerializer, UsernameSerializer, CompleteProfileSerializer,PublicProfileSerializer, MeSerializer, UpdateProfileSerializer, UserProfileOverviewSerializer, MyWorkTicketSerializer

from tickets.models import Ticket
from organizations.models import OrganizationMember

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    serializer = MeSerializer(request.user)

    return Response(
        {
            "success": True,
            "user": serializer.data,
        },
        status=200,
    )

@api_view(["GET"])
def check_username_view(request):
    serializer = UsernameSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=400
        )
    username = serializer.validated_data["username"]
    
    username_exists = User.objects.filter(username__iexact=username).exists()
    return Response({
            "success": True,
            "available": not username_exists
        },
        status=200
    )

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_username_view(request):
    user = request.user

    serializer = UsernameUpdateSerializer(data=request.data, context={"user": user})

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=400
        )

    user.username = serializer.validated_data["username"]
    user.is_username_set = True
    user.save(update_fields=["username","is_username_set"])

    return Response({
        "success": True,
        "message": "Username updated successfully.",
        "user": MeSerializer(user).data
    },status=200)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def complete_profile_view(request):

    user = request.user
    # identity must be completed first
    if (
        not user.is_username_set
        or not user.is_email_verified
    ):

        return Response(
            {
                "success": False,
                "message": "Complete identity setup first."
            },
            status=400
        )

    serializer = CompleteProfileSerializer(
        user,
        data=request.data,
        partial=True
    )

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=400
        )

    if not (user.first_name or serializer.validated_data.get("first_name")) or not  (user.last_name or serializer.validated_data.get("last_name")):
        return Response(
            {
                "success": False,
                "message": "First name and last name required."
            },
            status=400
        )

    serializer.save()

    return Response(
        {
            "success": True,
            "message": "Profile completed successfully."
        },
        status=200
    )

@api_view(["GET"])
def public_profile_view(request,username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"message":"User not found"},status=404)

        serializer = PublicProfileSerializer(user)

        return Response({
            "success": True,
            "data": serializer.data
        },status=200)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    user = request.user

    serializer = UpdateProfileSerializer(
        instance=user,
        data=request.data,
        partial=True,
    )

    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=400
        )

    serializer.save()

    if not user.is_profile_completed:
        user.is_profile_completed = True
        user.save(update_fields=["is_profile_completed"])

    return Response({
            "success": True,
            "user": UpdateProfileSerializer(user).data,
        },status=200
    )

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile_password_view(request):
    user = request.user

    new_password = request.data.get("new_password")

    if not new_password:
        return Response({
            "success": False,
            "message": "New password is required.",
        },status=400)
            
    try:
        validate_password(new_password, user)
    except ValidationError as error:
        return Response({
            "success": False,
            "message": error.messages,
        },status=400)
        

    user.set_password(new_password)
    user.save(update_fields=["password"])

    return Response({
        "success": True,
        "message": "Password updated successfully.",
    },status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_overview(request):
    user = request.user

    # 1. Global Assigned Tickets across all projects/organizations
    assigned_tickets = Ticket.objects.filter(assignee=user).select_related(
        "project", "project__workspace", "epic"
    ).order_by("-updated_at")

    # 2. Connected Organizations (Memberships)
    organizations = OrganizationMember.objects.filter(user=user).select_related(
        "organization"
    ).order_by("-joined_at")

    # 3. Subtle Ticket Metrics Summary
    total_assigned = assigned_tickets.count()
    completed_tickets = assigned_tickets.filter(status="DONE").count()
    in_progress_tickets = assigned_tickets.filter(kanban_column="IN_PROGRESS").count()
    
    completion_rate = (
        round((completed_tickets / total_assigned) * 100) if total_assigned > 0 else 0
    )

    metrics = {
        "total_assigned": total_assigned,
        "completed": completed_tickets,
        "in_progress": in_progress_tickets,
        "completion_rate": completion_rate,
    }

    # Package data together
    data = {
        "assigned_tickets": assigned_tickets,
        "organizations": organizations,
        "metrics": metrics,
    }

    serializer = UserProfileOverviewSerializer(data)
    
    return Response({
        "success": True,
        "profile": serializer.data
    }, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_work_tickets(request):
    user = request.user

    # Fetch all tickets assigned to the user, optimized with select_related
    tickets = Ticket.objects.filter(assignee=user).select_related(
        "project", "project__workspace", "epic"
    ).order_by("-updated_at")

    serializer = MyWorkTicketSerializer(tickets, many=True)

    # Optional metadata or status summary for the My Work header
    total_count = tickets.count()
    completed_count = tickets.filter(status="DONE").count()
    open_count = total_count - completed_count

    return Response({
        "success": True,
        "count": total_count,
        "summary": {
            "open": open_count,
            "completed": completed_count,
        },
        "tickets": serializer.data
    }, status=200)
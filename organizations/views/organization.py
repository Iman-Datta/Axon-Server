from django.db.models import Count, Q
from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..serializers import OrganizationSerializer, OrganizationDetailSerializer, OrganizationProjectSummarySerializer
from ..models import Organization
from ..permissions import has_admin_permission, is_org_owner
from projects.decorators import resolve_workspace, resolve_project
from users.models import Workspace
from tickets.models import Ticket
from projects.models import Project

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_org(request):
    serializer = OrganizationSerializer(
        data = request.data,
        context = {
            "user" :  request.user
        }
    )

    if not serializer.is_valid():
        return Response({
            "success": False,
            "errors": serializer.errors
        },status=400)
    
    organization = serializer.save()
    
    return Response({
        "success": True,
        "message": "Organization created successfully.",
        "organization": OrganizationSerializer(organization).data
    }, status=201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_org(request):
    organizations = Organization.objects.filter(members__user = request.user) # Find Organizations whose members contain this user.

    serializer = OrganizationSerializer(
        organizations,
        many = True,
    )

    return Response({
            "success": True,
            "organizations": serializer.data
        },
        status=200
    )

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_org(request, slug):
    try:
        organization = Organization.objects.get(
            slug = slug,
            members__user=request.user
        )
    except Organization.DoesNotExist:
        return Response({
            "success": False,
            "message": "Organization not found."
        }, status=400)

    if not has_admin_permission(request.user, organization):
        return Response({
                "success": False,
                "message": "Permission denied."
            },status=403)
    
    serializer = OrganizationSerializer(
        organization,
        data = request.data,
        partial = True
    )

    if not serializer.is_valid():
        return Response ({
            "success": False,
            "errors": serializer.errors
        }, status=400)
    
    serializer.save()
    return Response({
            "success": True,
            "message": "Organization updated successfully.",
            "organization": serializer.data
        },
        status=200
    )

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_org(request, slug):
    try:
        organization = Organization.objects.get(
            slug=slug
        )

    except Organization.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Organization not found."
            },
            status=404
        )

    if not is_org_owner(request.user, organization):
        return Response({
                "success": False,
                "message": "Permission denied."
            },status=403)
        
    organization.delete()

    return Response(
        {
            "success": True,
            "message": "Organization deleted successfully."
        },
        status=200
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
def org_detail_view(request, slug):
    workspace = request.workspace

    if workspace.type == Workspace.Type.PERSONAL:
        return Response(
            {
                "success": False,
                "message": "Organization not found.",
            },
            status=404,
        )

    organization = workspace.organization

    serializer = OrganizationDetailSerializer(
        organization,
        context={"request": request},
    )

    return Response(
        {
            "success": True,
            "message": "Organization fetched successfully.",
            "organization": serializer.data,
        },
        status=200,
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@resolve_workspace
def organization_overview(request, slug):
    workspace = request.workspace

    # 1. Query projects and tickets using request.workspace
    projects = Project.objects.filter(workspace=workspace)
    tickets = Ticket.objects.filter(project__workspace=workspace)

    # 2. Top-level metrics
    total_projects = projects.count()
    
    # Check how your workspace relates to members (adjust if field name differs)
    org = request.workspace.organization # or however you access the organization from workspace
    total_members = org.members.count() # Or OrganizationMembership.objects.filter(organization=org).count()
    
    total_tickets = tickets.count()
    completed_tickets = tickets.filter(status="DONE").count()

    # 3. Ticket Status Breakdown (1 optimized DB query)
    ticket_stats = tickets.aggregate(
        todo=Count('id', filter=Q(kanban_column='TODO')),
        development=Count('id', filter=Q(kanban_column='IN_PROGRESS')),
        review=Count('id', filter=Q(kanban_column='REVIEW')),
        done=Count('id', filter=Q(kanban_column='DONE')),
    )

    # 4. Project List with annotated ticket and member counts
    projects_annotated = projects.annotate(
        ticket_count=Count('tickets', distinct=True),
        member_count=Count('members', distinct=True) 
    ).order_by('is_archived', '-updated_at')[:10]

    projects_data = OrganizationProjectSummarySerializer(projects_annotated, many=True).data

    # 5. Response payload matching your frontend design mock
    return Response({
        "success": True,
        "metrics": {
            "projects": total_projects,
            "members": total_members,
            "tickets": total_tickets,
            "completed": completed_tickets,
        },
        "ticket_overview": {
            "todo": ticket_stats['todo'] or 0,
            "development": ticket_stats['development'] or 0,
            "review": ticket_stats['review'] or 0,
            "done": ticket_stats['done'] or 0,
        },
        "recent_activity": [],
        "projects": projects_data
    }, status=200)
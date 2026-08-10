from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..serializers import OrganizationSerializer, OrganizationDetailSerializer
from ..models import Organization
from ..permissions import has_admin_permission, is_org_owner
from projects.decorators import resolve_workspace
from users.models import Workspace

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

from .models import OrganizationMember

def get_org_member(user, organization):
    try:
        member = OrganizationMember.objects.get(
            user=user,
            organization=organization
        )
        return member
    except OrganizationMember.DoesNotExist:
        return None

def is_org_member(user, organization):
    member_exists = OrganizationMember.objects.filter(
        user=user,
        organization=organization
    ).exists()
    return member_exists

def has_admin_permission(user, organization):
    has_permission = OrganizationMember.objects.filter(
        user=user,
        organization=organization,
        role__in=[
            OrganizationMember.Role.OWNER,
            OrganizationMember.Role.ADMIN,
        ]
    ).exists()
    return has_permission

def is_org_owner(user, organization):
    owner_exists = OrganizationMember.objects.filter(
        user=user,
        organization=organization,
        role=OrganizationMember.Role.OWNER
    ).exists()
    return owner_exists
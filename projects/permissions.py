from .models import ProjectMember


def is_project_member(user, project):
    try:
        return ProjectMember.objects.get(
            user=user,
            project=project,
        )
    except ProjectMember.DoesNotExist:
        return None


def has_developer_permission(user, project):
    return ProjectMember.objects.filter(
        user=user,
        project=project,
        role__in=[
            ProjectMember.Role.DEVELOPER,
            ProjectMember.Role.LEAD,
            ProjectMember.Role.OWNER,
        ],
    ).exists()


def has_lead_permission(user, project):
    return ProjectMember.objects.filter(
        user=user,
        project=project,
        role__in=[
            ProjectMember.Role.LEAD,
            ProjectMember.Role.OWNER,
        ],
    ).exists()


def is_project_owner(user, project):
    return ProjectMember.objects.filter(
        user=user,
        project=project,
        role=ProjectMember.Role.OWNER,
    ).exists()
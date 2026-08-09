from rest_framework import serializers

from projects.models import Project, ProjectMember
from users.models import Workspace, User

class ProjectUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "avatar",
            "first_name",
            "last_name",
            "github_username",
        ]

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "visibility",
            "website",
        ]

class ProjectListSerializer(serializers.ModelSerializer):
    workspace_slug = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    workspace_type = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "visibility",
            "website",
            "workspace_slug",
            "workspace_name",
            "workspace_type",
            "created_at",
            "updated_at",
        ]

    def get_workspace_slug(self, obj):
        if obj.workspace.type == Workspace.Type.PERSONAL:
            return obj.workspace.owner.username

        return obj.workspace.organization.slug

    def get_workspace_name(self, obj):
        if obj.workspace.type == Workspace.Type.PERSONAL:
            return obj.workspace.owner.get_full_name() or obj.workspace.owner.username

        return obj.workspace.organization.name

    def get_workspace_type(self, obj):
        return obj.workspace.type

class ProjectDetailSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    created_by = ProjectUserSerializer(read_only=True)
    workspace_type = serializers.CharField(source="workspace.type",read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "visibility",
            "website",
            "is_archived",
            "created_by",
            "workspace_type",
            "role",
            "created_at",
            "updated_at",
        ]

    def get_role(self, obj):
        request = self.context["request"]
        user = request.user

        membership = ProjectMember.objects.filter(project=obj,user=user,).first()
        return membership.role if membership else None

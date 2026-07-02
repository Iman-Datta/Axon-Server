from rest_framework import serializers

from projects.models import Project

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

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "visibility",
            "website",
            "created_at",
            "updated_at",
        ]

class ProjectDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username",read_only=True)
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
            "created_at",
            "updated_at",
        ]

class ProjectUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "visibility",
            "website",
            "is_archived",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError("Project name too short.")
        return value
import re

from rest_framework import serializers

from ..models import Epic
from users.models import User
from projects.models import ProjectMember


class UserMiniSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "role",
        ]

    def get_role(self, obj):
        project = self.context.get("project")

        if not project:
            return None

        membership = ProjectMember.objects.filter(
            project=project,
            user=obj,
        ).first()

        return membership.role if membership else None


class EpicSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Epic
        fields = [
            "id",
            "name",
            "description",
            "color",
            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def get_created_by(self, obj):
        if not obj.created_by:
            return None

        return UserMiniSerializer(
            obj.created_by,
            context={"project": obj.project},
        ).data

    def validate_color(self, value):
        if not re.fullmatch(r"^#[0-9A-Fa-f]{6}$", value):
            raise serializers.ValidationError(
                "Color must be a valid hex code (e.g. #3B82F6)."
            )
        return value

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Epic name cannot be empty."
            )

        project = self.context["project"]

        queryset = Epic.objects.filter(
            project=project,
            name__iexact=value,
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "An epic with this name already exists in this project."
            )

        return value

    def create(self, validated_data):
        project = self.context["project"]
        user = self.context["user"]

        return Epic.objects.create(
            project=project,
            created_by=user,
            **validated_data,
        )

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance
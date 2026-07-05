import re
from rest_framework import serializers
from ..models import Epic

class EpicSerializer(serializers.ModelSerializer):
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

    def validate_color(self, value):
        if not re.fullmatch(r"^#[0-9A-Fa-f]{6}$", value):
            raise serializers.ValidationError(
                "Color must be a valid hex code (e.g. #3B82F6)."
            )
        return value
    
    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Epic name cannot be empty.")

        project = self.context["project"]

        queryset = Epic.objects.filter(project=project,name__iexact=value,)

        # Ignore current epic while updating
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError("An epic with this name already exists in this project.")
        return value

    def create(self, validated_data):
        project = self.context["project"]
        user = self.context["user"]

        epic = Epic.objects.create(
            project=project,
            created_by=user,
            **validated_data,
        )
        return epic
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

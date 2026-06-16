from rest_framework import serializers
from .models import Organization, OrganizationMember

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
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
            raise serializers.ValidationError("Organization name too short.")
        return value

    def create(self, validated_data):
        user = self.context["user"]

        organization = Organization.objects.create(
            created_by=user,
            **validated_data
        )

        OrganizationMember.objects.create(
            organization=organization,
            user=user,
            role = OrganizationMember.Role.OWNER
        )

        return organization
    
    def update(self, instance, validated_data):

        
        instance.name = validated_data.get("name",instance.name)
        instance.description = validated_data.get("description",instance.description)

        instance.save()
        return instance
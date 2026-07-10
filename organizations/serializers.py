from rest_framework import serializers
from .models import Organization, OrganizationMember
from users.models import User

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
    
class OrganizationDetailSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "avatar",
            "location",
            "email",
            "website",
            "followers_count",
            "members_count",
            "projects_count",
            "created_at",
        ]

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_members_count(self, obj):
        return obj.members.count()

    def get_projects_count(self, obj):
        return obj.projects.count()

class OrganizationMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username",read_only=True)
    email = serializers.EmailField(source="user.email",read_only=True)

    class Meta:
        model = OrganizationMember

        fields = [
            "id",
            "username",
            "email",
            "role",
            "joined_at",
        ]

class AddMemberSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=OrganizationMember.Role.choices, default=OrganizationMember.Role.MEMBER)

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=OrganizationMember.Role.choices
    )
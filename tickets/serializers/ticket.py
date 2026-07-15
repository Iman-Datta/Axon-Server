from rest_framework import serializers

from ..models import Ticket, Epic
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


class EpicMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Epic
        fields = [
            "id",
            "name",
            "color",
        ]


class TicketSerializer(serializers.ModelSerializer):
    epic = EpicMiniSerializer(read_only=True)
    epic_id = serializers.PrimaryKeyRelatedField(
        queryset=Epic.objects.all(),
        source="epic",
        write_only=True,
        required=False,
        allow_null=True,
    )
    creator = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()

    class Meta:
        model = Ticket

        fields = [
            "id",
            "title",
            "ticket_number",
            "description",
            "type",
            "status",
            "priority",
            "kanban_column",
            "story_points",
            "estimated_hours",
            "order",
            "epic",
            "epic_id",
            "creator",
            "assignee",
            "created_at",
            "updated_at",
            "due_date",
        ]

        read_only_fields = [
            "id",
            "ticket_number",
            "creator",
            "created_at",
            "updated_at",
        ]

    def get_creator(self, obj):
        if not obj.creator:
            return None

        return UserMiniSerializer(
            obj.creator,
            context={"project": obj.project},
        ).data

    def get_assignee(self, obj):
        if not obj.assignee:
            return None

        return UserMiniSerializer(
            obj.assignee,
            context={"project": obj.project},
        ).data

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Ticket title cannot be empty."
            )

        return value

    def create(self, validated_data):
        project = self.context["project"]
        user = self.context["user"]

        last_ticket = (Ticket.objects.filter(project=project,).order_by("-id").first())
        
        if last_ticket:
            last_number = int(last_ticket.ticket_number.split("-")[-1])
            next_number = last_number + 1
        else:
            next_number = 1

        ticket_number = (f"{project.slug.upper()}-{next_number}")

        return Ticket.objects.create(
            project=project,
            creator=user,
            ticket_number=ticket_number,
            **validated_data,
        )
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance
from django.db import transaction, IntegrityError
from django.db.models import Max, F

from rest_framework import serializers

from ..models import Ticket, Epic
from users.models import User
from projects.models import Project, ProjectMember


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

        with transaction.atomic():
            # Lock this project's row so two simultaneous ticket-creation
            # requests for the SAME project cannot read/increment the
            # counter at the same time. This guarantees no two tickets
            # in this project can ever get the same number.
            locked_project = Project.objects.select_for_update().get(pk=project.pk)

            locked_project.ticket_sequence = F("ticket_sequence") + 1
            locked_project.save(update_fields=["ticket_sequence"])
            locked_project.refresh_from_db(fields=["ticket_sequence"])

            next_number = locked_project.ticket_sequence
            ticket_number = f"{locked_project.key}-{next_number:03d}"

            # Get column (default is TODO)
            column = validated_data.get("kanban_column", Ticket.KanbanColumn.TODO)

            # Generate order
            max_order = (
                Ticket.objects.filter(project=project, kanban_column=column)
                .aggregate(Max("order"))["order__max"]
            )
            order = 0 if max_order is None else max_order + 1

            try:
                return Ticket.objects.create(
                    project=project,
                    creator=user,
                    ticket_number=ticket_number,
                    order=order,
                    **validated_data,
                )
            except IntegrityError:
                # Safety net only, should not trigger given the row lock above.
                raise serializers.ValidationError(
                    {"message": "Could not generate a unique ticket number. Please try again."}
                )

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance
from rest_framework import serializers

from ..models import Ticket


class TicketSerializer(serializers.ModelSerializer):
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
            "creator",
            "assignee",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "ticket_number",
            "creator",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Ticket title cannot be empty.")
        return value

    def create(self, validated_data):
        project = self.context["project"]
        user = self.context["user"]

        # Generate next ticket number
        ticket_count = Ticket.objects.filter(
            project=project
        ).count() + 1

        ticket_number = f"{project.slug.upper()}-{ticket_count}"

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
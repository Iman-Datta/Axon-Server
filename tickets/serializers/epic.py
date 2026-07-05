from rest_framework import serializers
from ..models import Epic

class EpicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Epic

        fields = [
            "name",
            "slug",
            "description",
            "color",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
        ]
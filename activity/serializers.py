from rest_framework import serializers
from activity.models import Activity
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "avatar"]

class ActivitySerializer(serializers.ModelSerializer):
    actor = UserMiniSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id",
            "verb",
            "metadata",
            "created_at",
            "actor",
        ]
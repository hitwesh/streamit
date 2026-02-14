from rest_framework import serializers

from .models import WatchProgress


class WatchProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchProgress
        fields = [
            "room",
            "media_id",
            "media_type",
            "season",
            "episode",
            "timestamp",
            "duration",
            "progress_percent",
            "completed",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rooms", "0008_room_genre"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="video_media_type",
            field=models.CharField(default="movie", max_length=10),
        ),
        migrations.AddField(
            model_name="room",
            name="video_season",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="room",
            name="video_episode",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]

from django.urls import path
from django.urls import path
from sync.consumers import RoomPresenceConsumer

websocket_urlpatterns = [
    path("ws/room/<str:room_code>/", RoomPresenceConsumer.as_asgi()),
    path("ws/v1/room/<str:room_code>/", RoomPresenceConsumer.as_asgi()),
]

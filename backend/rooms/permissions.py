class PermissionService:
    @staticmethod
    def _get_host_id(room):
        if isinstance(room, dict):
            return room.get("host_id")
        return getattr(room, "host_id", None)

    @staticmethod
    def is_host(user, room) -> bool:
        return (
            user.is_authenticated
            and not user.is_guest
            and PermissionService._get_host_id(room) == user.id
        )

    @staticmethod
    def can_host(user) -> bool:
        return (
            user.is_authenticated
            and not user.is_guest
            and user.username is not None
        )

    @staticmethod
    def can_control_playback(user, room) -> bool:
        return PermissionService.is_host(user, room)

    @staticmethod
    def can_moderate(user, room) -> bool:
        return PermissionService.is_host(user, room)

    @staticmethod
    def can_chat(user, room) -> bool:
        if not user.is_authenticated:
            return False
        return True

def room_state_key(room_code: str) -> str:
    return f"room:{room_code}:state"


def room_participants_key(room_code: str) -> str:
    return f"room:{room_code}:participants"


def room_host_status_key(room_code: str) -> str:
    return f"room:{room_code}:host_status"

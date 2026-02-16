def room_state_key(room_code: str) -> str:
    return f"room:{room_code}:state"


def room_participants_key(room_code: str) -> str:
    return f"room:{room_code}:participants"


def room_host_status_key(room_code: str) -> str:
    return f"room:{room_code}:host_status"


def room_viewers_key(room_code: str) -> str:
    return f"room:{room_code}:viewers"


def chat_rate_limit_key(room_code: str, user_id: str) -> str:
    return f"room:{room_code}:chat_rate:{user_id}"


def chat_duplicate_key(room_code: str, user_id: str) -> str:
    return f"room:{room_code}:chat_dup:{user_id}"

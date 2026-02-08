import asyncio


async def wait_for_event(comm, expected_type, timeout=1.0):
    """
    Consume messages until expected_type is found or timeout expires.
    """
    try:
        while True:
            event = await comm.receive_json_from(timeout=timeout)
            if event.get("type") == expected_type:
                return event
    except asyncio.TimeoutError as exc:
        raise AssertionError(f"Did not receive event {expected_type}") from exc

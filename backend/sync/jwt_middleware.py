from urllib.parse import parse_qs
import logging
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from channels.db import database_sync_to_async


logger = logging.getLogger("sync.ws.auth")


@database_sync_to_async
def get_user_from_token(token):
    try:
        validated = JWTAuthentication().get_validated_token(token)
        user = JWTAuthentication().get_user(validated)
        logger.info("WS auth token validated | user_id=%s", getattr(user, "id", None))
        return user
    except Exception as exc:
        logger.warning("WS auth token invalid | error=%s", exc.__class__.__name__)
        return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        token = query_params.get("token")
        if token:
            raw = token[0]
            logger.info("WS auth token present | len=%s", len(raw))
            scope["user"] = await get_user_from_token(token[0])
        else:
            logger.warning("WS auth token missing | query=%s", query_string)
            # Keep user resolved by AuthMiddlewareStack (e.g. session auth)
            # when no token is supplied.
            scope.setdefault("user", AnonymousUser())

        return await self.inner(scope, receive, send)

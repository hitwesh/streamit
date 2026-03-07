import logging
import os
import sys

from asgiref.sync import async_to_sync
from django.apps import AppConfig


logger = logging.getLogger(__name__)


class RoomsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rooms"

    def ready(self):
        if "test" in sys.argv:
            return

        if os.environ.get("RUN_MAIN") == "false":
            return

        from .services.recovery import recover_live_rooms

        try:
            async_to_sync(recover_live_rooms)()
        except Exception:
            logger.exception("Startup recovery failed")

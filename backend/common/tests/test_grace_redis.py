import asyncio
import time

from django.test import TestCase

from common.redis_room_state import clear_grace, is_in_grace, start_grace


class RedisGraceTests(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()

    def test_grace_ttl(self):
        room_code = "TESTROOM1"

        self.loop.run_until_complete(start_grace(room_code, 2))
        self.assertTrue(self.loop.run_until_complete(is_in_grace(room_code)))

        time.sleep(3)

        self.assertFalse(self.loop.run_until_complete(is_in_grace(room_code)))

    def test_clear_grace(self):
        room_code = "TESTROOM2"

        self.loop.run_until_complete(start_grace(room_code, 30))
        self.loop.run_until_complete(clear_grace(room_code))

        self.assertFalse(self.loop.run_until_complete(is_in_grace(room_code)))

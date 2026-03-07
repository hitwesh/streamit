from django.conf import settings
from django.db import connection
from django.http import JsonResponse
import redis


def health_check(request):
	try:
		connection.ensure_connection()
		db_status = "ok"
	except Exception:
		db_status = "error"

	try:
		client = redis.from_url(settings.REDIS_URL)
		client.ping()
		redis_status = "ok"
	except Exception:
		redis_status = "error"

	return JsonResponse({
		"status": "ok",
		"database": db_status,
		"redis": redis_status,
	})

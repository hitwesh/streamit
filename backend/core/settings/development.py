from .base import *

DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
	"localhost",
	"127.0.0.1",
	"[::1]",
]

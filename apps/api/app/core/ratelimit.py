from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

LLM_RATE_LIMIT = "10/minute"
PAYMENTS_RATE_LIMIT = "20/minute"
EMAIL_RATE_LIMIT = "5/minute"

from dotenv import load_dotenv
from redis import Redis
import os
import datetime

load_dotenv(".env")

class Config(object):
    # Flask base config
    SECRET_KEY = os.getenv("APP_SECRET_KEY")

    # Flask-Session config
    SESSION_TYPE = "redis"
    SESSION_REDIS = Redis.from_url(os.getenv("REDIS_URL"))
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=7)
    SESSION_COOKIE_DOMAIN = os.getenv("APP_DOMAIN")
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True

config = {
    "default": Config
}

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from redis import Redis
from app.routes.oauth import oauth_bp
from app.routes.playlists import playlists_bp
import os
import datetime
import logging
import sys

load_dotenv(".env")

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

# CORS config
CORS(app, supports_credentials=True)

# Flask-Session config
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(host="redis", port=6379, db=0)
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)

Session(app)

# Routes and blueprints config
app.register_blueprint(oauth_bp, url_prefix="/oauth")
app.register_blueprint(playlists_bp, url_prefix="/playlists")

# Logging config
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.ERROR)

logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(levelname)s - %(asctime)s]: %(message)s",
    datefmt="%m-%d-%Y %H:%M:%S",
    handlers=[stdout_handler, stderr_handler]
)

# Home endpoint
@app.route("/")
def index():
    return "Welcome to YouTify API"

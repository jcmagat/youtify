from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from redis import Redis
from app.routes.oauth import oauth_bp
from app.routes.playlists import playlists_bp
import os
import logging

load_dotenv(".env")

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

# CORS config
CORS(app, supports_credentials=True)

# Flask-Session config
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(host="redis", port=6379, db=0)

Session(app)

# Routes and blueprints config
app.register_blueprint(oauth_bp, url_prefix="/oauth")
app.register_blueprint(playlists_bp, url_prefix="/playlists")

# Logging config
logging.basicConfig(
    level=logging.DEBUG,
    filename="logs/debug.log",
    format="[%(levelname)s - %(asctime)s]: %(message)s",
    datefmt="%m-%d-%Y %H:%M:%S"
)

# Home endpoint
@app.route("/")
def index():
    return "Welcome to YouTify API"

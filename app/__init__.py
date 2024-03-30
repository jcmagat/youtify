from flask import Flask
from flask_talisman import Talisman
from flask_cors import CORS
from flask_session import Session
from app.config import config
from app.routes.oauth import oauth_bp
from app.routes.playlists import playlists_bp
import os
import logging
import sys

app = Flask(__name__)
app.config.from_object(config["default"])

# Talisman config
talisman = Talisman(
    app,
    force_https=True,
    force_https_permanent=True
)

# CORS config
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": "*"
    }
})

# Initialize Flask-Session
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

from dotenv import load_dotenv
from flask import Flask
import os

from app.routes.oauth import oauth_bp
from app.routes.playlists import playlists_bp

load_dotenv(".env")

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

app.register_blueprint(oauth_bp, url_prefix="/oauth")
app.register_blueprint(playlists_bp, url_prefix="/playlists")

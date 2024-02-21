from flask import Blueprint, redirect, request, jsonify, session, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

# YouTube API info
CLIENT_SECRETS_FILE = "app/config/client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI")

flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

# Create /youtube blueprint
youtube_bp = Blueprint("youtube", __name__)

# Home endpoint
@youtube_bp.route("/")
def index():
  return "Welcome to YouTify <a href='/youtube/login'>Login with YouTube</a>"

# Login endpoint
@youtube_bp.route("/login")
def login():
  auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
  return redirect(auth_url)

# Callback endpoint
@youtube_bp.route("/callback")
def callback():
  flow.fetch_token(authorization_response=request.url)
  credentials = flow.credentials

  # Store credentials in Flask session
  session["credentials"] = {
    "token": credentials.token,
    "refresh_token": credentials.refresh_token,
    "token_uri": credentials.token_uri,
    "client_id": credentials.client_id,
    "client_secret": credentials.client_secret,
    "scopes": credentials.scopes
  }
  
  return redirect(url_for("youtube.get_playlists"))

# Playlists endpoint
@youtube_bp.route("/playlists")
def get_playlists():
    if "credentials" not in session:
        return redirect(url_for("youtube.login"))

    credentials = Credentials.from_authorized_user_info(session["credentials"])

    # YouTube API client
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Fetch authenticated user's playlists
    playlists = youtube.playlists().list(
        part="snippet,contentDetails,status",
        mine=True
    ).execute()

    return jsonify(playlists)
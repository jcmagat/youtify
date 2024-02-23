from flask import Blueprint, redirect, request, session, url_for
from google_auth_oauthlib.flow import Flow
import os

# Create /oauth blueprint
oauth_bp = Blueprint("oauth", __name__)

WEB_APP_URL: str = os.getenv("WEB_APP_URL")

# YouTube API info
CLIENT_SECRETS_FILE = "app/config/client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

API_SERVICE_NAME: str = os.getenv("YOUTUBE_API_SERVICE_NAME")
API_VERSION: str = os.getenv("YOUTUBE_API_VERSION")
REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI")

flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

# Status endpoint
@oauth_bp.route("/status")
def status():
  res = {
      "is_logged_in_youtube": False,
      "is_logged_in_spotify": False
    }

  if "credentials" in session:
    res["is_logged_in_youtube"] = True

  if "access_token" in session:
    res["is_logged_in_spotify"] = True

  return res

# Login endpoint
@oauth_bp.route("/youtube/login")
def youtube_login():
  auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
  return redirect(auth_url)

# Callback endpoint
@oauth_bp.route("/youtube/callback")
def youtube_callback():
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
  
  # TODO: redirect to WEB_APP_URL
  return redirect(url_for("oauth.status"))

from flask import Blueprint, redirect, request, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow
import os
import requests
import urllib.parse
import datetime

# Create /oauth blueprint
oauth_bp = Blueprint("oauth", __name__)

WEB_APP_URL: str = os.getenv("WEB_APP_URL")

# YouTube API info
YOUTUBE_CLIENT_SECRETS_FILE = "app/config/client_secrets.json"
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly", 
                  "https://www.googleapis.com/auth/youtube.force-ssl"]
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI")

flow = Flow.from_client_secrets_file(
    YOUTUBE_CLIENT_SECRETS_FILE,
    scopes=YOUTUBE_SCOPES,
    redirect_uri=YOUTUBE_REDIRECT_URI
)

# Spotify Web API info
SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI")

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

# Status endpoint
@oauth_bp.route("/status")
def status():
  res = {
      "is_logged_in_youtube": False,
      "is_logged_in_spotify": False
    }

  # TODO: check for expiry

  if "credentials" in session:
    res["is_logged_in_youtube"] = True

  if "access_token" in session:
    res["is_logged_in_spotify"] = True

  return res

# ==================== YOUTUBE ENDPOINTS ====================

# YouTube login endpoint
@oauth_bp.route("/youtube/login")
def youtube_login():
  auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
  return redirect(auth_url)

# YouTube callback endpoint
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
  
  return redirect(os.getenv("WEB_APP_URL"))

# ==================== SPOTIFY ENDPOINTS ====================

# Spotify login endpoint
@oauth_bp.route("/spotify/login")
def spotify_login():
  scope = "user-read-private user-read-email playlist-read-private"
  params = {
    "client_id" : SPOTIFY_CLIENT_ID,
    "response_type": "code",
    "scope": scope,
    "redirect_uri": SPOTIFY_REDIRECT_URI,
    "show_dialog": True # TODO: remove after testing
  }
  auth_url = f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

  return redirect(auth_url)

# Spotify callback endpoint
@oauth_bp.route("/spotify/callback")
def spotify_callback():
  if "error" in request.args:
    # TODO: redirect to web app url with an error
    return jsonify({
      "error": request.args["error"]
    })
  
  if "code" in request.args:
    req_body = {
      "code": request.args["code"],
      "grant_type": "authorization_code",
      "redirect_uri": SPOTIFY_REDIRECT_URI,
      "client_id": SPOTIFY_CLIENT_ID,
      "client_secret": SPOTIFY_CLIENT_SECRET
    }

    # Send POST request with req_body to Spotify's token endpoint
    response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)

    token_info = response.json()
    session["access_token"] = token_info["access_token"]
    session["refresh_token"] = token_info["refresh_token"]
    session["expires_at"] = datetime.datetime.now().timestamp() + token_info["expires_in"]

    return redirect(os.getenv("WEB_APP_URL"))
  
  return redirect(url_for("oauth.spotify_login"))

# Spotify refresh token endpoint
@oauth_bp.route("/spotify/refresh-token")
def spotify_refresh_token():
  if "refresh_token" not in session:
    return redirect(url_for("oauth.spotify_login"))
  
  if datetime.datetime.now().timestamp() > session["expires_at"]:
    req_body = {
      "grant_type": "refresh_token",
      "refresh_token": session["refresh_token"],
      "client_id": SPOTIFY_CLIENT_ID,
      "client_secret": SPOTIFY_CLIENT_SECRET
    }
  
    response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)
    
    new_token_info = response.json()

    session["access_token"] = new_token_info["access_token"]
    session["expires_at"] = datetime.datetime.now().timestamp() + new_token_info["expires_in"]

  return redirect(os.getenv("WEB_APP_URL"))
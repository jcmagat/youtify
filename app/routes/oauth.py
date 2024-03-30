import logging
from flask import Blueprint, redirect, request, session, jsonify, render_template_string, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.services import YouTubeService
import os
import requests
import urllib.parse
import datetime

# Create /oauth blueprint
oauth_bp = Blueprint("oauth", __name__)

# YouTube API info
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI")
YOUTUBE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
        "project_id": os.getenv("YOUTUBE_PROJECT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET"),
        "redirect_uris": [YOUTUBE_REDIRECT_URI]
    }
}
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly", 
                  "https://www.googleapis.com/auth/youtube.force-ssl"]

flow = Flow.from_client_config(
    client_config=YOUTUBE_CLIENT_CONFIG,
    scopes=YOUTUBE_SCOPES,
    redirect_uri=YOUTUBE_REDIRECT_URI
)

# Spotify Web API info
SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI")

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


# ==================== YOUTUBE ENDPOINTS ====================


# YouTube login endpoint
@oauth_bp.route("/youtube/login")
def youtube_login():
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return jsonify({ "auth_url": auth_url })

# YouTube callback endpoint
@oauth_bp.route("/youtube/callback")
def youtube_callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # Store credentials in Flask session
    session["youtube_credentials"] = YouTubeService.format_credentials(credentials)
    
    return { "success": True }

# YouTube refresh token endpoint
@oauth_bp.route("/youtube/refresh-token")
def youtube_refresh_token():
    redirect_origin_url = session.pop("redirect_origin_url", None)
    if redirect_origin_url is None:
        # This endpoint should only be reached via a redirect from another endpoint
        return jsonify({ "error": "Bad request to refresh token" }), 400
    
    if "youtube_credentials" not in session:
        return jsonify({ "error": "Not authorized"}), 401
    
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
    if credentials.expired:
        credentials.refresh(Request())
        session["youtube_credentials"] = YouTubeService.format_credentials(credentials)

    return redirect(redirect_origin_url), 308

# YouTube check login status
@oauth_bp.route("/youtube/status")
def youtube_status():
    if "youtube_credentials" not in session:
        return jsonify({ "is_logged_in": False })
    
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
    if credentials.expired:
        session["redirect_origin_url"] = url_for("oauth.youtube_status")
        return redirect(url_for("oauth.youtube_refresh_token")), 307
    
    return jsonify({ "is_logged_in": True })


# ==================== SPOTIFY ENDPOINTS ====================


# Spotify login endpoint
@oauth_bp.route("/spotify/login")
def spotify_login():
    scope = "user-read-private user-read-email playlist-read-private playlist-modify-public playlist-modify-private"
    params = {
        "client_id" : SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "show_dialog": True # TODO: remove after testing
    }
    auth_url = f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

    return jsonify({ "auth_url": auth_url })

# Spotify callback endpoint
@oauth_bp.route("/spotify/callback")
def spotify_callback():
    if "error" in request.args:
        logging.error(f"Error in spotify_callback: {request.args["error"]}")
        return { "error": "Failed to authorize Spotify. Please contact the developer" }, 500
    
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
        session["spotify_credentials"] = {
        "access_token": token_info["access_token"],
        "refresh_token": token_info["refresh_token"],
        "expires_at": datetime.datetime.now().timestamp() + token_info["expires_in"]
        }

        return { "success": True }
    
    return jsonify({ "error": "Bad request to callback" }), 400

# Spotify refresh token endpoint
@oauth_bp.route("/spotify/refresh-token")
def spotify_refresh_token():
    redirect_origin_url = session.pop("redirect_origin_url", None)
    if redirect_origin_url is None:
        # This endpoint should only be reached via a redirect from another endpoint
        return jsonify({ "error": "Bad request to refresh token" }), 400
    
    if "spotify_credentials" not in session:
        return jsonify({ "error": "Not authorized"}), 401
    
    if datetime.datetime.now().timestamp() > session["spotify_credentials"]["expires_at"]:
        req_body = {
        "grant_type": "refresh_token",
        "refresh_token": session["spotify_credentials"]["refresh_token"],
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
        }
    
        response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session["spotify_credentials"]["access_token"] = new_token_info["access_token"]
        session["spotify_credentials"]["expires_at"] = datetime.datetime.now().timestamp() + new_token_info["expires_in"]

    return redirect(redirect_origin_url), 308

# Spotify check login status
@oauth_bp.route("/spotify/status")
def spotify_status():
    if "spotify_credentials" not in session:
        return jsonify({ "is_logged_in": False })

    if datetime.datetime.now().timestamp() > session["spotify_credentials"]["expires_at"]:
        session["redirect_origin_url"] = url_for("oauth.spotify_status")
        return redirect(url_for("oauth.spotify_refresh_token")), 307
    
    return jsonify({ "is_logged_in": True })
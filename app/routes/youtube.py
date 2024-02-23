from flask import Blueprint, redirect, jsonify, session, url_for
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

# Create /youtube blueprint
youtube_bp = Blueprint("youtube", __name__)

# YouTube API info
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

# Home endpoint
@youtube_bp.route("/")
def index():
  return "Welcome to YouTify <a href='/oauth/youtube/login'>Login with YouTube</a>"

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
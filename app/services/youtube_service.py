from flask import redirect, session, url_for
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# YouTube API info
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

class YouTubeService:
  @staticmethod
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

    return playlists

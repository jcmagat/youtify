from flask import redirect, session, url_for
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# YouTube API info
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

class YouTubeService:
  @staticmethod
  def get_playlists():
    credentials = Credentials.from_authorized_user_info(session["credentials"])

    # YouTube API client
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Fetch authenticated user's playlists
    playlists = youtube.playlists().list(
      part="snippet,contentDetails,status",
      mine=True
    ).execute()

    return playlists
  
  @staticmethod
  def create_playlist(name, description):
    credentials = Credentials.from_authorized_user_info(session["credentials"])

    # YouTube API client
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    playlist = youtube.playlists().insert(
      part="snippet,status",
      body={
        "snippet": {
          "title": name,
          "description": description
        },
        "status": {
          "privacyStatus": "private"
        }
      }
    ).execute()

    return playlist
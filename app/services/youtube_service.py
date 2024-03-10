from flask import session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# YouTube API info
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

class YouTubeService:
  @staticmethod
  def get_playlists():
    # YouTube API client
    credentials = Credentials.from_authorized_user_info(session["credentials"])
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Fetch authenticated user's playlists
    response = youtube.playlists().list(
      part="snippet",
      mine=True,
      maxResults=50
    ).execute()

    playlists = { "playlists" : [{
      "id": item["id"],
      "name": item["snippet"]["title"],
      "description": item["snippet"]["description"],
      "image": item["snippet"]["thumbnails"]["high"]["url"]
    } for item in response["items"]] }

    return playlists
  
  # Get a playlist's tracks
  @staticmethod
  def get_playlist_tracks(playlist_id: str):
    # YouTube API client
    credentials = Credentials.from_authorized_user_info(session["credentials"])
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    playlist_items_response = youtube.playlistItems().list(
      part="snippet",
      playlistId=playlist_id,
      maxResults=50
    ).execute()

    tracks = [{
      "id": item["snippet"]["resourceId"]["videoId"],
      "image": item["snippet"]["thumbnails"]["high"]["url"],
      "name": item["snippet"]["title"]
    } for item in playlist_items_response["items"]]
      
    videos_response = youtube.videos().list(
      part="snippet",
      id=[track["id"] for track in tracks]
    ).execute()

    category_ids = [item["snippet"]["categoryId"] for item in videos_response["items"]]

    # Only return music videos (categoryId of "10")
    filtered_tracks = [track for track, category_id in zip(tracks, category_ids) if category_id == "10"]

    return filtered_tracks
  
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
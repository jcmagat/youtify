from flask import session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import asyncio

# YouTube API info
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

class YouTubeService:
  @staticmethod
  async def get_playlists():
    def _fetch_playlists():
      # YouTube API client
      credentials = Credentials.from_authorized_user_info(session["credentials"])
      youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

      # Fetch authenticated user's playlists
      response = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
      ).execute()

      return [{
        "id": item["id"],
        "name": item["snippet"]["title"],
        "description": item["snippet"]["description"],
        "image": item["snippet"]["thumbnails"].get("high", {}).get("url", "")
      } for item in response["items"]]

    playlists = await asyncio.to_thread(_fetch_playlists)
    return { "playlists": playlists }
  
  # Get a playlist's tracks
  @staticmethod
  async def get_playlist_tracks(playlist_id: str):
    def _fetch_playlist_tracks():
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
        "name": item["snippet"]["title"],
        "image": item["snippet"]["thumbnails"].get("high", {}).get("url", "")
      } for item in playlist_items_response["items"]]
        
      videos_response = youtube.videos().list(
        part="snippet",
        id=[track["id"] for track in tracks]
      ).execute()

      category_ids = [item["snippet"]["categoryId"] for item in videos_response["items"]]

      # Only return music videos (categoryId of "10")
      return [track for track, category_id in zip(tracks, category_ids) if category_id == "10"]

    filtered_tracks = await asyncio.to_thread(_fetch_playlist_tracks)
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
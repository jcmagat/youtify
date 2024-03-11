from flask import session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import aiohttp

# YouTube API info
API_BASE_URL = "https://www.googleapis.com/youtube/v3"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

async def fetch_data(url, params=None, headers=None):
  async with aiohttp.ClientSession() as session:
    async with session.get(url, params=params, headers=headers) as response:
        return await response.json()

class YouTubeService:
  # Get all of user's playlists
  @staticmethod
  async def get_playlists():
    # YouTube API client
    credentials = Credentials.from_authorized_user_info(session["credentials"])
    access_token = credentials.token

    url = f"{API_BASE_URL}/playlists"
    params = {
      "part": "snippet",
      "mine": "true",
      "maxResults": 50,
    }
    headers = {
      "Authorization": f"Bearer {access_token}",
      "Accept": "application/json",
    }

    response = await fetch_data(url, params, headers)

    playlists = [{
      "id": item["id"],
      "name": item["snippet"]["title"],
      "description": item["snippet"]["description"],
      "image": item["snippet"]["thumbnails"].get("high", {}).get("url", "")
    } for item in response["items"]]
    
    return { "playlists": playlists }
  
  # Get a playlist's tracks
  @staticmethod
  async def get_playlist_tracks(playlist_id: str):
    # YouTube API client
    credentials = Credentials.from_authorized_user_info(session["credentials"])
    access_token = credentials.token

    # Get playlist's items
    items_url = f"{API_BASE_URL}/playlistItems"
    items_params = {
      "part": "snippet",
      "playlistId": playlist_id,
      "maxResults": 50,
    }
    items_headers = {
      "Authorization": f"Bearer {access_token}",
      "Accept": "application/json",
    }

    items_response = await fetch_data(items_url, items_params, items_headers)

    tracks = [{
      "id": item["snippet"]["resourceId"]["videoId"],
      "name": item["snippet"]["title"],
      "image": item["snippet"]["thumbnails"].get("high", {}).get("url", "")
    } for item in items_response["items"]]

    # Get videos (mainly for their categoryId)
    videos_url = f"{API_BASE_URL}/videos"
    videos_params = {
      "part": "snippet",
      "id": [track["id"] for track in tracks]
    }
    videos_headers = {
      "Authorization": f"Bearer {access_token}",
      "Accept": "application/json",
    }

    videos_response = await fetch_data(videos_url, videos_params, videos_headers)

    # Only return music videos (categoryId of "10")
    category_ids = [video["snippet"]["categoryId"] for video in videos_response["items"]]
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
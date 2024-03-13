from flask import session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import aiohttp
import asyncio

# YouTube API info
API_BASE_URL = "https://www.googleapis.com/youtube/v3"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

async def fetch_data(url, params=None, headers=None):
  async with aiohttp.ClientSession() as session:
    async with session.get(url, params=params, headers=headers) as response:
        return await response.json()
    
async def post(url, params=None, headers=None, json=None):
  async with aiohttp.ClientSession() as session:
    async with session.post(url=url, params=params, headers=headers, json=json) as response:
        return await response.json()

class YouTubeService:
  # Turn Credentials from oauth flow to a dictionary
  @staticmethod
  def format_credentials(credentials):
    return {
    "token": credentials.token,
    "refresh_token": credentials.refresh_token,
    "token_uri": credentials.token_uri,
    "client_id": credentials.client_id,
    "client_secret": credentials.client_secret,
    "scopes": credentials.scopes,
    "expiry": credentials.expiry.isoformat()
  }

  # Get all of user's playlists
  @staticmethod
  async def get_playlists():
    # YouTube API client
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
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
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
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
  
  # Create a playlist and return its id
  @staticmethod
  async def create_playlist(name: str, description: str):
    # YouTube API client
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
    access_token = credentials.token

    url = f"{API_BASE_URL}/playlists"
    params = {
      "part": "snippet"
    }
    headers = {
      "Authorization": f"Bearer {access_token}",
      "Content-Type": "application/json"
    }
    json = {
      "snippet": {
        "title": name,
        "desciption": description
      }
    }
    
    response = await post(url, params, headers, json)

    return response["id"]
  
  # Search for tracks and return a list of each track's videoIds
  @staticmethod
  async def search_tracks(tracks: list[str]):
    # YouTube API client
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
    access_token = credentials.token

    url = f"{API_BASE_URL}/search"
    params = {
      "part": "snippet",
      "type": "video",
      "maxResults": 1,
      "q": ""
    }
    headers = {
      "Authorization": f"Bearer {access_token}",
      "Content-Type": "application/json"
    }

    tasks = [fetch_data(url, headers=headers, params={ **params, "q": track }) for track in tracks]
    results = await asyncio.gather(*tasks)

    ids = [video["items"][0]["id"]["videoId"] for video in results]

    return ids
  
  # Add tracks to playlist
  @staticmethod
  async def fill_playlist(playlist_id: str, track_ids: list[str]):
    # YouTube API client
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
    access_token = credentials.token

    # Search for tracks
    url = f"{API_BASE_URL}/playlistItems"
    params = {
      "part": "snippet",
      "type": "video",
      "maxResults": 1,
      "q": ""
    }
    headers = {
      "Authorization": f"Bearer {access_token}",
      "Content-Type": "application/json"
    }

    tasks = []
    for track_id in track_ids:
      json = {
        "snippet": {
          "playlistId": playlist_id,
          "resourceId": {
            "kind": "youtube#video",
            "videoId": track_id
          }
        }
      }
      tasks.append(post(url, params, headers, json))

    # TODO: fix operation ABORTED error
    results = await asyncio.gather(*tasks)

    return results
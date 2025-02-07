from flask import session
from google.oauth2.credentials import Credentials
from app.schemas import Playlist, Track
from app.utils import fetch_cache, set_cache
import aiohttp
import asyncio
import logging
import time
import json

# YouTube API info
API_BASE_URL = "https://www.googleapis.com/youtube/v3"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

async def fetch_data(url, params=None, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            try:
                data = await response.json()
                if response.status == 200:
                    return data
                else:
                    response.raise_for_status() # caught by except below
            except aiohttp.ClientResponseError as e:
                if e.status == 403 and "quotaExceeded" in str(data):
                    # Re-raise rate limit error as 429 to standardize across different music services
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=429,
                        message="Rate Limit Exceeded"
                    )
                else:
                    response.raise_for_status()


async def post(url, params=None, headers=None, json=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, params=params, headers=headers, json=json) as response:
            try:
                data = await response.json()
                if response.status == 200:
                    return data
                else:
                    response.raise_for_status() # caught by except below
            except aiohttp.ClientResponseError as e:
                if e.status == 403 and "quotaExceeded" in str(data):
                    # Re-raise rate limit error as 429 to standardize across different music services
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=429,
                        message="Rate Limit Exceeded"
                    )
                else:
                    response.raise_for_status()

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

        url = f"{API_BASE_URL}/playlists" # quota cost per call: 1
        params = {
            "part": "snippet",
            "mine": "true",
            "maxResults": 50,
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        try:
            response = await fetch_data(url, params, headers)
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in YouTubeService.get_playlists: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in YouTubeService.get_playlists: {e}")
            raise            
        
        playlists = [Playlist(**{
            "id": item["id"],
            "name": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "image": item["snippet"]["thumbnails"].get("high", {}).get("url", "")
        }) for item in response["items"]]
        
        return { "playlists": playlists }
  
    # Get a playlist's tracks
    @staticmethod
    async def get_playlist_tracks(playlist_id: str):
        # YouTube API client
        credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
        access_token = credentials.token

        # Get playlist's items
        items_url = f"{API_BASE_URL}/playlistItems" # quota cost per call: 1
        items_params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
        }
        items_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        try:
            items_response = await fetch_data(items_url, items_params, items_headers)

            tracks = [Track(**{
                "id": item["snippet"]["resourceId"]["videoId"],
                "name": item["snippet"]["title"],
                "image": item["snippet"]["thumbnails"].get("high", {}).get("url", "")
            }) for item in items_response["items"]]

            # Get videos (mainly for their categoryId)
            videos_url = f"{API_BASE_URL}/videos" # quota cost per call: 1
            videos_params = {
                "part": "snippet",
                "id": [track.id for track in tracks]
            }
            videos_headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            videos_response = await fetch_data(videos_url, videos_params, videos_headers)
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in YouTubeService.get_playlist_tracks: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in YouTubeService.get_playlist_tracks: {e}")
            raise

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

        url = f"{API_BASE_URL}/playlists" # quota cost per call: 50
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
        
        try:
            response = await post(url, params, headers, json)
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in YouTubeService.create_playlist: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in YouTubeService.create_playlist: {e}")
            raise

        return response["id"]
  
    # Search for tracks and return a list of each video's videoId
    # videoId is used for inserting playlistItems into playlists in fill_playlist()
    @staticmethod
    async def search_tracks(tracks: list[str]):
        async def _search_track(track: str):
            # Check cache
            cached_video_id = await fetch_cache(f"youtube_search:{track}")
            if cached_video_id:
                return cached_video_id.decode("utf-8")

            # YouTube API client
            credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
            access_token = credentials.token

            url = f"{API_BASE_URL}/search" # quota cost per call: 100
            params = {
                "part": "snippet",
                "type": "video",
                "maxResults": 1,
                "videoCategoryId": "10", # music
                "q": ""
            }
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # Fetch from YouTube        
            params["q"] = track
            result = await fetch_data(url, headers=headers, params=params)

            video_id = result["items"][0]["id"]["videoId"]

            # Save to cache
            await set_cache(f"youtube_search:{track}", video_id, ttl=60*60*24) # 1 day

            return video_id

        try:
            tasks = [_search_track(track) for track in tracks]
            results = await asyncio.gather(*tasks)
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in YouTubeService.search_tracks: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in YouTubeService.search_tracks: {e}")
            raise

        return results
  
    # Add tracks to playlist
    @staticmethod
    async def fill_playlist(playlist_id: str, video_ids: list[str]):
        # YouTube API client
        credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
        access_token = credentials.token

        url = f"{API_BASE_URL}/playlistItems" # quota cost per call: 50
        params = {
            "part": "snippet"
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async def _add_to_playlist(playlist_id, video_id):
            MAX_RETRIES = 5
            retry_count = 0
            wait_time = 1 # seconds

            while retry_count < MAX_RETRIES:
                try:
                    json = {
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id
                            }
                        }
                    }
                    return await post(url, params, headers, json)
                except aiohttp.ClientResponseError as e:
                    if e.status == 409:
                        retry_count += 1
                        time.sleep(wait_time)
                        wait_time *= 2
                    else:
                        raise
            return { "error": "Failed to add video to playlist" }

        try:
            results = [await _add_to_playlist(playlist_id, video_id) for video_id in video_ids]
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in YouTubeService.fill_playlist: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in YouTubeService.fill_playlist: {e}")
            raise

        return results
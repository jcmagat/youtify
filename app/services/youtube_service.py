from flask import session
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from app.schemas import Playlist, Track
import aiohttp
import asyncio
import logging

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
            logging.error(f"Error in YouTubeService.get_playlists: {e}")
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
            logging.error(f"Error in YouTubeService.create_playlist: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in YouTubeService.create_playlist: {e}")
            raise

        return response["id"]
  
    # Search for tracks and return a list of each video's resourceId
    # resourceId is used for inserting playlistItems into playlists in fill_playlist()
    @staticmethod
    async def search_tracks(tracks: list[str]):
        # YouTube API client
        credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
        access_token = credentials.token

        url = f"{API_BASE_URL}/search" # quota cost per call: 100
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

        try:
            tasks = [fetch_data(url, headers=headers, params={ **params, "q": track }) for track in tracks]
            results = await asyncio.gather(*tasks)
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in YouTubeService.search_tracks: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in YouTubeService.search_tracks: {e}")
            raise

        resource_ids = [video["items"][0]["id"] for video in results]

        return resource_ids
  
    # Add tracks to playlist
    @staticmethod
    async def fill_playlist(playlist_id: str, resource_ids: list[str]):
        # YouTube API client
        credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
        access_token = credentials.token

        # Search for tracks
        url = f"{API_BASE_URL}/playlistItems" # quota cost per call: 50
        params = {
            "part": "snippet"
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            results = []
            for resource_id in resource_ids:
                json = {
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": resource_id
                    }
                }
                results.append(await post(url, params, headers, json))

            # NOTE: seems like adding videos to playlist can't be done asynchronously
            # without running into 409 Conflict errors
            # BUT 409 still happens with large playlists despite synchronous calls

        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in YouTubeService.fill_playlist: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in YouTubeService.fill_playlist: {e}")
            raise

        return results
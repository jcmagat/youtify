import logging
from flask import session
from app.schemas import Playlist, Track
import aiohttp
import asyncio

API_BASE_URL = "https://api.spotify.com/v1"

async def fetch_data(url, params=None, headers=None):
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(url, params=params, headers=headers) as response:
            return await response.json()
        
async def post(url, json=None, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, json=json, headers=headers) as response:
            return await response.json()

class SpotifyService:
    # Get all playlists
    @staticmethod
    async def get_playlists():
        token = session["spotify_credentials"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = await fetch_data(f"{API_BASE_URL}/me/playlists", headers=headers)
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in SpotifyService.get_playlists: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in SpotifyService.get_playlists: {e}")
            raise

        playlists = [Playlist(**{
            "id": item["id"],
            "name": item["name"],
            "description": item["description"],
            "image": item["images"][0]["url"]
        }) for item in response["items"]]

        return { "playlists" : playlists }

    # Get a playlist's tracks
    @staticmethod
    async def get_playlist_tracks(playlist_id):
        token = session["spotify_credentials"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = await fetch_data(f"{API_BASE_URL}/playlists/{playlist_id}/tracks", headers=headers)
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in SpotifyService.get_playlist_tracks: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in SpotifyService.get_playlist_tracks: {e}")
            raise
    
        tracks: list[Track] = []
        for item in response["items"]:
            track = item["track"]
            artists = []

            for artist in track["artists"]:
                artists.append(artist["name"])

            new_track = Track(**{
                "id": track["id"],
                "image": track["album"]["images"][0]["url"],
                "name": f"{", ".join(artists)} - {track["name"]}"
            })
            tracks.append(new_track)

        return tracks

    # Create a playlist and return its id
    @staticmethod
    async def create_playlist(name: str, description: str):
        token = session["spotify_credentials"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        try:
            user_response = await fetch_data(f"{API_BASE_URL}/me", headers=headers)
            user_id = user_response["id"]

            body = {
                "name": name,
                "description": description
            }
            response = await post(f"{API_BASE_URL}/users/{user_id}/playlists", json=body, headers=headers)
            return response["id"]
        
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in SpotifyService.create_playlist: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in SpotifyService.create_playlist: {e}")
            raise
  
    # Search for tracks and return a list of each track's uri
    # track uri is used for inserting tracks into playlists in fill_playlist()
    @staticmethod
    async def search_tracks(tracks: list[str]):
        token = session["spotify_credentials"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}


        try:
            tasks = []
            for track in tracks:
                params = {
                    "q": track,
                    "type": ["track"],
                    "limit": 1
                }
                tasks.append(fetch_data(f"{API_BASE_URL}/search", params=params, headers=headers))
            
            responses = await asyncio.gather(*tasks)
            track_uris = [response["tracks"]["items"][0]["uri"] for response in responses]
            return track_uris
        
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in SpotifyService.search_tracks: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in SpotifyService.search_tracks: {e}")
            raise
  
    # Add tracks to playlist
    @staticmethod
    async def fill_playlist(playlist_id: str, track_uris: list[str]):
        token = session["spotify_credentials"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        try:
            body = { "uris": track_uris }
            response = await post(f"{API_BASE_URL}/playlists/{playlist_id}/tracks", json=body, headers=headers)
            return response
        
        except aiohttp.ClientResponseError as e:
            logging.error(f"Error in SpotifyService.fill_playlist: {e.status} {e.message}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in SpotifyService.fill_playlist: {e}")
            raise
import logging
from flask import session
from app.schemas import Playlist, Track
import aiohttp

API_BASE_URL = "https://api.spotify.com/v1"

async def fetch_data(url, headers=None):
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(url, headers=headers) as response:
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

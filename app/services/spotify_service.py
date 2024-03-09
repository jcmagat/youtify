from flask import session
import aiohttp

API_BASE_URL = "https://api.spotify.com/v1/"

async def fetch_data(url, headers=None):
  async with aiohttp.ClientSession() as session:
    async with session.get(url, headers=headers) as response:
        return await response.json()

class SpotifyService:
  # Get all playlists
  @staticmethod
  async def get_playlists():
    headers = {
      "Authorization": f"Bearer {session["access_token"]}"
    }

    response = await fetch_data(f"{API_BASE_URL}me/playlists", headers=headers)

    playlists = { "playlists" : [] }

    for item in response["items"]:      
      playlist = {
        "id": item["id"],
        "name": item["name"],
        "description": item["description"],
        "image": item["images"][0]["url"]
      }

      playlists["playlists"].append(playlist)

    return playlists

  # Get a playlist's tracks
  @staticmethod
  async def get_playlist_tracks(playlist_id):
    headers = {
      "Authorization": f"Bearer {session["access_token"]}"
    }

    response = await fetch_data(f"{API_BASE_URL}playlists/{playlist_id}/tracks", headers=headers)
    
    tracks = []
    
    for item in response["items"]:
      track = item["track"]
      artists = []

      for artist in track["artists"]:
        artists.append(artist["name"])

      new_track = {
        "id": track["id"],
        "image": track["album"]["images"][0]["url"],
        "name": f"{", ".join(artists)} - {track["name"]}"
      }

      tracks.append(new_track)
    
    return tracks

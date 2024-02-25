from flask import session
import requests

API_BASE_URL = "https://api.spotify.com/v1/"

class SpotifyService:
  @staticmethod
  def get_playlist_tracks(playlist_id):
    headers = {
      "Authorization": f"Bearer {session["access_token"]}"
    }

    response = requests.get(API_BASE_URL + f"playlists/{playlist_id}/tracks", headers=headers)
    tracks = response.json()

    result = []

    for item in tracks["items"]:
      track = item["track"]
      artists = []
      
      for artist in track["artists"]:
        artists.append(artist["name"])

      result.append(f"{", ".join(artists)} - {track["name"]}")
    
    return result
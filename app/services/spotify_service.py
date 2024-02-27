from flask import redirect, session, url_for
import requests

API_BASE_URL = "https://api.spotify.com/v1/"

class SpotifyService:
  @staticmethod
  def get_playlists():
    headers = {
      "Authorization": f"Bearer {session["access_token"]}"
    }

    response = requests.get(API_BASE_URL + "me/playlists", headers=headers).json()

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
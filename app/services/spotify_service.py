from flask import redirect, session, url_for
import requests
import datetime

API_BASE_URL = "https://api.spotify.com/v1/"

class SpotifyService:
  @staticmethod
  def get_playlists():
    if "access_token" not in session:
      return redirect(url_for("spotify.login"))

    if datetime.datetime.now().timestamp() > session["expires_at"]:
      return redirect(url_for("spotify.refresh_token"))

    headers = {
      "Authorization": f"Bearer {session["access_token"]}"
    }

    response = requests.get(API_BASE_URL + "me/playlists", headers=headers)
    playlists = response.json()

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
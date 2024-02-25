from flask import Blueprint, redirect, jsonify, session, url_for
from app.services import SpotifyService
import requests
import datetime

API_BASE_URL = "https://api.spotify.com/v1/"

# Create /spotify blueprint
spotify_bp = Blueprint("spotify", __name__)

# Playlists endpoint
@spotify_bp.route("/playlists")
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

  return jsonify(playlists)

# Playlist tracks endpoint
@spotify_bp.route("/playlists/<playlist_id>/tracks")
def get_playlist_tracks(playlist_id):
  if "access_token" not in session:
    return redirect(url_for("spotify.login"))
  
  if datetime.datetime.now().timestamp() > session["expires_at"]:
    return redirect(url_for("spotify.refresh_token"))

  tracks = SpotifyService.get_playlist_tracks(playlist_id)

  res = {
    "playlist_id": playlist_id,
    "tracks": tracks
  }

  return jsonify(res)

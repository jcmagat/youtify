from flask import Blueprint, jsonify, redirect, session, url_for, request
from app.services import SpotifyService
from app.services import YouTubeService
import datetime
import asyncio

# Create /playlists blueprint
playlists_bp = Blueprint("playlists", __name__)

# ==================== SPOTIFY ENDPOINTS ====================

# Get all Spotify playlists + tracks
@playlists_bp.route("/spotify")
async def get_spotify_playlists():
  if "access_token" not in session:
    return jsonify({ "error": "Not authorized"}), 401

  if datetime.datetime.now().timestamp() > session["expires_at"]:
    session["redirect_origin_url"] = url_for("playlists.get_spotify_playlists")
    return redirect(url_for("oauth.spotify_refresh_token"))
  
  playlists = await SpotifyService.get_playlists()
  
  # Asynchronous calls to Spotify API
  tasks = [SpotifyService.get_playlist_tracks(playlist["id"]) for playlist in playlists["playlists"]]
  results = await asyncio.gather(*tasks)

  # Map resulting tracks to corresponding playlist
  for i, playlist in enumerate(playlists["playlists"]):
    playlist["tracks"] = results[i]

  return jsonify(playlists)

# TODO: CREATE SPOTIFY PLAYLISTS FROM A LIST OF PLAYLISTS

# ==================== YOUTUBE ENDPOINTS ====================

# Get all YouTube playlists + tracks
@playlists_bp.route("/youtube")
def get_youtube_playlists():
    if "credentials" not in session:
      return jsonify({ "error": "Not authorized"}), 401
    
    playlists = YouTubeService.get_playlists()

    return jsonify(playlists)

# TODO: CREATE YOUTUBE PLAYLISTS FROM A LIST OF PLAYLISTS
# Create a YouTube playlist
@playlists_bp.route("/youtube/create", methods=["POST"])
def create_youtube_playlist():
  if "credentials" not in session:
    return jsonify({ "error": "Not authorized"}), 401
  
  data = request.json
  
  playlist = YouTubeService.create_playlist(data["name"], data["description"])

  return jsonify(playlist)

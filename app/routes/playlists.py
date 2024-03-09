from flask import Blueprint, jsonify, redirect, session, url_for, request
from app.services import SpotifyService
from app.services import YouTubeService
import datetime

# Create /playlists blueprint
playlists_bp = Blueprint("playlists", __name__)

# ==================== SPOTIFY ENDPOINTS ====================

# Get all Spotify playlists + tracks
@playlists_bp.route("/spotify")
def get_spotify_playlists():
  if "access_token" not in session:
    return jsonify({ "error": "Not authorized"}), 401

  if datetime.datetime.now().timestamp() > session["expires_at"]:
    session["redirect_origin_url"] = url_for("playlists.get_spotify_playlists")
    return redirect(url_for("oauth.spotify_refresh_token"))
  
  playlists = SpotifyService.get_playlists()
  
  for playlist in playlists["playlists"]:
    tracks = SpotifyService.get_playlist_tracks(playlist["id"])
    playlist["tracks"] = tracks

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

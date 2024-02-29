from flask import Blueprint, jsonify, redirect, session, url_for, request
from app.services import SpotifyService
from app.services import YouTubeService
import datetime

# Create /playlists blueprint
playlists_bp = Blueprint("playlists", __name__)

# ==================== SPOTIFY ENDPOINTS ====================

# Get all Spotify playlists
@playlists_bp.route("/spotify")
def get_spotify_playlists():
  if "access_token" not in session:
    return redirect(url_for("oauth.spotify_login"))

  if datetime.datetime.now().timestamp() > session["expires_at"]:
    return redirect(url_for("oauth.spotify_refresh_token"))
  
  playlists = SpotifyService.get_playlists()

  return jsonify(playlists)

# Get a single Spotify playlist
@playlists_bp.route("/spotify/<playlist_id>")
def get_spotify_playlist(playlist_id):
  if "access_token" not in session:
    return redirect(url_for("oauth.spotify_login"))

  if datetime.datetime.now().timestamp() > session["expires_at"]:
    return redirect(url_for("oauth.spotify_refresh_token"))
  
  playlist = SpotifyService.get_playlist(playlist_id)

  return jsonify(playlist)

# ==================== YOUTUBE ENDPOINTS ====================

# Get all YouTube playlists
@playlists_bp.route("/youtube")
def get_youtube_playlists():
    if "credentials" not in session:
      return redirect(url_for("youtube.login"))
    
    playlists = YouTubeService.get_playlists()

    return jsonify(playlists)

# Create a YouTube playlist
@playlists_bp.route("/youtube/create", methods=["POST"])
def create_youtube_playlist():
  if "credentials" not in session:
    return redirect(url_for("youtube.login"))
  
  data = request.json
  
  playlist = YouTubeService.create_playlist(data["name"], data["description"])

  return jsonify(playlist)

# ==================== SHARED ENDPOINTS ====================

@playlists_bp.route("/copy", methods=["POST"])
def copy_playlists():
  # Get spotify playlists ids
  data = request.json
  if "playlist_ids" not in data:
    return jsonify({"error": "Playlist IDs not provided"}), 400

  # Get spotify playlist tracks, other info
  spotify_playlists = []
  for id in data["playlist_ids"]:
    spotify_playlists.append(SpotifyService.get_playlist(id))

  # Create youtube playlist
  youtube_playlist = YouTubeService.create_playlist(data["name"], data["description"])

  # Search for tracks


  # Add to playlist
  

  return jsonify({})

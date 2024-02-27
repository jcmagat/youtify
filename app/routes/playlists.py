from flask import Blueprint, jsonify, redirect, session, url_for
from app.services import SpotifyService
from app.services import YouTubeService
import datetime

# Create /playlists blueprint
playlists_bp = Blueprint("playlists", __name__)

# Playlists endpoint
@playlists_bp.route("/spotify")
def get_spotify_playlists():
  if "access_token" not in session:
    return redirect(url_for("oauth.spotify_login"))

  if datetime.datetime.now().timestamp() > session["expires_at"]:
    return redirect(url_for("oauth.spotify_refresh_token"))
  
  playlists = SpotifyService.get_playlists()

  return jsonify(playlists)

# Playlists endpoint
@playlists_bp.route("/youtube")
def get_youtube_playlists():
    playlists = YouTubeService.get_playlists()

    return jsonify(playlists)

# TODO: Copy playlists
@playlists_bp.route("/copy", methods=["POST"])
def copy_playlists():
    # Get spotify playlists ids
    # Get spotify playlist tracks, other info
    # Create youtube playlist
    # Search for tracks
    # Add to playlist

    return jsonify({})

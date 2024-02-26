from flask import Blueprint, jsonify
from app.services import SpotifyService
from app.services import YouTubeService

# Create /playlists blueprint
playlists_bp = Blueprint("playlists", __name__)

# Playlists endpoint
@playlists_bp.route("/spotify")
def get_spotify_playlists():
  playlists = SpotifyService.get_playlists()

  return jsonify(playlists)

# Playlists endpoint
@playlists_bp.route("/youtube")
def get_youtube_playlists():
    playlists = YouTubeService.get_playlists()

    return jsonify(playlists)

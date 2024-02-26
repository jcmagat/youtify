from flask import Blueprint, jsonify
from app.services import SpotifyService

SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1/"

# Create /playlists blueprint
playlists_bp = Blueprint("playlists", __name__)

# Playlists endpoint
@playlists_bp.route("/spotify")
def get_spotify_playlists():
  playlists = SpotifyService.get_playlists()

  return jsonify(playlists)
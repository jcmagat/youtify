from dotenv import load_dotenv
from flask import Blueprint, redirect, request, jsonify, session
import os
import requests
import urllib.parse
import datetime

load_dotenv(".env")

# Spotify Web API info
CLIENT_ID: str = os.getenv("CLIENT_ID")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")
REDIRECT_URI: str = os.getenv("REDIRECT_URI")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"

# Create /spotify blueprint
spotify_bp = Blueprint("spotify", __name__)

# Login endpoint
@spotify_bp.route("/login")
def login():
  scope = "user-read-private user-read-email playlist-read-private"
  params = {
    "client_id" : CLIENT_ID,
    "response_type": "code",
    "scope": scope,
    "redirect_uri": REDIRECT_URI,
    "show_dialog": True #remove after testing
  }
  auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
  return redirect(auth_url)

# Callback endpoint
@spotify_bp.route("/callback")
def callback():
  if "error" in request.args:
    return jsonify({
      "error": request.args["error"]
    })
  
  if "code" in request.args:
    req_body = {
      "code": request.args["code"],
      "grant_type": "authorization_code",
      "redirect_uri": REDIRECT_URI,
      "client_id": CLIENT_ID,
      "client_secret": CLIENT_SECRET
    }

    # Send POST request with req_body to Spotify's token endpoint
    response = requests.post(TOKEN_URL, data=req_body)

    token_info = response.json()
    session["access_token"] = token_info["access_token"]
    session["refresh_token"] = token_info["refresh_token"]
    session["expires_at"] = datetime.datetime.now().timestamp() + token_info["expires_in"]

    return redirect("/spotify/playlists")
  
  return redirect("/spotify/login")

# Playlists endpoint
@spotify_bp.route("/playlists")
def get_playlists():
  if "access_token" not in session:
    return redirect("/spotify/login")

  if datetime.datetime.now().timestamp() > session["expires_at"]:
    return redirect("/spotify/refresh-token")

  headers = {
    "Authorization": f"Bearer {session["access_token"]}"
  }

  response = requests.get(API_BASE_URL + "me/playlists", headers=headers)
  playlists = response.json()

  return jsonify(playlists)

# Refresh token endpoint
@spotify_bp.route("/refresh-token")
def refresh_token():
  if "refresh_token" not in session:
    return redirect("/spotify/login")
  
  if datetime.datetime.now().timestamp() > session["expires_at"]:
    req_body = {
      "grant_type": "refresh_token",
      "refresh_token": session["refresh_token"],
      "client_id": CLIENT_ID,
      "client_secret": CLIENT_SECRET
    }
  
    response = requests.post(TOKEN_URL, data=req_body)
    
    new_token_info = response.json()
    print(new_token_info)

    session["access_token"] = new_token_info["access_token"]
    session["expires_at"] = datetime.datetime.now().timestamp() + new_token_info["expires_in"]

  return redirect("/spotify/playlists")

# Playlist tracks endpoint
@spotify_bp.route("/playlists/<playlist_id>/tracks")
def get_playlist_tracks(playlist_id):
  if "access_token" not in session:
    return redirect("/spotify/login")
  
  if datetime.datetime.now().timestamp() > session["expires_at"]:
    return redirect("/spotify/refresh-token")
  
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

  return jsonify(result)

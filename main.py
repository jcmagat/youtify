from dotenv import load_dotenv
from flask import Flask, redirect, request, jsonify, session
import os
import requests
import urllib.parse
import datetime

load_dotenv(".env")

app = Flask(__name__)
app.secret_key: str = os.getenv("APP_SECRET_KEY")

# Spotify Web API info
CLIENT_ID: str = os.getenv("CLIENT_ID")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")
REDIRECT_URI: str = os.getenv("REDIRECT_URI")

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"

# Home endpoint
@app.route("/")
def index():
  return "Welcome to YouTify <a href='/login'>Login with Spotify</a>"

# Login endpoint
@app.route("/login")
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
@app.route("/callback")
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

    return redirect("/playlists")
  
  return redirect("/login")

if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True, port=8080)

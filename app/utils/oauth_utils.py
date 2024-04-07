import logging
from flask import session, jsonify
from functools import wraps
import os
import datetime
import requests

# Spotify Web API info
SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI")

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

def authorize_spotify():
    logging.debug("In authorize_spotify")
    if "spotify_credentials" not in session:
        logging.debug("In authorize_spotify: Not authorized")
        return jsonify({ "error": "Not authorized" })

    if datetime.datetime.now().timestamp() > session["spotify_credentials"]["expires_at"]:
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": session["spotify_credentials"]["refresh_token"],
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET
        }
    
        response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session["spotify_credentials"]["access_token"] = new_token_info["access_token"]
        session["spotify_credentials"]["expires_at"] = datetime.datetime.now().timestamp() + new_token_info["expires_in"]
    

def authorize(service: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logging.debug("In decorated_function")

            if service == "spotify":
                authorize_spotify()
            elif service == "youtube":
                return jsonify({ "error", "Not implemented" })
            else:
                return jsonify({ "error", "Invalid service" })
            return f(*args, **kwargs)
        return decorated_function
    return decorator

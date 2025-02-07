from flask import Blueprint, jsonify, redirect, session, url_for, request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from app.services import SpotifyService
from app.services import YouTubeService
import datetime
import asyncio
import aiohttp

# Create /playlists blueprint
playlists_bp = Blueprint("playlists", __name__)


# ==================== SPOTIFY ENDPOINTS ====================


# Get all Spotify playlists + tracks
@playlists_bp.route("/spotify")
async def get_spotify_playlists():
    if "spotify_credentials" not in session:
        return { "error": "Not authorized" }, 401

    if datetime.datetime.now().timestamp() > session["spotify_credentials"]["expires_at"]:
        session["redirect_origin_url"] = url_for("playlists.get_spotify_playlists")
        return redirect(url_for("oauth.spotify_refresh_token"))
    
    try:
        playlists = await SpotifyService.get_playlists()
    
        # Asynchronous calls to Spotify API
        tasks = [SpotifyService.get_playlist_tracks(playlist.id) for playlist in playlists["playlists"]]
        results = await asyncio.gather(*tasks)
    except aiohttp.ClientResponseError as e:
        if e.status == 401:
            return { "error": "Not authorized"}, 401
        elif e.status == 429:
            return { "error": "Spotify rate limit exceeded. Please try again later" }, 429
        else:
            return { "error": "Internal server error. Please contact the developer" }, 500
    except Exception as e:
            return { "error": "Internal server error. Please contact the developer" }, 500
    
    # Map resulting tracks to corresponding playlist
    for playlist, tracks in zip(playlists["playlists"], results):
        playlist.tracks = tracks

    return jsonify(playlists)

# Create Spotify playlists
@playlists_bp.route("/spotify/create", methods=["POST"])
async def create_youtube_playlists():
    if "spotify_credentials" not in session:
        return { "error": "Not authorized" }, 401

    if datetime.datetime.now().timestamp() > session["spotify_credentials"]["expires_at"]:
        session["redirect_origin_url"] = url_for("playlists.create_youtube_playlists")
        return redirect(url_for("oauth.spotify_refresh_token"))
    
    if "playlists" not in request.json:
        return jsonify({ "error": "Request body must contain playlists" }), 400

    playlists = request.json["playlists"]

    try:
        # Create playlists
        create_playlist_tasks = [SpotifyService.create_playlist(playlist["name"], playlist["description"]) for playlist in playlists]
        new_playlist_ids = await asyncio.gather(*create_playlist_tasks)

        # Search tracks
        search_track_tasks = [SpotifyService.search_tracks([track["name"] for track in playlist["tracks"]]) for playlist in playlists]
        track_uris_list = await asyncio.gather(*search_track_tasks)

        # # Add tracks to playlist
        fill_playlist_tasks = [SpotifyService.fill_playlist(playlist_id, track_uris) for playlist_id, track_uris in zip(new_playlist_ids, track_uris_list)]
        fill_playlist_results = await asyncio.gather(*fill_playlist_tasks)
        
    except aiohttp.ClientResponseError as e:
        if e.status == 401:
            return { "error": "Not authorized"}, 401
        elif e.status == 429:
            return { "error": "Spotify rate limit exceeded. Please try again later" }, 429
        else:
            return { "error": "Internal server error. Please contact the developer" }, 500
    except Exception as e:
            return { "error": "Internal server error. Please contact the developer" }, 500

    return jsonify(fill_playlist_results)


# ==================== YOUTUBE ENDPOINTS ====================


# Get all YouTube playlists + tracks
@playlists_bp.route("/youtube")
async def get_youtube_playlists():
    if "youtube_credentials" not in session:
        return jsonify({ "error": "Not authorized"}), 401
    
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
    if credentials.expired:
        session["redirect_origin_url"] = url_for("playlists.get_youtube_playlists")
        return redirect(url_for("oauth.youtube_refresh_token"))
    
    try:
        playlists = await YouTubeService.get_playlists()

        tasks = [YouTubeService.get_playlist_tracks(playlist.id) for playlist in playlists["playlists"]]
        results = await asyncio.gather(*tasks)
    except aiohttp.ClientResponseError as e:
        if e.status == 403:
            # Possible reasons for playlists.list:
            # channelClosed
            # channelSuspended
            # playlistForbidden
            return { "error": "Forbidden"}, e.status
        elif e.status == 404:
            # Possible reasons playlists.list:
            # channelNotFound
            # playlistNotFound
            return { "error": "Not found" }, e.status
        elif e.status == 429:
            return { "error": "YouTube rate limit exceeded. Please try again later" }, e.status
        else:
            return { "error": "Internal server error. Please contact the developer" }, 500
    except Exception as e:
            return { "error": "Internal server error. Please contact the developer" }, 500

    # Map resulting tracks to corresponding playlist
    for playlist, tracks in zip(playlists["playlists"], results):
        playlist.tracks = tracks

    # Filter out empty playlists (playlists not containing music)
    playlists["playlists"] = [playlist for playlist in playlists["playlists"] if playlist.tracks]

    return jsonify(playlists)

# Create a YouTube playlist
@playlists_bp.route("/youtube/create", methods=["POST"])
async def create_youtube_playlist():
    if "youtube_credentials" not in session:
        return jsonify({ "error": "Not authorized"}), 401
    
    credentials = Credentials.from_authorized_user_info(session["youtube_credentials"])
    if credentials.expired:
        session["redirect_origin_url"] = url_for("playlists.create_youtube_playlist")
        return redirect(url_for("oauth.youtube_refresh_token"))
    
    if "playlists" not in request.json:
        return jsonify({ "error": "Request body must contain playlists" }), 400

    playlists = request.json["playlists"]

    try:
        # Create playlists
        create_playlist_tasks = [YouTubeService.create_playlist(playlist["name"], playlist["description"]) for playlist in playlists]
        new_playlist_ids = await asyncio.gather(*create_playlist_tasks)

        # Search tracks
        search_track_tasks = [YouTubeService.search_tracks([track["name"] for track in playlist["tracks"]]) for playlist in playlists]
        video_ids_list = await asyncio.gather(*search_track_tasks)

        # Add tracks to playlist
        fill_playlist_tasks = [YouTubeService.fill_playlist(playlist_id, video_ids) for playlist_id, video_ids in zip(new_playlist_ids, video_ids_list)]
        fill_playlist_results = await asyncio.gather(*fill_playlist_tasks)

    except aiohttp.ClientResponseError as e:
        if e.status == 403:
            # Possible reasons for playlists.list:
            # channelClosed
            # channelSuspended
            # playlistForbidden
            return { "error": "Forbidden"}, e.status
        elif e.status == 404:
            # Possible reasons playlists.list:
            # channelNotFound
            # playlistNotFound
            return { "error": "Not found" }, e.status
        elif e.status == 409:
            return { "error": "Conflict" }, e.status
        elif e.status == 429:
            return { "error": "YouTube rate limit exceeded. Please try again later" }, e.status
        else:
            return { "error": "Internal server error. Please contact the developer" }, 500
    except Exception as e:
            return { "error": "Internal server error. Please contact the developer" }, 500

    return jsonify(fill_playlist_results)

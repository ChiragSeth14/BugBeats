from flask import Flask, redirect, request, jsonify
import os
import requests
from dotenv import load_dotenv
from threading import Timer

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session handling

# Spotify API credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# In-memory token storage (for demonstration purposes)
tokens = {}

@app.route('/')
def home():
    return "Welcome to Flask Spotify App!"

# Spotify Authorization URL
@app.route('/login')
def login():
    scope = "user-read-playback-state user-modify-playback-state"
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

# Callback to exchange code for access token
@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        tokens['access_token'] = data.get('access_token')
        tokens['refresh_token'] = data.get('refresh_token')
        return jsonify({"message": "Logged in successfully!"})
    else:
        return jsonify({"error": "Failed to get token", "details": response.json()})

# Refresh access token
def refresh_access_token(refresh_token):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        return None

# Fetch user's playlists
@app.route('/playlists', methods=['GET'])
def get_playlists():
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')

    if not access_token:
        return jsonify({"error": "User not authenticated. Please log in first."}), 401

    playlists_url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(playlists_url, headers=headers)

    # Handle token expiration
    if response.status_code == 401 and refresh_token:
        new_access_token = refresh_access_token(refresh_token)
        if new_access_token:
            tokens['access_token'] = new_access_token
            headers = {"Authorization": f"Bearer {new_access_token}"}
            response = requests.get(playlists_url, headers=headers)

    if response.status_code == 200:
        playlists = response.json().get("items", [])
        simplified_playlists = [
            {
                "name": playlist["name"],
                "id": playlist["id"],
                "url": playlist["external_urls"]["spotify"],
                "total_tracks": playlist["tracks"]["total"],
            }
            for playlist in playlists
        ]
        return jsonify(simplified_playlists)
    else:
        return jsonify({"error": "Failed to fetch playlists", "details": response.json()}), response.status_code
    
@app.route('/play/<playlist_id>', methods=['PUT'])
def play_playlist(playlist_id):
    access_token = tokens.get('access_token')
    if not access_token:
        return jsonify({"error": "User not authenticated. Please log in first."}), 401

    play_url = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "context_uri": f"spotify:playlist:{playlist_id}"  # Spotify URI for the playlist
    }
    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        return jsonify({"message": f"Playlist {playlist_id} is now playing!"})
    elif response.status_code == 404:
        return jsonify({"error": "No active Spotify device found. Please start Spotify on a device."}), 404
    else:
        return jsonify({"error": "Failed to play playlist", "details": response.json()}), response.status_code


@app.route('/play/track/<track_id>', methods=['PUT'])
def play_track(track_id):
    access_token = tokens.get('access_token')
    if not access_token:
        return jsonify({"error": "User not authenticated. Please log in first."}), 401

    play_url = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "uris": [f"spotify:track:{track_id}"]  # Spotify URI for the track
    }
    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        return jsonify({"message": f"Track {track_id} is now playing!"})
    elif response.status_code == 404:
        return jsonify({"error": "No active Spotify device found. Please start Spotify on a device."}), 404
    else:
        return jsonify({"error": "Failed to play track", "details": response.json()}), response.status_code

@app.route('/vscode/error/<error_code>', methods=['POST'])
def handle_error_event(error_code):
    """Triggered when an error occurs in VS Code."""
    track_mapping = {
        "syntax_error": {"track_uri": "spotify:track:0ee3MUsiFe6mETk4oBgPoG", "start_position_ms": 10000, "stop_time_ms": 24000},
        "name_error": {"track_uri": "spotify:track:59OkvZEB9zPsEa6fQL2LlZ", "start_position_ms": 0, "stop_time_ms": 8000},
        "type_error": {"track_uri": "spotify:track:1VsTvfmPwrJxIP5idldxX7", "start_position_ms": 0, "stop_time_ms": 12000},
        "index_error": {"track_uri": "spotify:track:2mlGPkAx4kwF8Df0GlScsC", "start_position_ms": 16000, "stop_time_ms": 16000},
        "key_error": {"track_uri": "spotify:track:4uLU6hMCjMI75M1A2tKUQC", "start_position_ms": 1000, "stop_time_ms": 18000},
        "unknown_error": {"track_uri": "spotify:track:5QIQWDc5c20Sn5sEUwsqdU", "start_position_ms": 0, "stop_time_ms": 3000},
    }
    track_data = track_mapping.get(error_code, track_mapping["unknown_error"])
    track_uri = track_data["track_uri"]
    start_position_ms = track_data["start_position_ms"]
    stop_time_ms = track_data["stop_time_ms"]
    access_token = tokens.get("access_token")

    if not access_token:
        return jsonify({"error": "No Spotify token available"}), 401

    # Play the track
    play_url = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "uris": [track_uri],
        "position_ms": start_position_ms,
    }

    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        # Schedule a stop
        def stop_playback():
            stop_url = "https://api.spotify.com/v1/me/player/pause"
            stop_response = requests.put(stop_url, headers=headers)

            if stop_response.status_code in [200, 204]:
                # Treat both 200 and 204 as successful pauses
                print("Playback paused successfully.")
            else:
                try:
                    # Attempt to parse response as JSON
                    error_details = stop_response.json()
                except ValueError:
                    # Fallback to raw text if not JSON
                    error_details = stop_response.text
                print(f"Failed to pause playback. Status: {stop_response.status_code}, Details: {error_details}")

        # Schedule the stop time
        Timer(stop_time_ms / 1000, stop_playback).start()

        return jsonify({"message": f"Track {track_uri} is now playing for error {error_code}!"})
    else:
        return jsonify({"error": "Failed to play track", "details": response.json()}), 500
    
@app.route('/vscode/success', methods=['POST'])
def handle_success_event():
    """Triggered when no errors are detected."""
    track_uri = "spotify:track:0O3ow3j5y8q3ykRs2K2n1b"  # Spotify URI for the specific track
    start_position_ms = 45000  # Start time in milliseconds (0:45 = 45000 ms)
    stop_time_ms = 15000  # Play for 15 seconds (45s to 1:00)
    access_token = tokens.get("access_token")

    if not access_token:
        return jsonify({"error": "No Spotify token available"}), 401

    # Play the track
    play_url = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "uris": [track_uri],
        "position_ms": start_position_ms,
    }

    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        # Schedule a stop
        def stop_playback():
            stop_url = "https://api.spotify.com/v1/me/player/pause"
            stop_response = requests.put(stop_url, headers=headers)

            if stop_response.status_code in [200, 204]:
                # Treat both 200 and 204 as successful pauses
                print("Playback paused successfully.")
            else:
                try:
                    # Attempt to parse response as JSON
                    error_details = stop_response.json()
                except ValueError:
                    # Fallback to raw text if not JSON
                    error_details = stop_response.text
                print(f"Failed to pause playback. Status: {stop_response.status_code}, Details: {error_details}")

        # Schedule the stop time
        Timer(stop_time_ms / 1000, stop_playback).start()

        return jsonify({"message": f"Track {track_uri} is now playing from 0:45 for success!"})
    else:
        return jsonify({"error": "Failed to play track", "details": response.json()}), 500

@app.route('/vscode/stop', methods=['POST'])
def stop_playback():
    """Stop Spotify playback."""
    access_token = tokens.get("access_token")

    if not access_token:
        return jsonify({"error": "No Spotify token available"}), 401

    # Check playback state first
    playback_state_url = "https://api.spotify.com/v1/me/player"
    headers = {"Authorization": f"Bearer {access_token}"}
    playback_response = requests.get(playback_state_url, headers=headers)

    if playback_response.status_code == 200:
        playback_data = playback_response.json()
        is_playing = playback_data.get("is_playing", False)

        if not is_playing:
            return jsonify({"message": "No track is currently playing. Nothing to stop."}), 200

    elif playback_response.status_code == 204:
        # 204 means no active device; treat it as no playback
        return jsonify({"message": "No active Spotify device. Nothing to stop."}), 200
    else:
        try:
            error_details = playback_response.json()
        except ValueError:
            error_details = playback_response.text
        return jsonify({"error": "Failed to check playback state", "details": error_details}), playback_response.status_code

    # If playback is active, attempt to stop
    stop_url = "https://api.spotify.com/v1/me/player/pause"
    stop_response = requests.put(stop_url, headers=headers)

    if stop_response.status_code in [200, 204]:
        return jsonify({"message": "Playback stopped successfully!"})
    elif stop_response.status_code == 403:
        try:
            error_details = stop_response.json()
            # Handle restriction-related errors gracefully
            if error_details.get("error", {}).get("reason") == "UNKNOWN":
                return jsonify({"message": "Playback stopped successfully (403 restriction ignored)."}), 200
            else:
                return jsonify({"error": "Failed to stop playback", "details": error_details}), 403
        except ValueError:
            return jsonify({"error": "Failed to stop playback", "details": stop_response.text}), 403
    else:
        try:
            error_details = stop_response.json()
        except ValueError:
            error_details = stop_response.text
        return jsonify({"error": "Failed to stop playback", "details": error_details}), stop_response.status_code

if __name__ == '__main__':
    app.run(debug=True)

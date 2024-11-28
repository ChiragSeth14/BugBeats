from flask import Flask, redirect, request, jsonify
import os
import requests
from dotenv import load_dotenv

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
    
@app.route('/vscode/error', methods=['POST'])
def handle_error_event():
    """Triggered when an error occurs in VS Code."""
    track_uri = "spotify:track:0ee3MUsiFe6mETk4oBgPoG"  # Spotify URI for the specific track
    start_position_ms = 10000  # Start time in milliseconds (10 seconds = 10000 ms)
    access_token = tokens.get("access_token")

    if not access_token:
        return jsonify({"error": "No Spotify token available"}), 401

    play_url = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "uris": [track_uri],
        "position_ms": start_position_ms  # Start track at 10 seconds
    }

    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        return jsonify({"message": f"Track {track_uri} is now playing from 10 seconds!"})
    else:
        return jsonify({"error": "Failed to play track", "details": response.json()}), 500


@app.route('/vscode/success', methods=['POST'])
def handle_success_event():
    """Triggered when no errors are detected."""
    track_uri = "spotify:track:0O3ow3j5y8q3ykRs2K2n1b"  # Spotify URI for the specific track
    start_position_ms = 45000  # Start time in milliseconds (0:45 = 45000 ms)
    access_token = tokens.get("access_token")

    if not access_token:
        return jsonify({"error": "No Spotify token available"}), 401

    play_url = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "uris": [track_uri],
        "position_ms": start_position_ms  # Start track at 0:45
    }

    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        return jsonify({"message": f"Track {track_uri} is now playing from 0:45!"})
    else:
        return jsonify({"error": "Failed to play track", "details": response.json()}), 500





if __name__ == '__main__':
    app.run(debug=True)

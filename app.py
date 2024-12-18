from flask import Flask, redirect, request, jsonify
import os
import requests
from dotenv import load_dotenv
from threading import Timer, Lock
from flask_cors import CORS
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'

# Spotify API credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# Token storage and timers
tokens = {}
active_timer = None
lock = Lock()
TOKEN_FILE = "spotify_tokens.json"


# Load tokens from file
def load_tokens():
    global tokens
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            tokens.update(json.load(f))
    print("Tokens loaded:", tokens)


# Save tokens to file
def save_tokens():
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)
    print("Tokens saved:", tokens)


# Refresh access token
def refresh_access_token(user_id):
    user_tokens = tokens.get(user_id)
    if not user_tokens:
        print(f"No tokens found for user {user_id}")
        return None

    refresh_token = user_tokens.get("refresh_token")
    if not refresh_token:
        print(f"No refresh token for user {user_id}")
        return None

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
        access_token = response.json().get("access_token")
        tokens[user_id]["access_token"] = access_token
        save_tokens()
        return access_token
    else:
        print(f"Failed to refresh token for user {user_id}: {response.json()}")
        return None


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
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')

        # Fetch user info using the access token
        user_info = requests.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        user_id = user_info.get('id')

        if user_id:
            tokens[user_id] = {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            save_tokens()
            return jsonify({"message": "Logged in successfully!", "user_id": user_id})
        else:
            return jsonify({"error": "Failed to fetch user info from Spotify."})
    else:
        return jsonify({"error": "Failed to get token", "details": response.json()})


@app.route('/vscode/check_login_status', methods=['GET'])
def check_login_status():
    if tokens:
        for user_id in tokens.keys():
            return jsonify({"logged_in": True, "user_id": user_id})
    return jsonify({"logged_in": False})


@app.route('/vscode/refresh_token', methods=['POST'])
def manual_refresh_token():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is missing"}), 400

    access_token = refresh_access_token(user_id)
    if access_token:
        return jsonify({"message": "Access token refreshed successfully!"})
    else:
        return jsonify({"error": "Failed to refresh access token"}), 500


@app.route('/vscode/success', methods=['POST'])
def handle_success_event():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is missing"}), 400

    user_tokens = tokens.get(user_id)
    if not user_tokens:
        return jsonify({"error": f"No tokens found for user {user_id}"}), 401

    access_token = user_tokens.get("access_token")
    if not access_token:
        access_token = refresh_access_token(user_id)
        if not access_token:
            return jsonify({"error": "No valid access token available"}), 401

    # Fetch active devices
    devices_url = "https://api.spotify.com/v1/me/player/devices"
    headers = {"Authorization": f"Bearer {access_token}"}
    devices_response = requests.get(devices_url, headers=headers)

    if devices_response.status_code != 200:
        return jsonify({"error": "Failed to fetch devices", "details": devices_response.json()}), 500

    devices = devices_response.json().get("devices", [])
    if not devices:
        return jsonify({"error": "No active devices found for the user"}), 404

    # Use the first available device
    target_device_id = devices[0]["id"]

    # Play the track
    play_url = "https://api.spotify.com/v1/me/player/play"
    payload = {
        "uris": ["spotify:track:0O3ow3j5y8q3ykRs2K2n1b"],
        "device_id": target_device_id,
        "position_ms": 45000
    }
    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        global active_timer
        with lock:
            if active_timer:
                active_timer.cancel()

        def stop_playback():
            stop_url = "https://api.spotify.com/v1/me/player/pause"
            requests.put(stop_url, headers=headers, params={"device_id": target_device_id})

        with lock:
            active_timer = Timer(15, stop_playback)
            active_timer.start()

        return jsonify({"message": f"Success track playing for user {user_id}"})
    else:
        return jsonify({"error": "Failed to play success track", "details": response.json()}), 500


@app.route('/vscode/error/<error_code>', methods=['POST'])
def handle_error_event(error_code):
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is missing"}), 400

    user_tokens = tokens.get(user_id)
    if not user_tokens:
        return jsonify({"error": f"No tokens found for user {user_id}"}), 401

    access_token = user_tokens.get("access_token")
    if not access_token:
        access_token = refresh_access_token(user_id)
        if not access_token:
            return jsonify({"error": "No valid access token available"}), 401

    track_mapping = {
        "syntax_error": {"track_uri": "spotify:track:0ee3MUsiFe6mETk4oBgPoG", "start_position_ms": 10000, "stop_time_ms": 24000},
        "name_error": {"track_uri": "spotify:track:59OkvZEB9zPsEa6fQL2LlZ", "start_position_ms": 0, "stop_time_ms": 8000},
        "type_error": {"track_uri": "spotify:track:1VsTvfmPwrJxIP5idldxX7", "start_position_ms": 0, "stop_time_ms": 12000},
        "index_error": {"track_uri": "spotify:track:2mlGPkAx4kwF8Df0GlScsC", "start_position_ms": 16000, "stop_time_ms": 16000},
        "key_error": {"track_uri": "spotify:track:4uLU6hMCjMI75M1A2tKUQC", "start_position_ms": 1000, "stop_time_ms": 18000},
        "unknown_error": {"track_uri": "spotify:track:5QIQWDc5c20Sn5sEUwsqdU", "start_position_ms": 0, "stop_time_ms": 3000}
    }

    track_data = track_mapping.get(error_code, track_mapping["unknown_error"])
    track_uri = track_data["track_uri"]
    start_position_ms = track_data["start_position_ms"]
    stop_time_ms = track_data["stop_time_ms"]

    devices_url = "https://api.spotify.com/v1/me/player/devices"
    headers = {"Authorization": f"Bearer {access_token}"}
    devices_response = requests.get(devices_url, headers=headers)

    if devices_response.status_code != 200:
        return jsonify({"error": "Failed to fetch devices", "details": devices_response.json()}), 500

    devices = devices_response.json().get("devices", [])
    if not devices:
        return jsonify({"error": "No active devices found for the user"}), 404

    target_device_id = devices[0]["id"]

    play_url = "https://api.spotify.com/v1/me/player/play"
    payload = {
        "uris": [track_uri],
        "device_id": target_device_id,
        "position_ms": start_position_ms
    }
    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        global active_timer
        with lock:
            if active_timer:
                active_timer.cancel()

        def stop_playback():
            stop_url = "https://api.spotify.com/v1/me/player/pause"
            requests.put(stop_url, headers=headers, params={"device_id": target_device_id})

        with lock:
            active_timer = Timer(stop_time_ms / 1000, stop_playback)
            active_timer.start()

        return jsonify({"message": f"Error track playing for user {user_id} and error {error_code}"})
    else:
        return jsonify({"error": "Failed to play error track", "details": response.json()}), 500


@app.route('/vscode/stop', methods=['POST'])
def stop_playback():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is missing"}), 400

    user_tokens = tokens.get(user_id)
    if not user_tokens:
        return jsonify({"error": f"No tokens found for user {user_id}"}), 401

    access_token = user_tokens.get("access_token")
    if not access_token:
        access_token = refresh_access_token(user_id)
        if not access_token:
            return jsonify({"error": "No valid access token available"}), 401

    stop_url = "https://api.spotify.com/v1/me/player/pause"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(stop_url, headers=headers)

    if response.status_code in [200, 204]:
        return jsonify({"message": f"Playback stopped for user {user_id}"})
    else:
        return jsonify({"error": "Failed to stop playback", "details": response.json()}), 500


if __name__ == '__main__':
    load_tokens()
    app.run(debug=True)

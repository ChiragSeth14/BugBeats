# from flask import Flask, redirect, request, jsonify
# import os
# import requests
# from dotenv import load_dotenv
# from threading import Timer, Lock
# import json

# # Load environment variables
# load_dotenv()

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'  # Required for session handling

# # Spotify API credentials
# CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
# CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
# REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# # Token storage and timers
# tokens = {}
# active_timer = None  # Store the active timer
# active_track_uri = None  # Store the currently playing track URI
# lock = Lock()  # To ensure thread safety when updating playback context
# TOKEN_FILE = "spotify_tokens.json"  # File to persist tokens


# # Load tokens from file
# def load_tokens():
#     global tokens
#     if os.path.exists(TOKEN_FILE):
#         with open(TOKEN_FILE, "r") as f:
#             tokens.update(json.load(f))


# # Save tokens to file
# def save_tokens():
#     with open(TOKEN_FILE, "w") as f:
#         json.dump(tokens, f)

# def get_user_tokens(user_id):
#     return tokens.get(user_id)

# # Refresh tokens before the server starts handling requests
# @app.before_request
# def initialize_tokens():
#     if not tokens:
#         load_tokens()
#     refresh_token = tokens.get("refresh_token")
#     if refresh_token and "access_token" not in tokens:
#         refresh_access_token(refresh_token)


# @app.route('/')
# def home():
#     return "Welcome to Flask Spotify App!"


# # Spotify Authorization URL
# @app.route('/login')
# def login():
#     scope = "user-read-playback-state user-modify-playback-state"
#     auth_url = (
#         f"https://accounts.spotify.com/authorize"
#         f"?client_id={CLIENT_ID}"
#         f"&response_type=code"
#         f"&redirect_uri={REDIRECT_URI}"
#         f"&scope={scope}"
#     )
#     return redirect(auth_url)


# @app.route('/callback')
# def callback():
#     code = request.args.get('code')
#     token_url = "https://accounts.spotify.com/api/token"
#     payload = {
#         "grant_type": "authorization_code",
#         "code": code,
#         "redirect_uri": REDIRECT_URI,
#         "client_id": CLIENT_ID,
#         "client_secret": CLIENT_SECRET,
#     }
#     headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     response = requests.post(token_url, data=payload, headers=headers)

#     if response.status_code == 200:
#         data = response.json()
#         access_token = data.get('access_token')

#         # Get user info from Spotify
#         user_info = requests.get(
#             "https://api.spotify.com/v1/me",
#             headers={"Authorization": f"Bearer {access_token}"}
#         ).json()

#         user_id = user_info.get('id')  # Unique Spotify user ID

#         # Store tokens by user ID
#         tokens[user_id] = {
#             "access_token": access_token,
#             "refresh_token": data.get('refresh_token')
#         }
#         save_tokens()  # Save tokens to file

#         return jsonify({"message": "Logged in successfully!", "user_id": user_id})
#     else:
#         return jsonify({"error": "Failed to get token", "details": response.json()})


# # Refresh access token
# def refresh_access_token(refresh_token):
#     token_url = "https://accounts.spotify.com/api/token"
#     payload = {
#         "grant_type": "refresh_token",
#         "refresh_token": refresh_token,
#         "client_id": CLIENT_ID,
#         "client_secret": CLIENT_SECRET,
#     }
#     headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     response = requests.post(token_url, data=payload, headers=headers)

#     if response.status_code == 200:
#         tokens['access_token'] = response.json().get('access_token')
#         save_tokens()  # Save refreshed token
#         return tokens['access_token']
#     else:
#         print("Failed to refresh token:", response.json())
#         return None


# @app.route('/vscode/refresh_token', methods=['POST'])
# def manual_refresh_token():
#     refresh_token = tokens.get("refresh_token")
#     if not refresh_token:
#         return jsonify({"error": "No refresh token available"}), 401

#     new_access_token = refresh_access_token(refresh_token)
#     if new_access_token:
#         return jsonify({"message": "Access token refreshed successfully!"})
#     else:
#         return jsonify({"error": "Failed to refresh access token"}), 500


# @app.route('/vscode/check_login_status', methods=['GET'])
# def check_login_status():
#     if 'access_token' in tokens:
#         return jsonify({"logged_in": True})
#     return jsonify({"logged_in": False})


# # Handle success event and play a specific track
# @app.route('/vscode/success', methods=['POST'])
# def handle_success_event():
#     """Triggered when no errors are detected."""
#     track_uri = "spotify:track:0O3ow3j5y8q3ykRs2K2n1b"  # Spotify URI for success track
#     start_position_ms = 45000  # Start time in milliseconds (0:45 = 45000 ms)
#     stop_time_ms = 15000  # Play for 15 seconds
#     access_token = tokens.get("access_token")

#     if not access_token:
#         return jsonify({"error": "No Spotify token available"}), 401

#     # Play the track
#     play_url = "https://api.spotify.com/v1/me/player/play"
#     headers = {"Authorization": f"Bearer {access_token}"}
#     payload = {
#         "uris": [track_uri],
#         "position_ms": start_position_ms,
#     }

#     response = requests.put(play_url, headers=headers, json=payload)

#     if response.status_code == 204:
#         global active_timer, active_track_uri

#         # Cancel the existing timer if any
#         with lock:
#             if active_timer:
#                 active_timer.cancel()
#             active_track_uri = track_uri  # Update the active track

#         # Schedule the stop for the current track
#         def stop_playback():
#             with lock:
#                 if active_track_uri != track_uri:
#                     print("Skipping pause for non-active track.")
#                     return

#             stop_url = "https://api.spotify.com/v1/me/player/pause"
#             stop_response = requests.put(stop_url, headers=headers)

#             if stop_response.status_code in [200, 204]:
#                 print("Playback paused successfully.")
#             else:
#                 print(f"Failed to pause playback. Status: {stop_response.status_code}, Details: {stop_response.json()}")

#         with lock:
#             active_timer = Timer(stop_time_ms / 1000, stop_playback)
#             active_timer.start()

#         return jsonify({"message": f"Success track is now playing from 0:45 for success!"})
#     else:
#         return jsonify({"error": "Failed to play success track", "details": response.json()}), 500


# # Handle error event and play tracks for specific errors
# @app.route('/vscode/error/<error_code>', methods=['POST'])
# def handle_error_event(error_code):
#     """Triggered when an error occurs in VS Code."""
#     track_mapping = {
#         "syntax_error": {"track_uri": "spotify:track:0ee3MUsiFe6mETk4oBgPoG", "start_position_ms": 10000, "stop_time_ms": 24000},
#         "name_error": {"track_uri": "spotify:track:59OkvZEB9zPsEa6fQL2LlZ", "start_position_ms": 0, "stop_time_ms": 8000},
#         "type_error": {"track_uri": "spotify:track:1VsTvfmPwrJxIP5idldxX7", "start_position_ms": 0, "stop_time_ms": 12000},
#         "index_error": {"track_uri": "spotify:track:2mlGPkAx4kwF8Df0GlScsC", "start_position_ms": 16000, "stop_time_ms": 16000},
#         "key_error": {"track_uri": "spotify:track:4uLU6hMCjMI75M1A2tKUQC", "start_position_ms": 1000, "stop_time_ms": 18000},
#         "unknown_error": {"track_uri": "spotify:track:5QIQWDc5c20Sn5sEUwsqdU", "start_position_ms": 0, "stop_time_ms": 3000}
#     }

#     track_data = track_mapping.get(error_code, track_mapping["unknown_error"])
#     track_uri = track_data["track_uri"]
#     start_position_ms = track_data["start_position_ms"]
#     stop_time_ms = track_data["stop_time_ms"]
#     access_token = tokens.get("access_token")

#     if not access_token:
#         return jsonify({"error": "No Spotify token available"}), 401

#     # Play the track
#     play_url = "https://api.spotify.com/v1/me/player/play"
#     headers = {"Authorization": f"Bearer {access_token}"}
#     payload = {
#         "uris": [track_uri],
#         "position_ms": start_position_ms,
#     }

#     response = requests.put(play_url, headers=headers, json=payload)

#     if response.status_code == 204:
#         global active_timer, active_track_uri

#         # Cancel the existing timer if any
#         with lock:
#             if active_timer:
#                 active_timer.cancel()
#             active_track_uri = track_uri  # Update the active track

#         # Schedule the stop for the current track
#         def stop_playback():
#             with lock:
#                 if active_track_uri != track_uri:
#                     print("Skipping pause for non-active track.")
#                     return

#             stop_url = "https://api.spotify.com/v1/me/player/pause"
#             stop_response = requests.put(stop_url, headers=headers)

#             if stop_response.status_code in [200, 204]:
#                 print("Playback paused successfully.")
#             else:
#                 print(f"Failed to pause playback. Status: {stop_response.status_code}, Details: {stop_response.json()}")

#         with lock:
#             active_timer = Timer(stop_time_ms / 1000, stop_playback)
#             active_timer.start()

#         return jsonify({"message": f"Track {track_uri} is now playing for error {error_code}!"})
#     else:
#         return jsonify({"error": "Failed to play track", "details": response.json()}), 500


# @app.route('/vscode/stop', methods=['POST'])
# def stop_playback():
#     """Stop Spotify playback."""
#     access_token = tokens.get("access_token")
#     if not access_token:
#         return jsonify({"error": "No Spotify token available"}), 401

#     # Stop the current playback
#     stop_url = "https://api.spotify.com/v1/me/player/pause"
#     headers = {"Authorization": f"Bearer {access_token}"}
#     response = requests.put(stop_url, headers=headers)

#     with lock:
#         global active_timer, active_track_uri
#         if active_timer:
#             active_timer.cancel()  # Cancel any active timers
#             active_timer = None
#         active_track_uri = None  # Reset active track

#     if response.status_code in [200, 204]:
#         return jsonify({"message": "Playback stopped successfully!"})
#     elif response.status_code == 403:
#         # Handle 403 restrictions gracefully
#         return jsonify({"message": "Playback stopped successfully!"}), 200
#     else:
#         try:
#             error_details = response.json()
#         except ValueError:
#             error_details = response.text
#         return jsonify({"error": "Failed to stop playback", "details": error_details}), response.status_code


# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, redirect, request, jsonify
import os
import requests
from dotenv import load_dotenv
from threading import Timer, Lock
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session handling

# Spotify API credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# Token storage and timers
tokens = {}  # Now stores tokens per user ID
active_timer = None  # Store the active timer
active_track_uri = None  # Store the currently playing track URI
lock = Lock()  # To ensure thread safety when updating playback context
TOKEN_FILE = "spotify_tokens.json"  # File to persist tokens


# Load tokens from file
def load_tokens():
    global tokens
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            tokens.update(json.load(f))


# Save tokens to file
def save_tokens():
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)


# Retrieve tokens for a specific user ID
def get_user_tokens(user_id):
    return tokens.get(user_id)


# Refresh tokens before the server starts handling requests
@app.before_request
def initialize_tokens():
    if not tokens:
        load_tokens()


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

        # Get user info from Spotify
        user_info = requests.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        user_id = user_info.get('id')  # Unique Spotify user ID

        # Store tokens by user ID
        tokens[user_id] = {
            "access_token": access_token,
            "refresh_token": data.get('refresh_token')
        }
        save_tokens()  # Save tokens to file

        return jsonify({"message": "Logged in successfully!", "user_id": user_id})
    else:
        return jsonify({"error": "Failed to get token", "details": response.json()})


# Refresh access token
def refresh_access_token(user_id):
    user_tokens = get_user_tokens(user_id)
    if not user_tokens:
        return None

    refresh_token = user_tokens.get("refresh_token")
    if not refresh_token:
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
        user_tokens["access_token"] = response.json().get("access_token")
        save_tokens()  # Save refreshed token
        return user_tokens["access_token"]
    else:
        print("Failed to refresh token:", response.json())
        return None


@app.route('/vscode/refresh_token', methods=['POST'])
def manual_refresh_token():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "No user ID provided"}), 400

    new_access_token = refresh_access_token(user_id)
    if new_access_token:
        return jsonify({"message": "Access token refreshed successfully!"})
    else:
        return jsonify({"error": "Failed to refresh access token"}), 500


@app.route('/vscode/check_login_status', methods=['POST'])
def check_login_status():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "No user ID provided"}), 400

    user_tokens = get_user_tokens(user_id)
    if user_tokens and "access_token" in user_tokens:
        return jsonify({"logged_in": True})
    return jsonify({"logged_in": False})


# Handle success event and play a specific track
@app.route('/vscode/success', methods=['POST'])
def handle_success_event():
    data = request.json
    user_id = data.get("user_id")
    track_uri = "spotify:track:0O3ow3j5y8q3ykRs2K2n1b"  # Spotify URI for success track
    start_position_ms = 45000  # Start time in milliseconds (0:45 = 45000 ms)
    stop_time_ms = 15000  # Play for 15 seconds

    user_tokens = get_user_tokens(user_id)
    if not user_tokens:
        return jsonify({"error": "No Spotify token available"}), 401

    access_token = user_tokens.get("access_token")
    play_url = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "uris": [track_uri],
        "position_ms": start_position_ms,
    }

    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        global active_timer, active_track_uri

        # Cancel the existing timer if any
        with lock:
            if active_timer:
                active_timer.cancel()
            active_track_uri = track_uri  # Update the active track

        # Schedule the stop for the current track
        def stop_playback():
            with lock:
                if active_track_uri != track_uri:
                    return

            stop_url = "https://api.spotify.com/v1/me/player/pause"
            stop_response = requests.put(stop_url, headers=headers)

        with lock:
            active_timer = Timer(stop_time_ms / 1000, stop_playback)
            active_timer.start()

        return jsonify({"message": "Success track is now playing from 0:45 for success!"})
    else:
        return jsonify({"error": "Failed to play success track", "details": response.json()}), 500


# Handle error event and play tracks for specific errors
@app.route('/vscode/error/<error_code>', methods=['POST'])
def handle_error_event(error_code):
    data = request.json
    user_id = data.get("user_id")

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

    user_tokens = get_user_tokens(user_id)
    if not user_tokens:
        return jsonify({"error": "No Spotify token available"}), 401

    access_token = user_tokens.get("access_token")
    play_url = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "uris": [track_uri],
        "position_ms": start_position_ms,
    }

    response = requests.put(play_url, headers=headers, json=payload)

    if response.status_code == 204:
        global active_timer, active_track_uri

        # Cancel the existing timer if any
        with lock:
            if active_timer:
                active_timer.cancel()
            active_track_uri = track_uri  # Update the active track

        # Schedule the stop for the current track
        def stop_playback():
            with lock:
                if active_track_uri != track_uri:
                    return

            stop_url = "https://api.spotify.com/v1/me/player/pause"
            requests.put(stop_url, headers=headers)

        with lock:
            active_timer = Timer(stop_time_ms / 1000, stop_playback)
            active_timer.start()

        return jsonify({"message": f"Track {track_uri} is now playing for error {error_code}!"})
    else:
        return jsonify({"error": "Failed to play track", "details": response.json()}), 500


if __name__ == '__main__':
    app.run(debug=True)


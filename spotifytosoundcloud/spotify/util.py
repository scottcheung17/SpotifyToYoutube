import spotipy
from spotipy.oauth2 import SpotifyOAuth
from .credentials import CLIENT_SECRET, CLIENT_ID

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = 'http://127.0.0.1:8000/redirect', 
        scope = 'user-library-read playlist-read-private playlist-read-collaborative'
    )


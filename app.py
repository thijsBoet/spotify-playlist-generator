import datetime
import logging
import os
import json
import argparse

import openai
import spotipy

from dotenv import dotenv_values
config = dotenv_values(".env")
openai.api_key = config["OPEN_AI_API_KEY"]

parser = argparse.ArgumentParser(description="Generate a Spotify playlist based on a prompt.")
parser.add_argument("-p", type=str, help="Prompt to generate a playlist from openAI.")
parser.add_argument("-n", type=int, default=10, help="The number of songs to add to the playlist.")

args = parser.parse_args()

def get_playlist(prompt, count=10):
    example_json = """
    [
        {"song": "Hurt", "artist": "Johnny Cash"},
        {"song": "Someone Like You", "artist": "Adele"},
        {"song": "Tears in Heaven", "artist": "Eric Clapton"},
        {"song": "Nothing Compares 2 U", "artist": "Sinead O'Connor"},
        {"song": "Hallelujah", "artist": "Jeff Buckley"},
        {"song": "Everybody Hurts", "artist": "R.E.M."},
        {"song": "Hurt", "artist": "Nine Inch Nails"},
        {"song": "Fix You", "artist": "Coldplay"},
        {"song": "The Sound of Silence", "artist": "Simon & Garfunkel"},
        {"song": "Yesterday", "artist": "The Beatles"}
    ]
    """

    messages = [
        {"role": "system", "content": """You are a helpful playlist generating assistant.
        You should generate a list of songs and their artists according to a text prompt.
        Your should return a JSON array, where each element follows the format: [{"song": <song_title>, "artist": <artist_name>}]
        """},
        {"role": "user", "content": """Generate a playlist of 10 songs on this prompt: very sad songs"""},
        {"role": "assistant", "content": example_json},
        {"role": "user", "content": f"Generate a playlist of {count} songs on this prompt: {prompt}"},
    ]

    response = openai.ChatCompletion.create(
        messages=messages,
        model="gpt-3.5-turbo",
        max_tokens=400
    )

    playlist = json.loads(response.choices[0].message.content)
    return playlist


playlist = get_playlist(args.p, args.n)
print(playlist)

sp = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
        client_id=config["SPOTIFY_CLIENT_ID"],
        client_secret=config["SPOTIFY_CLIENT_SECRET"],
        redirect_uri="http://localhost:9999",
        scope="playlist-modify-private",
        # playlist-modify-public
    )
)

current_user = sp.current_user()

track_ids = []
assert current_user is not None

for item in playlist:
    artist, song = item["artist"], item["song"]
    query = f"{song} {artist}"
    search_results = sp.search(q=query, type="track", limit=10)
    track_ids.append(search_results["tracks"]["items"][0]["id"])

created_playlist = sp.user_playlist_create(
    current_user["id"],
    public=False,
    name=args.p.capitalize(),
)

sp.user_playlist_add_tracks(
    current_user["id"],
    created_playlist["id"],
    track_ids
)
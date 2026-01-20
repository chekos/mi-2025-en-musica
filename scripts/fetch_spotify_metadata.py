"""
Extrae metadata enriquecida de Spotify para tracks y artistas.
Guarda álbumes, artistas con géneros, popularidad, etc.

Uso:
    uv run --with requests scripts/fetch_spotify_metadata.py
"""

import json
import os
import time
from collections import defaultdict
from pathlib import Path

import requests

# Rutas
ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "streaming_history_2025.json"
OUTPUT_FILE = ROOT / "data" / "spotify-metadata.json"

# Credenciales desde variables de entorno
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError(
        "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables."
    )


def get_access_token() -> str:
    """Obtiene token de acceso de Spotify."""
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    return response.json()["access_token"]


def load_streaming_history() -> list[dict]:
    """Carga el historial de streaming."""
    with open(DATA_FILE) as f:
        return json.load(f)


def extract_unique_tracks(history: list[dict]) -> dict[str, dict]:
    """Extrae tracks únicos con estadísticas agregadas."""
    tracks = defaultdict(lambda: {
        "ms_played": 0,
        "play_count": 0,
        "track_name": "",
        "artist_name": "",
        "album_name": "",
    })

    for item in history:
        uri = item.get("spotify_track_uri")
        if not uri or not uri.startswith("spotify:track:"):
            continue

        track_id = uri.split(":")[-1]
        tracks[track_id]["ms_played"] += item.get("ms_played", 0)
        tracks[track_id]["play_count"] += 1
        tracks[track_id]["track_name"] = item.get("master_metadata_track_name", "")
        tracks[track_id]["artist_name"] = item.get("master_metadata_album_artist_name", "")
        tracks[track_id]["album_name"] = item.get("master_metadata_album_album_name", "")

    return dict(tracks)


def fetch_tracks_batch(track_ids: list[str], headers: dict) -> list[dict]:
    """Obtiene información de hasta 50 tracks a la vez."""
    if not track_ids:
        return []

    response = requests.get(
        "https://api.spotify.com/v1/tracks",
        params={"ids": ",".join(track_ids[:50])},
        headers=headers,
    )

    if response.status_code != 200:
        print(f"  Error fetching tracks: {response.status_code}")
        return []

    return response.json().get("tracks", [])


def fetch_artists_batch(artist_ids: list[str], headers: dict) -> list[dict]:
    """Obtiene información de hasta 50 artistas a la vez."""
    if not artist_ids:
        return []

    response = requests.get(
        "https://api.spotify.com/v1/artists",
        params={"ids": ",".join(artist_ids[:50])},
        headers=headers,
    )

    if response.status_code != 200:
        print(f"  Error fetching artists: {response.status_code}")
        return []

    return response.json().get("artists", [])


def main():
    print("Cargando historial de streaming...")
    history = load_streaming_history()

    print("Extrayendo tracks únicos...")
    unique_tracks = extract_unique_tracks(history)
    print(f"  {len(unique_tracks)} tracks únicos encontrados")

    print("\nObteniendo token de Spotify...")
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch track details in batches
    print("\nObteniendo detalles de tracks...")
    track_ids = list(unique_tracks.keys())
    all_track_data = []

    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i+50]
        print(f"  Batch {i//50 + 1}/{(len(track_ids)-1)//50 + 1} ({len(batch)} tracks)")
        tracks_data = fetch_tracks_batch(batch, headers)
        all_track_data.extend(tracks_data)
        time.sleep(0.1)  # Rate limiting

    # Extract unique artists and albums
    artists_map = {}
    albums_map = {}
    tracks_enriched = []

    for track in all_track_data:
        if not track:
            continue

        track_id = track["id"]
        local_stats = unique_tracks.get(track_id, {})

        # Collect artist IDs
        for artist in track.get("artists", []):
            artists_map[artist["id"]] = artist["name"]

        # Collect album info
        album = track.get("album", {})
        album_id = album.get("id")
        if album_id and album_id not in albums_map:
            albums_map[album_id] = {
                "id": album_id,
                "name": album.get("name"),
                "album_type": album.get("album_type"),
                "release_date": album.get("release_date"),
                "total_tracks": album.get("total_tracks"),
                "images": album.get("images", []),
                "artist_ids": [a["id"] for a in album.get("artists", [])],
                "artist_names": [a["name"] for a in album.get("artists", [])],
            }

        # Enrich track data
        tracks_enriched.append({
            "id": track_id,
            "name": track.get("name"),
            "popularity": track.get("popularity"),
            "duration_ms": track.get("duration_ms"),
            "explicit": track.get("explicit"),
            "track_number": track.get("track_number"),
            "album_id": album_id,
            "artist_ids": [a["id"] for a in track.get("artists", [])],
            "artist_names": [a["name"] for a in track.get("artists", [])],
            # Stats from listening history
            "ms_played": local_stats.get("ms_played", 0),
            "play_count": local_stats.get("play_count", 0),
        })

    # Fetch artist details in batches
    print(f"\nObteniendo detalles de {len(artists_map)} artistas...")
    artist_ids = list(artists_map.keys())
    artists_enriched = {}

    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i+50]
        print(f"  Batch {i//50 + 1}/{(len(artist_ids)-1)//50 + 1} ({len(batch)} artistas)")
        artists_data = fetch_artists_batch(batch, headers)

        for artist in artists_data:
            if artist:
                artists_enriched[artist["id"]] = {
                    "id": artist["id"],
                    "name": artist["name"],
                    "genres": artist.get("genres", []),
                    "popularity": artist.get("popularity"),
                    "followers": artist.get("followers", {}).get("total", 0),
                    "images": artist.get("images", []),
                }

        time.sleep(0.1)

    # Add listening stats to albums
    album_stats = defaultdict(lambda: {"ms_played": 0, "play_count": 0})
    for track in tracks_enriched:
        album_id = track.get("album_id")
        if album_id:
            album_stats[album_id]["ms_played"] += track["ms_played"]
            album_stats[album_id]["play_count"] += track["play_count"]

    for album_id, stats in album_stats.items():
        if album_id in albums_map:
            albums_map[album_id]["ms_played"] = stats["ms_played"]
            albums_map[album_id]["play_count"] = stats["play_count"]

    # Add listening stats to artists
    artist_stats = defaultdict(lambda: {"ms_played": 0, "play_count": 0})
    for track in tracks_enriched:
        for artist_id in track.get("artist_ids", []):
            artist_stats[artist_id]["ms_played"] += track["ms_played"]
            artist_stats[artist_id]["play_count"] += track["play_count"]

    for artist_id, stats in artist_stats.items():
        if artist_id in artists_enriched:
            artists_enriched[artist_id]["ms_played"] = stats["ms_played"]
            artists_enriched[artist_id]["play_count"] = stats["play_count"]

    # Build final output
    output = {
        "tracks": tracks_enriched,
        "albums": list(albums_map.values()),
        "artists": list(artists_enriched.values()),
        "metadata": {
            "total_tracks": len(tracks_enriched),
            "total_albums": len(albums_map),
            "total_artists": len(artists_enriched),
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    }

    print(f"\nGuardando en {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n¡Listo!")
    print(f"  {output['metadata']['total_tracks']} tracks")
    print(f"  {output['metadata']['total_albums']} álbumes")
    print(f"  {output['metadata']['total_artists']} artistas")


if __name__ == "__main__":
    main()

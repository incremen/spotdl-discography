#!/usr/bin/env python3
"""
download_artist.py

Downloads a Spotify artist's full discography as MP3s, organized into folders.

Usage:
    .venv/bin/python3 download_artist.py <spotify_artist_url> [output_dir]

Example:
    .venv/bin/python3 download_artist.py "https://open.spotify.com/artist/2uYWxilOVlUdk4oV9DvwqK"
    .venv/bin/python3 download_artist.py "https://open.spotify.com/artist/2uYWxilOVlUdk4oV9DvwqK" ~/Music

How to get the artist URL:
    Open Spotify → right-click the artist name → Share → Copy link to artist

See README.md for full setup (credentials, VPN, etc.)
"""

import sys
import importlib.util
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()

# ── Spotify app credentials ───────────────────────────────────────────────────
# Create a .env file in this directory with:
#   SPOTIFY_CLIENT_ID=your_id_here
#   SPOTIFY_CLIENT_SECRET=your_secret_here
# Get credentials at: https://developer.spotify.com/dashboard
CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

# ── Output folder structure ───────────────────────────────────────────────────
# Output path is: <output_dir>/Artist/Album/01 - Track Title.mp3
# output_dir defaults to "downloads" if not passed as a second argument.
OUTPUT_TEMPLATE = "{artist}/{album}/{track-number} - {title}.{output-ext}"
DEFAULT_OUTPUT_DIR = "downloads"

# ── Patches ───────────────────────────────────────────────────────────────────
# Spotify's free-tier (Development Mode) API omits certain fields and enforces
# a lower page-size limit — both of which crash spotdl out of the box.
# These patches are applied to the library files before running spotdl and
# reverted automatically when done, so the library stays clean between runs.

PATCHES = [
    {
        "module": "spotipy.client",
        "find":    "self, artist_id, album_type=None, include_groups=None, country=None, limit=20, offset=0",
        "replace": "self, artist_id, album_type=None, include_groups=None, country=None, limit=10, offset=0",
        "reason":  "Dev Mode caps artist_albums page size at 10 (default is 20)",
    },
    {
        "module": "spotdl.types.album",
        "find":    'publisher=album_metadata["label"]',
        "replace": 'publisher=album_metadata.get("label", "")',
        "reason":  "Dev Mode omits 'label' from album metadata",
    },
    {
        "module": "spotdl.types.artist",
        "find":    '"genres": raw_artist_meta["genres"]',
        "replace": '"genres": raw_artist_meta.get("genres", [])',
        "reason":  "Dev Mode omits 'genres' from artist metadata",
    },
    {
        "module": "spotdl.types.song",
        "find":    'genres=raw_album_meta["genres"] + raw_artist_meta["genres"]',
        "replace": 'genres=raw_album_meta.get("genres", []) + raw_artist_meta.get("genres", [])',
        "reason":  "Dev Mode omits 'genres' from song metadata",
    },
    {
        "module": "spotdl.types.song",
        "find":    'publisher=raw_album_meta["label"]',
        "replace": 'publisher=raw_album_meta.get("label", "")',
        "reason":  "Dev Mode omits 'label' from song metadata",
    },
    {
        "module": "spotdl.types.song",
        "find":    'popularity=raw_track_meta["popularity"]',
        "replace": 'popularity=raw_track_meta.get("popularity", 0)',
        "reason":  "Dev Mode omits 'popularity' from track metadata",
    },
]


def get_lib_path(module_name):
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise RuntimeError(f"Cannot find module: {module_name}")
    return spec.origin


def apply_patches():
    applied = []
    print("Applying patches for Spotify Development Mode compatibility...")
    for patch in PATCHES:
        path = get_lib_path(patch["module"])
        with open(path, "r") as f:
            content = f.read()
        if patch["find"] in content:
            patched = content.replace(patch["find"], patch["replace"])
            with open(path, "w") as f:
                f.write(patched)
            applied.append((path, patch["find"], patch["replace"]))
            print(f"  + {patch['reason']}")
        elif patch["replace"] in content:
            print(f"  = Already applied (will still revert): {patch['reason']}")
            applied.append((path, patch["find"], patch["replace"]))
        else:
            print(f"  ! Could not patch ({path}): {patch['reason']}")
            print("    spotdl may have been updated — check README troubleshooting.")
            revert_patches(applied)
            sys.exit(1)
    print()
    return applied


def revert_patches(applied):
    print("\nReverting library patches...")
    for path, original, replacement in applied:
        with open(path, "r") as f:
            content = f.read()
        with open(path, "w") as f:
            f.write(content.replace(replacement, original))
    print("  Done — library files restored to original state.")


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET are not set.")
        print("Create a .env file in this directory with:")
        print("  SPOTIFY_CLIENT_ID=your_id_here")
        print("  SPOTIFY_CLIENT_SECRET=your_secret_here")
        print("Get credentials at: https://developer.spotify.com/dashboard")
        sys.exit(1)

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    artist_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR
    output_format = os.path.join(output_dir, OUTPUT_TEMPLATE)

    os.makedirs(output_dir, exist_ok=True)

    if "open.spotify.com" not in artist_url:
        print(f"Error: doesn't look like a Spotify URL: {artist_url}")
        print("Example: https://open.spotify.com/artist/2uYWxilOVlUdk4oV9DvwqK")
        sys.exit(1)

    applied = apply_patches()
    try:
        cmd = [
            sys.executable, "-m", "spotdl", artist_url,
            "--client-id",     CLIENT_ID,
            "--client-secret", CLIENT_SECRET,
            "--output",        output_format,
        ]
        print(f"Running: spotdl {artist_url}\n", flush=True)
        subprocess.run(cmd, check=False)
    finally:
        revert_patches(applied)


if __name__ == "__main__":
    main()

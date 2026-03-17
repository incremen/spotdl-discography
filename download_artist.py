#!/usr/bin/env python3
"""
download_artist.py

Downloads a Spotify artist's full discography using spotdl.
Applies runtime patches to work around Spotify Development Mode API restrictions,
then reverts the library files back to their original state when done.

Usage:
    python3 download_artist.py "https://open.spotify.com/artist/ARTIST_ID"

See README.md for full setup instructions.
"""

import sys
import importlib.util
import subprocess

# Run spotdl via the same Python that's running this script (venv-aware)
PYTHON = sys.executable

# ── Spotify app credentials ───────────────────────────────────────────────────
# From https://developer.spotify.com/dashboard
CLIENT_ID     = "7b0eb6ab49f646f6ad2f2b9321aef8d6"
CLIENT_SECRET = "2ce499b9ca4a4e81af8194f52de64df1"

# ── Output folder structure ───────────────────────────────────────────────────
# Downloads go into: <artist>/<album>/<track-number> - <title>.mp3
# Files are saved relative to wherever you run this script from.
OUTPUT_FORMAT = "{artist}/{album}/{track-number} - {title}.{output-ext}"

# ── Patches ───────────────────────────────────────────────────────────────────
# Spotify's Development Mode API omits certain fields and enforces a lower
# page size limit. These patches are applied before running spotdl and
# reverted automatically when done, so the library files stay clean.

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
            print(f"  = Already applied: {patch['reason']}")
        else:
            print(f"  ! Could not patch ({path}): {patch['reason']}")
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
    if len(sys.argv) < 2:
        print("Usage: python3 download_artist.py \"https://open.spotify.com/artist/ARTIST_ID\"")
        print("\nExample:")
        print("  python3 download_artist.py \"https://open.spotify.com/artist/2uYWxilOVlUdk4oV9DvwqK\"")
        sys.exit(1)

    artist_url = sys.argv[1]
    applied = apply_patches()

    try:
        cmd = [
            PYTHON, "-m", "spotdl", artist_url,
            "--client-id",     CLIENT_ID,
            "--client-secret", CLIENT_SECRET,
            "--output",        OUTPUT_FORMAT,
        ]
        print(f"Running spotdl for: {artist_url}\n", flush=True)
        subprocess.run(cmd, check=False)
    finally:
        revert_patches(applied)


if __name__ == "__main__":
    main()

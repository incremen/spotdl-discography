# spotdl-discography

Download a full Spotify artist discography as MP3s, sorted into `Artist/Album/Track` folders. You can use this to gain access to songs spotify geoblocked from you.

---

## Requirements

Before using this script, make sure you have the following:

**1. Python 3.8+**
Check with `python3 --version`. If you don't have it, download it from [python.org](https://www.python.org/downloads/).

**2. Spotify Premium (Required)**
As of March 9, 2026, Spotify requires an active Premium subscription to use the Developer API (even in Development Mode). The audio itself is downloaded from YouTube Music, but you need Premium to create the API credentials to fetch the metadata.

**3. A Desktop VPN (If you want to get around a geoblock)**
If you are in a country where parts of an artist's catalog are geo-restricted on Spotify, the API will not return those albums. Any free VPN will do. I recommend [Windscribe](https://windscribe.com/download) because of how easy it is to set

---

## Setup

### 1. Clone and initialize

```bash
git clone <repo-url>
cd spotdl-discography
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Get Spotify API credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Click **Create app** (Name and description do not matter. No Redirect URI is needed as this uses the Client Credentials flow).
3. Copy the **Client ID** and **Client Secret**.
4. Create a `.env` file in the project root:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

---

## Usage

### 1. Get the artist URL
1. Open Spotify and go to the artist's page.
2. Right-click the artist name (or click the `...` menu) → **Share** → **Copy link to artist**.
3. It will look like: `https://open.spotify.com/artist/2uYWxilOVlUdk4oV9DvwqK` (You can paste this full URL directly; you do not need to extract the ID).

### 2. Run the script
Pass the URL to the script:

```bash 
python3 download_artist.py "https://open.spotify.com/artist/2uYWxilOVlUdk4oV9DvwqK"
```

Downloads land in the current directory, organized as:
```text
Mitski/
  Puberty 2/
    01 - Happy.mp3
    02 - Once More to See You.mp3
    ...
  Be the Cowboy/
    01 - Geyser.mp3
    ...
```

*Note: Re-running the script automatically skips tracks that are already downloaded, making it safe to resume if interrupted.*

---

## Why this wrapper script exists

Running `spotdl` directly against a Spotify artist URL breaks in a few ways when using a standard Development Mode app. The script patches the library before running and reverts it after, keeping the library files untouched between runs.

**Problem 1 — page size cap**
Development Mode limits the `artist_albums` endpoint to 10 results per page, but `spotdl` requests 20. Spotify returns `400 Invalid limit`.

**Problem 2 — missing metadata fields**
Development Mode strips several fields from API responses (`label`, `genres`, `popularity`) that `spotdl` tries to access directly, causing `KeyError` crashes.

| Missing field | Crashes in | Error |
|---|---|---|
| `label` | `album.py`, `song.py` | `KeyError: 'label'` |
| `genres` | `artist.py`, `song.py` | `KeyError: 'genres'` |
| `popularity` | `song.py` | `KeyError: 'popularity'` |

All of these are patched with `.get()` fallbacks. None of them affect the actual download.

The patches are reverted when the script finishes—even if it crashes or you hit Ctrl+C. If the process is hard-killed (e.g., power loss), the patches will remain in the library files. Re-running the script detects the existing patches, uses them, and reverts them cleanly at the end of that run.

---

## Troubleshooting

**Got fewer songs than expected**
The VPN probably isn't routing your machine's traffic. Reconnect and retry. You can confirm the VPN is working by checking if the Spotify search API returns results in the VPN country's language.

**`400 Invalid limit` or `KeyError` errors**
The patches didn't find their target strings. `spotdl` may have been updated. Check `spotdl --version` against `requirements.txt`. If it changed, the find/replace strings in `download_artist.py` may need updating to match the new library code.

**`Retry will occur after: 86400s`**
Spotify rate-limited your IP. Switch to a different VPN server or network and retry.

---

*Built with [Claude Code](https://claude.ai/claude-code)*
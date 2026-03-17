# spotdl-discography

Download a full Spotify artist discography as MP3s, sorted into `Artist/Album/Track` folders. Built with [Claude Code](https://claude.ai/claude-code) to solve a bunch of annoying problems that come up when you try to do this the obvious way.

It uses [spotdl](https://github.com/spotDL/spotify-downloader) under the hood — which pulls metadata from Spotify and audio from YouTube Music — so no Spotify Premium required.

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd spotdl-discography
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Get Spotify API credentials

You need a Spotify developer app:

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app** — name and description don't matter. No Redirect URI needed (this script uses the Client Credentials flow, which is server-to-server and doesn't involve user login).
3. Copy the **Client ID** and **Client Secret**
4. Copy `.env.example` to `.env` and fill it in:

```bash
cp .env.example .env
```

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

> **Spotify Premium required:** As of March 9, 2026, Spotify requires an active Premium subscription to use the Developer API (even in Development Mode). The audio itself is downloaded from YouTube Music so Premium isn't needed for the download — but you do need it to create the API credentials in the first place.

### 3. Connect to a VPN (if needed)

If you're in a country where parts of an artist's catalog are geo-restricted on Spotify, the API simply won't return those albums — you'll get a partial download without any error. A VPN set to the US or UK fixes this.

A couple of things that *don't* work:
- A VPN on your phone while using it as a hotspot — the Mac still goes through your ISP
- Setting a `market` parameter in the API call — Spotify ignores it and uses the request IP anyway

The VPN has to run directly on the machine running the script.

### 4. Run it

```bash
.venv/bin/python3 download_artist.py "https://open.spotify.com/artist/ARTIST_ID"
```

**How to get the artist URL:** open Spotify → right-click the artist name → Share → Copy link to artist

**Example:**
```bash
.venv/bin/python3 download_artist.py "https://open.spotify.com/artist/2uYWxilOVlUdk4oV9DvwqK"
```

Downloads land in the current directory, organized as:
```
Mitski/
  Puberty 2/
    01 - Happy.mp3
    02 - Once More to See You.mp3
    ...
  Be the Cowboy/
    01 - Geyser.mp3
    ...
```

Re-running skips already-downloaded tracks automatically, so it's safe to run again if something was interrupted.

---

## Why this wrapper script exists

Running `spotdl` directly against a Spotify artist URL breaks in a few ways when using a standard Development Mode app. The script patches the library before running and reverts it after, so the library files stay untouched between runs.

**Problem 1 — page size cap**
Development Mode limits the `artist_albums` endpoint to 10 results per page, but spotdl requests 20. Spotify returns `400 Invalid limit`.

**Problem 2 — missing metadata fields**
Development Mode strips several fields from API responses (`label`, `genres`, `popularity`) that spotdl tries to access directly, causing `KeyError` crashes.

| Missing field | Crashes in | Error |
|---|---|---|
| `label` | `album.py`, `song.py` | `KeyError: 'label'` |
| `genres` | `artist.py`, `song.py` | `KeyError: 'genres'` |
| `popularity` | `song.py` | `KeyError: 'popularity'` |

All of these are patched with `.get()` fallbacks. None of them affect the actual download.

---

## Troubleshooting

**Got fewer songs than expected**
The VPN probably isn't routing the Mac's traffic. Reconnect and retry. You can confirm it's working by checking whether the Spotify search API returns results in your language or the VPN country's language.

**`400 Invalid limit` or `KeyError` errors**
The patches didn't find their target strings — spotdl may have been updated. Check `spotdl --version` and compare against what's in `requirements.txt`. If it changed, the find/replace strings in `download_artist.py` may need updating to match the new library code.

**`Retry will occur after: 86400s`**
Spotify rate-limited your IP. Switch VPN server or network and retry.

---

*Built with [Claude Code](https://claude.ai/claude-code)*

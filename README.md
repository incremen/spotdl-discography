# download_songs

Downloads a Spotify artist's full discography as MP3s, organized into folders by artist and album.

---

## How to use

### 1. Connect to a VPN

**This is required.** Most of Mitski's catalog (and many other artists) is geo-restricted and not available via the Spotify API from Israel. You need a VPN set to a Western country (US, Canada, UK, etc.) running directly on your Mac — not just on your phone.

- Windscribe, ProtonVPN, NordVPN, etc. all work.
- Confirm it's working by checking that `https://open.spotify.com` shows English content.

### 2. Run the script

```bash
cd /Users/itamar/vscode_projects/download_songs
python3 download_artist.py "SPOTIFY_ARTIST_URL"
```

**Example — Mitski:**
```bash
python3 download_artist.py "https://open.spotify.com/artist/2uYWxilOVlUdk4oV9DvwqK"
```

To get an artist URL: open Spotify → right-click the artist name → Share → Copy link to artist.

### 3. Output structure

Files are saved in the current directory, organized as:
```
Artist Name/
  Album Name/
    01 - Track Title.mp3
    02 - Track Title.mp3
    ...
```

Re-running the script on the same artist skips already-downloaded tracks automatically.

---

## Why this script exists (the problems we ran into)

### Problem 1: Spotify API geo-restriction
The Spotify Web API returns different catalog results based on the IP address of the request. From an Israeli IP, most major artist catalogs are not returned — only locally licensed content. **Fix: use a VPN on the Mac itself** before running.

Note: a VPN on your phone does not help — the Mac's traffic goes through your Israeli ISP regardless when using a phone hotspot.

### Problem 2: Spotify Development Mode API restrictions
Spotify apps created in the developer dashboard start in "Development Mode", which has two relevant restrictions that break spotdl out of the box:

| Field missing | Affected file | Error without patch |
|---|---|---|
| `limit` capped at 10 (not 20) | `spotipy/client.py` | `400 Invalid limit` |
| `label` omitted from album metadata | `spotdl/types/album.py`, `spotdl/types/song.py` | `KeyError: 'label'` |
| `genres` omitted from artist/album metadata | `spotdl/types/artist.py`, `spotdl/types/song.py` | `KeyError: 'genres'` |
| `popularity` omitted from track metadata | `spotdl/types/song.py` | `KeyError: 'popularity'` |

`download_artist.py` patches these fields at runtime before running spotdl, and reverts the library files automatically when done.

### Problem 3: Wrong artist ID in original URL
The artist URL originally provided (`2uYWxilOVlUcdLHIvgAXLl`) was slightly wrong. The correct Mitski ID is `2uYWxilOVlUdk4oV9DvwqK`. Always copy artist URLs directly from Spotify.

---

## Credentials

The Spotify app credentials are stored in `download_artist.py`:

```python
CLIENT_ID     = "7b0eb6ab49f646f6ad2f2b9321aef8d6"
CLIENT_SECRET = "2ce499b9ca4a4e81af8194f52de64df1"
```

These were created at https://developer.spotify.com/dashboard. If they expire or stop working, create a new app there and update these two values.

---

## Requirements

```bash
pip3 install spotdl
```

spotdl downloads audio from YouTube Music using the Spotify metadata for matching. No Spotify Premium required.

---

## Troubleshooting

**"Found 23 songs" but you expected more**
VPN is not active or not routing Mac traffic. Disconnect and reconnect the VPN, then retry.

**`400 Invalid limit` or `KeyError`**
The patches didn't apply. Check that spotdl is still version 4.x (`spotdl --version`). If spotdl was upgraded and the library internals changed, the patch strings in `download_artist.py` may need updating.

**Rate limit / `Retry will occur after: 86400s`**
Your IP was rate-limited by Spotify. Switch to a different network or VPN server and retry.

"""
Cue - fetch metadata and a timestamped transcript for one episode.

Normally started by transcribe.py in a background process. Usage:
    python fetch_transcript.py <url> --data <dir> [--model small] [--force] [--notion-page <id>]

Supported sources:
    - YouTube (captions; if there are none, audio + local Whisper)
    - Spotify (finds the public mp3 via Apple Podcasts / RSS, then local Whisper)
    - Apple Podcasts (mp3 via the iTunes lookup, then Whisper)
    - Direct link to an audio file (.mp3, .m4a, ...)

Output in <data>/episodes/<source>-<id>/:
    meta.json        episode metadata
    transcript.txt   transcript in ~45 s blocks, each line starting with [mm:ss]
Prints a final JSON on stdout with the paths and the metadata.
"""

import argparse
import difflib
import hashlib
import ipaddress
import socket
import html
import json
import os
import re
import shutil
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
# Whisper's math library (Intel runtime) aborts on console close / Ctrl-C events on Windows:
# without this, closing the Claude app mid-transcription kills the background worker.
os.environ.setdefault("FOR_DISABLE_CONSOLE_CTRL_HANDLER", "1")

import requests

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

DATA_DIR = Path(os.environ.get("CUE_DATA") or Path.home() / ".cue")
EPISODES_DIR = DATA_DIR / "episodes"
MODELS_DIR = DATA_DIR / "models"


def configure(data_dir):
    """Point every output folder at the user's data directory."""
    global DATA_DIR, EPISODES_DIR, MODELS_DIR
    DATA_DIR = Path(data_dir).expanduser()
    EPISODES_DIR = DATA_DIR / "episodes"
    MODELS_DIR = DATA_DIR / "models"


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)
PREVIEW_UA = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})

CHUNK_SECONDS = 30  # a block never starts more than this before the words it holds
CHUNK_MAX_CHARS = 1200
AUDIO_EXTS = (".mp3", ".m4a", ".aac", ".wav", ".ogg", ".opus", ".flac", ".webm")
MAX_AUDIO_BYTES = 1_500_000_000  # ~1.5 GB: far more than any podcast episode
NOISE = ("[Music]", "[Musica]", "[Applause]", "[Musique]", "[Música]")


def log(msg):
    print(f"[cue] {msg}", file=sys.stderr, flush=True)
    if LIVE:
        LIVE.set(progress_text(msg.strip()))


# --------------------------------------------------------------------------- progress on Notion


def progress_text(line):
    """Turn a log line into a short text for the Progress column in Notion."""
    m = re.search(r"([\d.]+)% - about (\d+) min left", line)
    if m:
        pct, eta = float(m.group(1)), int(m.group(2))
        bar = "▓" * int(pct // 10) + "░" * (10 - int(pct // 10))
        return f"🎙️ Transcribing {bar} {pct:.0f}% · ~{max(eta, 1)} min left"
    m = re.search(r"download (\d+)%", line)
    if m:
        return f"⬇️ Downloading audio {m.group(1)}%"
    if "Downloading audio" in line or "Audio downloaded" in line:
        return "⬇️ Downloading audio…"
    if "model" in line.lower():
        return "🧠 Loading Whisper…"
    if line.startswith("Transcribing"):
        return "🎙️ Transcription started…"
    if line.startswith("Saved transcript") or line.startswith("Captions found"):
        return "✍️ Writing the summary…"
    return "🔎 Finding the episode…"


def load_env():
    """Read <data>/.env (KEY=value lines). Optional: only used for live progress."""
    env = {}
    path = DATA_DIR / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            raw = raw.strip()
            if raw and not raw.startswith("#") and "=" in raw:
                key, value = raw.split("=", 1)
                env[key.strip()] = value.strip().strip("\"'")
    return env


class NotionLive:
    """Optional: update the episode's Progress column through the Notion API, from a background thread.
    Active only if the user created a Notion integration token (NOTION_TOKEN in <data>/.env)."""

    INTERVAL = 8  # minimum seconds between two updates

    def __init__(self, page_id):
        self.token = os.environ.get("NOTION_TOKEN") or load_env().get("NOTION_TOKEN", "")
        m = re.search(r"([0-9a-f]{32})", (page_id or "").replace("-", ""))
        self.page_id = m.group(1) if m else ""
        self.enabled = bool(self.token and self.page_id)
        self.pending = self.sent = None
        self.failures = 0
        if self.enabled:
            import threading

            self.lock = threading.Lock()
            threading.Thread(target=self._loop, daemon=True).start()

    def set(self, text):
        if self.enabled:
            with self.lock:
                self.pending = text

    def _push(self, text):
        try:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{self.page_id}",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                json={"properties": {"Progress": {"rich_text": [{"type": "text", "text": {"content": text}}]}}},
                timeout=15,
            )
            if r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            self.sent, self.failures = text, 0
        except Exception as e:
            self.failures += 1
            print(f"[notion-live] update failed: {e}", file=sys.stderr, flush=True)
            if self.failures >= 3:
                print("[notion-live] disabled after 3 errors (token or page permissions?)", file=sys.stderr, flush=True)
                self.enabled = False

    def _loop(self):
        while self.enabled:
            with self.lock:
                text = self.pending
            if text and text != self.sent:
                self._push(text)
            time.sleep(self.INTERVAL)

    def finish(self, text):
        """Last update, synchronous (the process is about to exit)."""
        if self.enabled:
            with self.lock:
                self.pending = text
            self._push(text)


LIVE = None


class FetchError(Exception):
    pass


TRAIL = []  # errors met along the way (e.g. captions that failed), used to explain the final error


# Known failures, checked in order: (code, patterns, plain message, worth retrying with a newer yt-dlp)
KNOWN_ERRORS = [
    ("youtube_bot_check", ("not a bot",),
     "YouTube asked to confirm that you're not a bot, so the video couldn't be read. Try again in a few minutes.", True),
    ("age_restricted", ("confirm your age", "age-restricted", "age restricted", "inappropriate for some users"),
     "The video is age-restricted: YouTube shows it only to signed-in users, so cue can't read it.", False),
    ("private", ("private video", "video is private"),
     "The video is private.", False),
    ("members_only", ("members-only", "join this channel", "channel's members", "members only"),
     "The video is for channel members only.", False),
    ("live", ("live event", "premieres in", "is live", "this live stream"),
     "It's a live stream or a premiere that hasn't finished: try again when the recording is available.", False),
    ("unavailable", ("video unavailable", "video is unavailable", "has been removed", "not available in your country",
                     "not made this video available", "video is no longer available"),
     "The video is not available (removed, or blocked in your country).", False),
    ("rate_limited", ("http error 429", "too many requests", "requestblocked", "ipblocked"),
     "YouTube is limiting requests from your connection right now. Try again in a few minutes.", False),
    ("spotify_exclusive", ("no public audio found",),
     "No public audio for this episode (it may be a Spotify exclusive). Try the YouTube link of the same episode.", False),
    ("unsupported", ("unsupported source", "link not recognised", "without an episode"),
     "This link isn't supported: use a YouTube, Spotify or Apple Podcasts episode link, or a link to an audio file.", False),
    ("offline", ("failed to resolve", "getaddrinfo", "nameresolutionerror", "connectionerror", "max retries exceeded",
                 "timed out", "network is unreachable"),
     "No internet connection, or the site didn't answer. Check the connection and try again.", False),
    ("no_disk_space", ("no space left",),
     "The disk is full: free some space and try again.", False),
    ("whisper_model", ("huggingface", "hf_hub", "snapshot_download"),
     "The speech model couldn't be downloaded (first time only, about 500 MB). Check the connection and try again.", False),
    ("youtube_changed", ("unable to extract", "nsig", "signature", "requested format is not available",
                         "http error 403", "precondition check failed"),
     "YouTube changed something on its side, so the video couldn't be read.", True),
]


def classify_error(error, trail=(), source=""):
    """Turn an exception into a stable code, a plain-language message and whether a newer yt-dlp may fix it."""
    text = " | ".join([f"{type(error).__name__}: {error}", *trail]).lower().replace("’", "'")
    for code, patterns, message, retry in KNOWN_ERRORS:
        if any(p in text for p in patterns):
            return {"code": code, "message": message, "retry_with_update": retry}
    return {
        "code": "unknown",
        "message": "Something went wrong while reading the episode.",
        # yt-dlp breaks when YouTube changes: a newer version is the most common fix
        "retry_with_update": source == "youtube",
    }


# --------------------------------------------------------------------------- utils


def norm(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def similarity(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return max(0.9, difflib.SequenceMatcher(None, a, b).ratio())
    return difflib.SequenceMatcher(None, a, b).ratio()


def fmt_ts(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def clean_segments(segments):
    """(start, text) segments with normalised text, without empty lines and [Music]-style noise."""
    out = []
    for start, text in segments:
        text = re.sub(r"\s+", " ", html.unescape(text or "")).strip()
        if text and text not in NOISE:
            out.append((round(float(start), 2), text))
    return out


def chunk_segments(segments):
    """Merge segments into blocks of ~30 seconds. A block is closed *before* a segment that would make it too long,
    so the [mm:ss] of a block is never more than CHUNK_SECONDS before any of its words."""
    chunks, cur_start, cur_text = [], None, []
    for start, text in clean_segments(segments):
        if cur_text and (start - cur_start >= CHUNK_SECONDS or len(" ".join(cur_text)) + len(text) > CHUNK_MAX_CHARS):
            chunks.append((cur_start, " ".join(cur_text)))
            cur_start, cur_text = None, []
        if cur_start is None:
            cur_start = start
        cur_text.append(text)
    if cur_text:
        chunks.append((cur_start, " ".join(cur_text)))
    return chunks


def locate_quotes(segments, quotes, threshold=0.6):
    """Find each quote in the original segments: the exact start time and the words actually said.
    Windows of consecutive segments about as long as the quote are compared with a fuzzy ratio."""
    segs = [(s, t, norm(t)) for s, t in clean_segments(segments)]
    out = []
    for q in quotes:
        nq = norm(q)
        best = (0.0, None, None)
        if nq:
            for i in range(len(segs)):
                joined_raw, joined_norm = [], ""
                for j in range(i, min(i + 12, len(segs))):
                    joined_raw.append(segs[j][1])
                    joined_norm = (joined_norm + " " + segs[j][2]).strip()
                    if len(joined_norm) >= len(nq) * 0.8:
                        sm = difflib.SequenceMatcher(None, nq, joined_norm)
                        if sm.quick_ratio() > best[0]:
                            score = sm.ratio()
                            if score > best[0]:
                                best = (score, segs[i][0], " ".join(joined_raw))
                    if len(joined_norm) > len(nq) * 1.6:
                        break
        score, start, said = best
        found = score >= threshold
        out.append({"quote": q, "found": found, "score": round(score, 2),
                    "start": start if found else None, "time": fmt_ts(start) if found else None,
                    "said": said if found else None})
    return out


def read_segments(workdir):
    """Original segments of an episode: segments.json, or the [mm:ss] blocks of an older transcript.txt."""
    seg_path, tx_path = workdir / "segments.json", workdir / "transcript.txt"
    if seg_path.exists():
        return [tuple(s) for s in json.loads(seg_path.read_text(encoding="utf-8"))]
    segs = []
    if tx_path.exists():
        for line in tx_path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\[(?:(\d+):)?(\d+):(\d+)\] (.*)$", line)
            if m:
                h, mi, s = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
                segs.append((h * 3600 + mi * 60 + s, m.group(4)))
    return segs


def write_atomic(path, text):
    """Write a file so that a crash never leaves it half written."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def safe_url(url):
    """For logs: host and path only, never the query string (private feeds put access tokens there)."""
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path}"[:120]


def is_public_host(host):
    """False for localhost, private, link-local and other non-public addresses (and names that resolve to them)."""
    if not host:
        return False
    try:
        addrs = [ipaddress.ip_address(host.strip("[]"))]
    except ValueError:
        try:
            addrs = [ipaddress.ip_address(ai[4][0].split("%")[0]) for ai in socket.getaddrinfo(host, None)]
        except OSError:
            return True  # can't resolve: requests will fail with a clear network error anyway
    return all(a.is_global for a in addrs)


def check_url(url):
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise FetchError(f"Unsupported source: only web links can be downloaded ({p.scheme or 'no scheme'})")
    if not is_public_host(p.hostname):
        raise FetchError("Unsupported source: this link points to a local or private network address")


def download(url, dest, max_bytes=MAX_AUDIO_BYTES):
    """Download an audio file: public web addresses only (every redirect is checked), with a size cap and a disk check."""
    log(f"Downloading audio: {safe_url(url)}")
    for _ in range(6):
        check_url(url)
        r = HTTP.get(url, stream=True, timeout=60, allow_redirects=False)
        if r.is_redirect and r.headers.get("location"):
            url = urljoin(url, r.headers["location"])
            r.close()
            continue
        break
    else:
        raise FetchError("Too many redirects while downloading the audio")
    with r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        if total > max_bytes:
            raise FetchError(f"The audio file is too big ({total / 1e9:.1f} GB)")
        free = shutil.disk_usage(dest.parent).free
        if free < max(total, 200_000_000) + 500_000_000:
            raise FetchError(f"No space left on the disk for the audio ({free / 1e9:.1f} GB free)")
        done, last = 0, time.time()
        with open(dest, "wb") as f:
            for block in r.iter_content(1 << 16):
                f.write(block)
                done += len(block)
                if done > max_bytes:
                    raise FetchError("The audio file is too big")
                if total and time.time() - last > 5:
                    log(f"  download {done * 100 // total}%")
                    last = time.time()
    log(f"Audio downloaded ({done / 1e6:.1f} MB)")
    return dest


# --------------------------------------------------------------------------- whisper


def transcribe_audio(path, model_name):
    from faster_whisper import WhisperModel

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    opts = dict(device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4, download_root=str(MODELS_DIR))
    try:
        # If the model is already on disk, don't contact Hugging Face (the connection sometimes hangs)
        model = WhisperModel(model_name, local_files_only=True, **opts)
        log(f"Whisper model '{model_name}' loaded from disk")
    except Exception:
        log(f"Downloading the Whisper model '{model_name}' (first time only, about 500 MB)...")
        model = WhisperModel(model_name, **opts)
    segments, info = model.transcribe(
        str(path),
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    total = info.duration or 0
    log(f"Transcribing {fmt_ts(total)} of audio (detected language: {info.language})...")
    t0, last, out = time.time(), 0.0, []
    for seg in segments:
        out.append((seg.start, seg.text))
        if total and time.time() - last > 10:
            pct = seg.end / total
            elapsed = time.time() - t0
            eta = elapsed / pct - elapsed if pct > 0 else 0
            log(f"  {pct:5.1%} - about {int(eta // 60)} min left")
            last = time.time()
    log(f"Transcription finished in {int((time.time() - t0) // 60)} min")
    return out, info.language, total


# --------------------------------------------------------------------------- YouTube


def youtube_id(url):
    p = urlparse(url)
    host = p.netloc.lower()
    if "youtu.be" in host:
        return p.path.strip("/").split("/")[0]
    if "youtube" in host:
        if p.path == "/watch":
            return parse_qs(p.query).get("v", [None])[0]
        m = re.match(r"^/(shorts|live|embed|v)/([^/?#]+)", p.path)
        if m:
            return m.group(2)
    return None


def js_runtimes():
    """yt-dlp needs a JavaScript runtime for YouTube: deno is installed with the scripts, node is a fallback."""
    found = {name: {} for name in ("deno", "node") if shutil.which(name)}
    return found or {"deno": {}}


def ydl_opts(extra=None):
    opts = {"quiet": True, "no_warnings": True, "noprogress": True, "skip_download": True}
    opts["js_runtimes"] = js_runtimes()
    opts.update(extra or {})
    return opts


def youtube_captions_api(video_id, lang_hint):
    from youtube_transcript_api import YouTubeTranscriptApi

    tlist = list(YouTubeTranscriptApi().list(video_id))
    if not tlist:
        raise FetchError("no captions")
    generated = [t for t in tlist if t.is_generated]
    manual = [t for t in tlist if not t.is_generated]
    # The spoken language comes from YouTube's metadata (yt-dlp). Auto-dubbed videos have automatic
    # captions in many languages, so the first generated track is only a fallback.
    spoken = (lang_hint or (generated[0].language_code if generated else "")).split("-")[0]
    pick = None
    for t in manual + generated:
        if spoken and t.language_code.split("-")[0] == spoken:
            pick = t
            break
    pick = pick or (manual or generated)[0]
    data = pick.fetch().to_raw_data()
    kind = "automatic captions" if pick.is_generated else "captions"
    return [(d["start"], d["text"]) for d in data], pick.language_code, kind


def youtube_captions_ytdlp(info):
    lang = (info.get("language") or "").split("-")[0]
    subs, auto = info.get("subtitles") or {}, info.get("automatic_captions") or {}
    candidates = []
    if lang:
        candidates += [(subs, lang), (auto, f"{lang}-orig"), (auto, lang)]
    candidates += [(subs, "en"), (auto, "en-orig"), (auto, "en")]
    for source, key in candidates:
        for fmt in source.get(key) or []:
            if fmt.get("ext") == "json3":
                data = HTTP.get(fmt["url"], timeout=30).json()
                segs = []
                for ev in data.get("events", []):
                    text = "".join(s.get("utf8", "") for s in ev.get("segs") or [])
                    if text.strip():
                        segs.append((ev.get("tStartMs", 0) / 1000, text))
                if segs:
                    kind = "automatic captions" if source is auto else "captions"
                    return segs, key.replace("-orig", ""), kind
    raise FetchError("no json3 captions available")


def fetch_youtube(url, workdir, model_name):
    import yt_dlp

    vid = youtube_id(url)
    if not vid:
        raise FetchError("YouTube video ID not recognised")
    canonical = f"https://www.youtube.com/watch?v={vid}"
    log(f"YouTube {vid}: reading metadata...")
    info = {}
    try:
        with yt_dlp.YoutubeDL(ydl_opts()) as ydl:
            info = ydl.extract_info(canonical, download=False) or {}
    except Exception as e:  # metadata is nice to have, not essential
        log(f"  yt-dlp metadata not available: {e}")
        TRAIL.append(str(e)[:300])

    upload = info.get("upload_date") or ""
    meta = {
        "source": "YouTube",
        "id": vid,
        "url": canonical,
        "title": info.get("title") or "",
        "podcast": info.get("channel") or info.get("uploader") or "",
        "published": f"{upload[:4]}-{upload[4:6]}-{upload[6:]}" if len(upload) == 8 else "",
        "duration_sec": info.get("duration") or 0,
        "thumbnail": f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
        "description": (info.get("description") or "")[:4000],
        "chapters": [
            {"start": c.get("start_time", 0), "title": c.get("title", "")}
            for c in (info.get("chapters") or [])
        ],
        "timestamp_link": canonical + "&t={seconds}s",
    }

    segments = lang = method = None
    for name, fn in (
        ("youtube-transcript-api", lambda: youtube_captions_api(vid, info.get("language"))),
        ("yt-dlp", lambda: youtube_captions_ytdlp(info)),
    ):
        try:
            segments, lang, method = fn()
            log(f"Captions found via {name} ({lang}, {len(segments)} segments)")
            break
        except Exception as e:
            log(f"  {name}: {type(e).__name__}: {str(e)[:200]}")
            TRAIL.append(f"{type(e).__name__}: {str(e)[:300]}")

    if not segments:
        log("No captions: downloading the audio to transcribe it with Whisper...")
        opts = ydl_opts({
            "skip_download": False,
            "format": "bestaudio[ext=m4a]/bestaudio",
            "outtmpl": str(workdir / "audio.%(ext)s"),
        })
        with yt_dlp.YoutubeDL(opts) as ydl:
            info2 = ydl.extract_info(canonical, download=True)
            audio = Path(ydl.prepare_filename(info2))
        segments, lang, dur = transcribe_audio(audio, model_name)
        method = f"Whisper {model_name} (local)"
        meta["duration_sec"] = meta["duration_sec"] or int(dur)
        audio.unlink(missing_ok=True)

    meta["language"] = lang
    meta["transcript_method"] = method
    return meta, segments


def pick_suggestions(entries, min_min=7, max_min=30, min_views=1000):
    """From a flat YouTube search, keep finished videos of a comfortable length (no lives, no Shorts), in YouTube's order."""
    out = []
    for e in entries or []:
        dur = e.get("duration") or 0
        if not e.get("id") or not (min_min * 60 <= dur <= max_min * 60):
            continue
        if e.get("live_status") in ("is_live", "is_upcoming", "post_live") or "/shorts/" in (e.get("url") or ""):
            continue
        if (e.get("view_count") or 0) < min_views:
            continue
        out.append({
            "title": e.get("title") or "",
            "channel": e.get("channel") or e.get("uploader") or "",
            "url": f"https://www.youtube.com/watch?v={e['id']}",
            "duration_min": round(dur / 60),
        })
    return out


def has_captions(video_id):
    """True / False, or None when YouTube doesn't answer (the video may still work)."""
    from youtube_transcript_api import YouTubeTranscriptApi

    try:
        return bool(list(YouTubeTranscriptApi().list(video_id)))
    except Exception as e:
        return False if "disabled" in str(e).lower() or "no transcript" in str(e).lower() else None


def suggest_videos(query, n=3):
    """A few short YouTube videos with captions about the user's question: ready in about 2 minutes each."""
    import yt_dlp

    with yt_dlp.YoutubeDL(ydl_opts({"extract_flat": True})) as ydl:
        res = ydl.extract_info(f"ytsearch20:{query}", download=False) or {}
    confirmed, unknown = [], []
    for v in pick_suggestions(res.get("entries")):
        caps = has_captions(v["url"].rsplit("=", 1)[-1])
        if caps:
            confirmed.append(v)
        elif caps is None:
            unknown.append(v)
        if len(confirmed) >= n:
            break
    return (confirmed + unknown)[:n]


# --------------------------------------------------------------------------- Spotify / Apple / RSS


def meta_tag(page, prop):
    m = re.search(
        rf'<meta[^>]+(?:property|name)="{re.escape(prop)}"[^>]+content="([^"]*)"', page
    ) or re.search(rf'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="{re.escape(prop)}"', page)
    return html.unescape(m.group(1)) if m else ""


def spotify_episode_info(url):
    m = re.search(r"open\.spotify\.com/(?:intl-[a-z]+/)?episode/([A-Za-z0-9]+)", url)
    if not m:
        raise FetchError("Spotify link not recognised: it must point to an *episode* (open.spotify.com/episode/...)")
    eid = m.group(1)
    canonical = f"https://open.spotify.com/episode/{eid}"
    # Browsers get an empty web player; link-preview crawlers get the meta tags
    page = HTTP.get(canonical, headers={"User-Agent": PREVIEW_UA}, timeout=30).text
    title = meta_tag(page, "og:title")
    descs = [meta_tag(page, "description"), meta_tag(page, "og:description")]
    desc = max(descs, key=len)
    show = ""
    for pat in (
        r"Listen to this episode from (.+?) on Spotify",
        r"Ascolta questo episodio (?:di|da) (.+?) su Spotify",
        r"^(.+?) · (?:Episode|Episodio|Episodio de|Épisode|Folge)$",  # og:description: "Show name · Episode"
    ):
        for d in descs:
            mm = re.search(pat, d)
            if mm:
                show = mm.group(1).strip()
                break
        if show:
            break
    if not show:
        # <title> is usually "Episode title | Show on Spotify" or "Title - Show | Spotify"
        t = re.search(r"<title>(.*?)</title>", page, re.S)
        if t:
            raw = html.unescape(t.group(1))
            mm = re.search(r"\|\s*(.+?)\s+(?:on|su)\s+Spotify", raw) or re.search(r" - (.+?) \| Spotify", raw)
            if mm:
                show = mm.group(1).strip()
    if not title:
        try:
            title = HTTP.get("https://open.spotify.com/oembed", params={"url": canonical}, timeout=20).json().get("title", "")
        except Exception:
            pass
    if not title:
        raise FetchError("Could not read the episode title from Spotify")
    date = meta_tag(page, "music:release_date")
    duration = meta_tag(page, "music:duration")
    return {
        "id": eid,
        "url": canonical,
        "title": title,
        "podcast": show,
        "published": date[:10] if date else "",
        "duration_sec": int(duration) if duration.isdigit() else 0,
        "thumbnail": meta_tag(page, "og:image"),
        "description": desc[:4000],
    }


def itunes_find_episode(title, show):
    """Search the Apple Podcasts index: returns (audio_url, extra) or (None, None)."""
    best, best_score = None, 0.0
    for term in filter(None, [f"{show} {title}" if show else None, title]):
        try:
            res = HTTP.get(
                "https://itunes.apple.com/search",
                params={"term": term[:200], "media": "podcast", "entity": "podcastEpisode", "limit": 25},
                timeout=30,
            ).json().get("results", [])
        except Exception as e:
            log(f"  iTunes search failed: {e}")
            continue
        for r in res:
            score = similarity(title, r.get("trackName", ""))
            if show:
                score = score * 0.75 + similarity(show, r.get("collectionName", "")) * 0.25
            if score > best_score and r.get("episodeUrl"):
                best, best_score = r, score
        if best_score >= 0.85:
            break
    if best and best_score >= 0.7:
        log(f"Found on Apple Podcasts: '{best.get('trackName')}' ({best.get('collectionName')}) score={best_score:.2f}")
        return best["episodeUrl"], best
    # Plan B: the show's RSS feed
    if show:
        try:
            shows = HTTP.get(
                "https://itunes.apple.com/search",
                params={"term": show, "media": "podcast", "entity": "podcast", "limit": 10},
                timeout=30,
            ).json().get("results", [])
        except Exception:
            shows = []
        shows.sort(key=lambda s: similarity(show, s.get("collectionName", "")), reverse=True)
        for s in shows[:3]:
            feed = s.get("feedUrl")
            if not feed or similarity(show, s.get("collectionName", "")) < 0.6:
                continue
            item = rss_find_episode(feed, title)
            if item:
                return item["audio"], {"collectionName": s.get("collectionName"), "feedUrl": feed, **item}
    return None, None


def rss_find_episode(feed_url, title):
    log(f"Searching the RSS feed: {feed_url}")
    try:
        root = ET.fromstring(HTTP.get(feed_url, timeout=60).content)
    except Exception as e:
        log(f"  feed not readable: {e}")
        return None
    best, best_score = None, 0.0
    for item in root.iter("item"):
        t = item.findtext("title") or ""
        enc = item.find("enclosure")
        if enc is None or not enc.get("url"):
            continue
        score = similarity(title, t)
        if score > best_score:
            best, best_score = {"title": t, "audio": enc.get("url"), "pubDate": item.findtext("pubDate")}, score
    if best and best_score >= 0.7:
        log(f"  episode found in the feed: '{best['title']}' score={best_score:.2f}")
        return best
    return None


def youtube_search_fallback(title, show):
    """Last resort: look for the same episode on YouTube."""
    import yt_dlp

    query = f"{show} {title}".strip()
    log(f"Looking for the episode on YouTube: {query[:80]}")
    with yt_dlp.YoutubeDL(ydl_opts({"extract_flat": True})) as ydl:
        res = ydl.extract_info(f"ytsearch5:{query}", download=False)
    for e in res.get("entries") or []:
        if similarity(title, e.get("title", "")) >= 0.75:
            log(f"  found on YouTube: {e.get('title')}")
            return f"https://www.youtube.com/watch?v={e['id']}"
    return None


def fetch_spotify(url, workdir, model_name):
    ep = spotify_episode_info(url)
    log(f"Spotify: '{ep['title']}' - {ep['podcast'] or 'unknown show'}")
    audio_url, extra = itunes_find_episode(ep["title"], ep["podcast"])
    meta = {
        "source": "Spotify",
        **ep,
        "chapters": [],
        "timestamp_link": None,
    }
    if not audio_url:
        yt = youtube_search_fallback(ep["title"], ep["podcast"])
        if yt:
            ymeta, segs = fetch_youtube(yt, workdir, model_name)
            meta.update({k: ymeta[k] for k in ("language", "transcript_method", "chapters")})
            meta["duration_sec"] = meta["duration_sec"] or ymeta["duration_sec"]
            meta["also_on_youtube"] = ymeta["url"]
            meta["timestamp_link"] = ymeta["timestamp_link"]
            return meta, segs
        raise FetchError(
            "No public audio found for this episode (it may be a Spotify exclusive). "
            "Try the YouTube link of the same episode."
        )
    if extra:
        meta["podcast"] = meta["podcast"] or extra.get("collectionName", "")
        meta["thumbnail"] = meta["thumbnail"] or extra.get("artworkUrl600", "")
        if not meta["published"] and extra.get("releaseDate"):
            meta["published"] = extra["releaseDate"][:10]
        if not meta["duration_sec"] and extra.get("trackTimeMillis"):
            meta["duration_sec"] = extra["trackTimeMillis"] // 1000
    return finish_audio(meta, audio_url, workdir, model_name)


def fetch_apple(url, workdir, model_name):
    ep_id = parse_qs(urlparse(url).query).get("i", [None])[0]
    show_id = re.search(r"/id(\d+)", url)
    if not ep_id or not show_id:
        raise FetchError("Apple Podcasts link without an episode (it needs the ?i=... parameter)")
    res = HTTP.get(
        "https://itunes.apple.com/lookup",
        params={"id": show_id.group(1), "entity": "podcastEpisode", "limit": 300},
        timeout=30,
    ).json().get("results", [])
    ep = next((r for r in res if str(r.get("trackId")) == ep_id), None)
    if not ep or not ep.get("episodeUrl"):
        # The index only returns the latest ~200 episodes: look for the title in the full RSS feed
        show = next((r for r in res if r.get("wrapperType") == "track" and r.get("kind") == "podcast"), {})
        page = HTTP.get(url, timeout=30).text
        title = re.sub(r"\s*[-|–]\s*Apple Podcasts.*$", "", meta_tag(page, "og:title")).strip()
        item = rss_find_episode(show["feedUrl"], title) if show.get("feedUrl") and title else None
        if not item:
            raise FetchError("Episode not found on Apple Podcasts")
        ep = {
            "trackName": item["title"],
            "collectionName": show.get("collectionName", ""),
            "episodeUrl": item["audio"],
            "artworkUrl600": show.get("artworkUrl600", ""),
            "description": meta_tag(page, "og:description"),
        }
    meta = {
        "source": "Apple Podcasts",
        "id": ep_id,
        "url": url,
        "title": ep.get("trackName", ""),
        "podcast": ep.get("collectionName", ""),
        "published": (ep.get("releaseDate") or "")[:10],
        "duration_sec": (ep.get("trackTimeMillis") or 0) // 1000,
        "thumbnail": ep.get("artworkUrl600") or "",
        "description": (ep.get("description") or "")[:4000],
        "chapters": [],
        "timestamp_link": None,
    }
    return finish_audio(meta, ep["episodeUrl"], workdir, model_name)


def fetch_direct_audio(url, workdir, model_name):
    name = Path(urlparse(url).path).name
    meta = {
        "source": "Other",
        "id": re.sub(r"[^A-Za-z0-9]+", "-", name)[:40] or "audio",
        "url": url,
        "title": Path(name).stem,
        "podcast": "",
        "published": "",
        "duration_sec": 0,
        "thumbnail": "",
        "description": "",
        "chapters": [],
        "timestamp_link": None,
    }
    return finish_audio(meta, url, workdir, model_name)


def finish_audio(meta, audio_url, workdir, model_name):
    ext = Path(urlparse(audio_url).path).suffix.lower()
    audio = download(audio_url, workdir / f"audio{ext if ext in AUDIO_EXTS else '.mp3'}")
    segments, lang, dur = transcribe_audio(audio, model_name)
    meta["duration_sec"] = meta["duration_sec"] or int(dur)
    meta["language"] = lang
    meta["transcript_method"] = f"Whisper {model_name} (local)"
    audio.unlink(missing_ok=True)
    return meta, segments


# --------------------------------------------------------------------------- main


def detect_source(url):
    host = urlparse(url).netloc.lower()
    if "youtube" in host or "youtu.be" in host:
        return "youtube"
    if "spotify.com" in host:
        return "spotify"
    if "podcasts.apple.com" in host:
        return "apple"
    if urlparse(url).path.lower().endswith(AUDIO_EXTS):
        return "audio"
    raise FetchError("Unsupported source: use a YouTube, Spotify or Apple Podcasts link, or a link to an audio file")


def work_id(source, url):
    if source == "youtube":
        return f"youtube-{youtube_id(url)}"
    if source == "spotify":
        m = re.search(r"episode/([A-Za-z0-9]+)", url)
        return f"spotify-{m.group(1) if m else 'x'}"
    if source == "apple":
        return f"apple-{parse_qs(urlparse(url).query).get('i', ['x'])[0]}"
    p = urlparse(url)
    key = f"{p.netloc.lower()}{p.path}"  # two different links that both end in episode.mp3 get different folders
    return "audio-" + re.sub(r"[^A-Za-z0-9]+", "-", Path(p.path).stem)[:30] + "-" + hashlib.sha1(key.encode()).hexdigest()[:8]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--data", default=str(DATA_DIR), help="the user's data folder")
    ap.add_argument("--model", default="small", help="Whisper model: tiny, base, small, medium")
    ap.add_argument("--force", action="store_true", help="redo the transcript even if one exists")
    ap.add_argument("--notion-page", default="", help="ID or URL of the Notion row that shows live progress")
    args = ap.parse_args()
    configure(args.data)

    global LIVE
    LIVE = NotionLive(args.notion_page)
    LIVE.set("🔎 Finding the episode…")

    url = args.url.strip().strip("<>\"'")
    source = ""
    try:
        source = detect_source(url)
        workdir = EPISODES_DIR / work_id(source, url)
        workdir.mkdir(parents=True, exist_ok=True)
        meta_path, tx_path = workdir / "meta.json", workdir / "transcript.txt"

        if tx_path.exists() and meta_path.exists() and not args.force:
            log("Transcript already there, reusing it (use --force to redo it)")
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            fetcher = {"youtube": fetch_youtube, "spotify": fetch_spotify, "apple": fetch_apple, "audio": fetch_direct_audio}[source]
            meta, segments = fetcher(url, workdir, args.model)
            segments = clean_segments(segments)
            chunks = chunk_segments(segments)
            meta["duration_min"] = round((meta.get("duration_sec") or (chunks[-1][0] if chunks else 0)) / 60)
            meta["words"] = sum(len(t.split()) for _, t in chunks)
            meta["input_url"] = url
            write_atomic(workdir / "segments.json", json.dumps(segments, ensure_ascii=False))
            write_atomic(meta_path, json.dumps(meta, ensure_ascii=False, indent=2))
            header = [
                f"# {meta['title']}",
                f"# Show/channel: {meta.get('podcast') or '-'}",
                f"# Source: {meta['source']} - {meta['url']}",
                f"# Language: {meta.get('language')} - Method: {meta.get('transcript_method')}",
                "",
            ]
            lines = [f"[{fmt_ts(s)}] {t}" for s, t in chunks]
            write_atomic(tx_path, "\n".join(header + lines) + "\n")
            log(f"Saved transcript: {len(lines)} blocks, {meta['words']} words")

        print(json.dumps({
            "ok": True,
            "dir": str(workdir),
            "meta": str(meta_path),
            "transcript": str(tx_path),
            "title": meta.get("title"),
            "podcast": meta.get("podcast"),
            "source": meta.get("source"),
            "language": meta.get("language"),
            "duration_min": meta.get("duration_min"),
            "words": meta.get("words"),
            "method": meta.get("transcript_method"),
        }, ensure_ascii=False, indent=2))
        LIVE.finish("✍️ Writing the summary…")
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {str(e)[:500]}", **classify_error(e, TRAIL, source)},
                         ensure_ascii=False, indent=2))
        LIVE.finish("⚠️ Transcription error")
        sys.exit(1)


if __name__ == "__main__":
    main()

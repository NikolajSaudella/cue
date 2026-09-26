"""Unit tests for the transcription scripts: the parts that don't need the network."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_transcript as ft  # noqa: E402
import transcribe as tr  # noqa: E402


@pytest.mark.parametrize("url, vid", [
    ("https://www.youtube.com/watch?v=_FBivfgOvuE", "_FBivfgOvuE"),
    ("https://www.youtube.com/watch?v=_FBivfgOvuE&t=42s&list=PL1", "_FBivfgOvuE"),
    ("https://youtu.be/_FBivfgOvuE?si=abc", "_FBivfgOvuE"),
    ("https://m.youtube.com/watch?v=_FBivfgOvuE", "_FBivfgOvuE"),
    ("https://www.youtube.com/shorts/abcDEF12345", "abcDEF12345"),
    ("https://www.youtube.com/live/abcDEF12345?feature=share", "abcDEF12345"),
    ("https://www.youtube.com/embed/abcDEF12345", "abcDEF12345"),
    ("https://www.youtube.com/@ycombinator", None),
])
def test_youtube_id(url, vid):
    assert ft.youtube_id(url) == vid


@pytest.mark.parametrize("url, source", [
    ("https://www.youtube.com/watch?v=_FBivfgOvuE", "youtube"),
    ("https://youtu.be/_FBivfgOvuE", "youtube"),
    ("https://open.spotify.com/episode/6vquQZjCFblZsGEccyCdsM?si=x", "spotify"),
    ("https://podcasts.apple.com/us/podcast/x/id123?i=456", "apple"),
    ("https://example.com/files/episode-12.MP3", "audio"),
])
def test_detect_source(url, source):
    assert ft.detect_source(url) == source


def test_detect_source_unsupported():
    with pytest.raises(ft.FetchError):
        ft.detect_source("https://example.com/blog/post")


def test_work_id_is_stable_per_episode():
    assert ft.work_id("youtube", "https://youtu.be/_FBivfgOvuE?t=10") == "youtube-_FBivfgOvuE"
    assert ft.work_id("spotify", "https://open.spotify.com/episode/6vquQZjCFblZsGEccyCdsM?si=a") == "spotify-6vquQZjCFblZsGEccyCdsM"
    assert ft.work_id("apple", "https://podcasts.apple.com/us/podcast/x/id123?i=456") == "apple-456"
    assert ft.work_id("audio", "https://example.com/a/My Episode 12.mp3") == "audio-My-Episode-12"


@pytest.mark.parametrize("seconds, text", [(0, "00:00"), (59.9, "00:59"), (61, "01:01"), (3600, "1:00:00"), (3725, "1:02:05")])
def test_fmt_ts(seconds, text):
    assert ft.fmt_ts(seconds) == text


def test_chunk_segments_groups_by_time_and_drops_noise():
    segments = [(0, "Hello"), (10, "[Music]"), (20, "world &amp; friends"), (50, "next"), (60, "block")]
    chunks = ft.chunk_segments(segments)
    assert chunks[0] == (0, "Hello world & friends next")
    assert chunks[1] == (60, "block")


def test_chunk_segments_splits_long_text():
    long = "word " * 400
    chunks = ft.chunk_segments([(0, long), (5, "after")])
    assert len(chunks) == 2 and chunks[1] == (5, "after")


@pytest.mark.parametrize("line, expected", [
    ("   45.0% - about 6 min left", "🎙️ Transcribing ▓▓▓▓░░░░░░ 45% · ~6 min left"),
    ("  download 30%", "⬇️ Downloading audio 30%"),
    ("Whisper model 'small' loaded from disk", "🧠 Loading Whisper…"),
    ("Captions found via yt-dlp (en, 300 segments)", "✍️ Writing the summary…"),
    ("YouTube abc: reading metadata...", "🔎 Finding the episode…"),
])
def test_progress_text(line, expected):
    assert ft.progress_text(line) == expected


def test_similarity():
    assert ft.similarity("How to Get Your First 10 Customers", "how to get your first 10 customers!") > 0.95
    assert ft.similarity("Ep. 49 - Jet HR", "EP.49 Jet HR con Alfredo") >= 0.5
    assert ft.similarity("pricing", "") == 0.0


@pytest.mark.parametrize("message, code, retry", [
    ("ERROR: [youtube] abc: Sign in to confirm you’re not a bot. Use --cookies", "youtube_bot_check", True),
    ("ERROR: [youtube] abc: Sign in to confirm your age. This video may be inappropriate", "age_restricted", False),
    ("ERROR: [youtube] abc: Private video. Sign in if you've been granted access", "private", False),
    ("ERROR: [youtube] abc: Join this channel to get access to members-only content", "members_only", False),
    ("ERROR: [youtube] abc: This live event will begin in 3 hours", "live", False),
    ("ERROR: [youtube] abc: Video unavailable", "unavailable", False),
    ("DownloadError: ERROR: [youtube] aaaaaaaaaaa: This video is unavailable", "unavailable", False),
    ("HTTP Error 429: Too Many Requests", "rate_limited", False),
    ("No public audio found for this episode (it may be a Spotify exclusive).", "spotify_exclusive", False),
    ("Unsupported source: use a YouTube, Spotify or Apple Podcasts link", "unsupported", False),
    ("HTTPSConnectionPool: Max retries exceeded (Failed to resolve 'www.youtube.com')", "offline", False),
    ("ERROR: [youtube] abc: Requested format is not available", "youtube_changed", True),
    ("OSError: [Errno 28] No space left on device", "no_disk_space", False),
])
def test_classify_error(message, code, retry):
    info = ft.classify_error(ft.FetchError(message))
    assert info["code"] == code
    assert info["retry_with_update"] is retry
    assert info["message"]


def test_classify_error_uses_the_trail_and_the_source():
    info = ft.classify_error(RuntimeError("boom"), ["youtube-transcript-api: RequestBlocked: blocked"])
    assert info["code"] == "rate_limited"
    assert ft.classify_error(RuntimeError("boom"), source="youtube")["retry_with_update"] is True
    assert ft.classify_error(RuntimeError("boom"), source="spotify") == {
        "code": "unknown", "message": "Something went wrong while reading the episode.", "retry_with_update": False}


def test_version_tuple():
    assert tr.version_tuple("0.2.0") == (0, 2, 0)
    assert tr.version_tuple("v1.10") == (1, 10, 0)
    assert tr.version_tuple("0.10.0") > tr.version_tuple("0.9.9")
    assert tr.version_tuple(None) == (0, 0, 0)


def test_update_info_uses_the_cache(tmp_path, monkeypatch):
    ft.configure(tmp_path)
    (tmp_path / "update-check.json").write_text('{"checked_at": 9999999999, "latest": "99.0.0"}', encoding="utf-8")
    info = tr.update_info()
    assert info and info["latest"] == "99.0.0"
    (tmp_path / "update-check.json").write_text('{"checked_at": 9999999999, "latest": "0.0.1"}', encoding="utf-8")
    assert tr.update_info() is None


def test_update_info_never_fails_offline(tmp_path, monkeypatch):
    ft.configure(tmp_path)

    def offline(*a, **k):
        raise OSError("no network")

    monkeypatch.setattr(ft.HTTP, "get", offline)
    assert tr.update_info() is None

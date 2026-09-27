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
    a1 = ft.work_id("audio", "https://example.com/a/My Episode 12.mp3")
    assert a1.startswith("audio-My-Episode-12-") and len(a1) == len("audio-My-Episode-12-") + 8
    assert a1 == ft.work_id("audio", "https://EXAMPLE.com/a/My Episode 12.mp3?token=abc")
    # two different links that end with the same file name get different folders
    assert ft.work_id("audio", "https://a.com/episode.mp3") != ft.work_id("audio", "https://b.com/episode.mp3")


@pytest.mark.parametrize("seconds, text", [(0, "00:00"), (59.9, "00:59"), (61, "01:01"), (3600, "1:00:00"), (3725, "1:02:05")])
def test_fmt_ts(seconds, text):
    assert ft.fmt_ts(seconds) == text


def test_chunk_segments_groups_by_time_and_drops_noise():
    segments = [(0, "Hello"), (10, "[Music]"), (20, "world &amp; friends"), (50, "next"), (60, "block")]
    chunks = ft.chunk_segments(segments)
    # the words said at 0:50 open a new block: they are never labelled [00:00]
    assert chunks == [(0, "Hello world & friends"), (50, "next block")]


def test_block_time_is_never_far_before_its_words():
    segments = [(i * 7.3, f"w{i}") for i in range(200)]
    said_at = {text: s for s, text in segments}
    for start, text in ft.chunk_segments(segments):
        assert all(said_at[w] - start < ft.CHUNK_SECONDS for w in text.split())


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


SEGS = [
    (0.0, "welcome back to the show"),
    (3.5, "today we talk about your first customers"),
    (61.2, "he closed more in three days than he had"),
    (64.0, "in three months of sending cold emails"),
    (70.0, "which is crazy when you think about it"),
    (125.0, "so start with your network"),
]


def test_locate_quotes_finds_time_and_words():
    res = ft.locate_quotes(SEGS, ["He closed more in 3 days than he had in 3 months of sending cold emails.",
                                  "Start with your network!",
                                  "This sentence was never said on the show at all."])
    assert res[0]["found"] and res[0]["start"] == 61.2 and res[0]["time"] == "01:01"
    assert "three months of sending cold emails" in res[0]["said"]
    assert res[1]["found"] and res[1]["start"] == 125.0
    assert not res[2]["found"] and res[2]["start"] is None


def test_read_segments_from_old_transcripts(tmp_path):
    (tmp_path / "transcript.txt").write_text("# Title\n\n[00:00] hello there\n[01:05] second block\n[1:02:03] late\n", encoding="utf-8")
    assert ft.read_segments(tmp_path) == [(0, "hello there"), (65, "second block"), (3723, "late")]
    ft.write_atomic(tmp_path / "segments.json", '[[1.5, "from json"]]')
    assert ft.read_segments(tmp_path) == [(1.5, "from json")]
    assert not (tmp_path / "segments.json.tmp").exists()


def test_safe_url_hides_tokens():
    assert ft.safe_url("https://feeds.example.com/private/ep1.mp3?token=SECRET&x=1") == "https://feeds.example.com/private/ep1.mp3"


@pytest.mark.parametrize("host, public", [
    ("127.0.0.1", False), ("10.0.0.5", False), ("192.168.1.10", False), ("169.254.169.254", False),
    ("::1", False), ("[::1]", False), ("8.8.8.8", True), ("", False),
])
def test_is_public_host(host, public):
    assert ft.is_public_host(host) is public


def test_check_url_refuses_local_and_odd_links():
    for url in ("file:///etc/passwd", "http://127.0.0.1:8080/a.mp3", "http://192.168.0.2/ep.mp3"):
        with pytest.raises(ft.FetchError):
            ft.check_url(url)
    ft.check_url("https://8.8.8.8/episode.mp3")


def test_pick_suggestions_keeps_short_finished_popular_videos():
    entries = [
        {"id": "ok1", "title": "Good talk", "channel": "YC", "duration": 14 * 60, "view_count": 50000},
        {"id": "short", "title": "Too short", "duration": 3 * 60, "view_count": 90000},
        {"id": "long", "title": "Too long", "duration": 95 * 60, "view_count": 90000},
        {"id": "live", "title": "Live now", "duration": 20 * 60, "view_count": 90000, "live_status": "is_live"},
        {"id": "sh", "title": "A Short", "duration": 10 * 60, "view_count": 90000, "url": "https://www.youtube.com/shorts/sh"},
        {"id": "few", "title": "Nobody watched", "duration": 10 * 60, "view_count": 12},
        {"id": "ok2", "title": "Another", "uploader": "Someone", "duration": 8 * 60, "view_count": 2000},
        {"title": "No id", "duration": 10 * 60, "view_count": 90000},
    ]
    picks = ft.pick_suggestions(entries)
    assert [p["url"].rsplit("=", 1)[-1] for p in picks] == ["ok1", "ok2"]
    assert picks[0] == {"title": "Good talk", "channel": "YC", "url": "https://www.youtube.com/watch?v=ok1", "duration_min": 14}
    assert picks[1]["channel"] == "Someone"


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


def test_worker_running_sees_a_finished_worker(tmp_path):
    # On macOS and Linux a finished child stays a zombie that os.kill(pid, 0) still reports as alive
    import subprocess
    import time

    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    deadline = time.time() + 10
    while tr.worker_running(proc, proc.pid) and time.time() < deadline:
        time.sleep(0.1)
    assert not tr.worker_running(proc, proc.pid)


def test_audio_is_deleted_when_transcription_fails(tmp_path, monkeypatch):
    def fake_download(url, dest, max_bytes=0):
        dest.write_bytes(b"audio")
        return dest

    def broken_whisper(path, model_name):
        raise RuntimeError("whisper crashed")

    monkeypatch.setattr(ft, "download", fake_download)
    monkeypatch.setattr(ft, "transcribe_audio", broken_whisper)
    with pytest.raises(RuntimeError):
        ft.finish_audio({"duration_sec": 0}, "https://example.com/ep.mp3", tmp_path, "small")
    assert not list(tmp_path.glob("audio.*"))


def test_partial_audio_is_deleted_when_the_download_fails(tmp_path, monkeypatch):
    def too_big(url, dest, max_bytes=0):
        dest.write_bytes(b"half an episode")
        raise ft.FetchError("The audio file is too big")

    monkeypatch.setattr(ft, "download", too_big)
    with pytest.raises(ft.FetchError):
        ft.finish_audio({"duration_sec": 0}, "https://example.com/ep.m4a", tmp_path, "small")
    assert not list(tmp_path.glob("audio.*"))

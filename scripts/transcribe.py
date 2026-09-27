# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#     "yt-dlp[default]>=2026.8.19",
#     "youtube-transcript-api>=1.2.4,<2",
#     "faster-whisper>=1.2.1,<2",
#     "requests>=2.32",
#     "deno>=2.4",
# ]
# ///
"""
cue - one idempotent command to get the transcript of a link.

Run it with uv, which installs Python and the dependencies by itself the first time:
    uv run --script transcribe.py <url> --data <dir> [--notion-page <row>] [--max 150] [--model small] [--force]
    uv run --script transcribe.py --check --data <dir>

- If the transcript already exists: prints the result (JSON) straight away.
- Otherwise starts fetch_transcript.py in a separate process and waits up to --max seconds.
- If the work isn't finished yet, prints {"ok": null, "state": "running", ...}:
  just run the SAME command again to keep waiting (it does not start over).

Exit code: 0 = ready, 2 = still running, 1 = error.
"""

import argparse
import ctypes
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_transcript as ft  # noqa: E402

PYTHON = sys.executable
WORKER = Path(__file__).resolve().parent / "fetch_transcript.py"
PLUGIN_JSON = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
# What users get when they update: the version on the default branch of the repository
LATEST_URL = "https://raw.githubusercontent.com/NikolajSaudella/cue/main/.claude-plugin/plugin.json"
UPDATE_EVERY = 12 * 3600  # check GitHub at most twice a day


def version_tuple(v):
    parts = [int(x) for x in re.findall(r"\d+", str(v or ""))[:3]]
    return tuple(parts + [0] * (3 - len(parts)))


def update_info():
    """{"current", "latest"} when a newer cue exists on GitHub, else None. Never fails, never slow (4 s max, cached)."""
    try:
        current = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        return None
    cache = ft.DATA_DIR / "update-check.json"
    data = read_json(cache) or {}
    if time.time() - data.get("checked_at", 0) > UPDATE_EVERY:
        latest = data.get("latest")
        try:
            r = ft.HTTP.get(LATEST_URL, timeout=4)
            if r.ok:
                latest = r.json().get("version") or latest
        except Exception:
            pass
        data = {"checked_at": time.time(), "latest": latest}
        try:
            cache.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass
    latest = data.get("latest")
    if latest and version_tuple(latest) > version_tuple(current):
        return {"current": current, "latest": latest}
    return None


def pid_alive(pid):
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    k32 = ctypes.windll.kernel32
    handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    k32.GetExitCodeProcess(handle, ctypes.byref(code))
    k32.CloseHandle(handle)
    return code.value == 259  # STILL_ACTIVE


def read_json(path):
    try:
        text = path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else None
    except (OSError, ValueError):
        return None


def last_progress(log_path):
    try:
        lines = [l for l in log_path.read_text(encoding="utf-8", errors="ignore").splitlines() if "[cue]" in l]
        return lines[-1].replace("[cue]", "").strip() if lines else ""
    except OSError:
        return ""


def start_worker(url, workdir, model, force, notion_page):
    out = open(workdir / "result.json", "w", encoding="utf-8")
    err = open(workdir / "log.txt", "w", encoding="utf-8")
    args = [PYTHON, str(WORKER), url, "--data", str(ft.DATA_DIR), "--model", model] + (["--force"] if force else [])
    if notion_page:
        args += ["--notion-page", notion_page]
    if sys.platform == "win32":
        # detached process: it survives even if the shell that started it is closed
        flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_PROCESS_GROUP | NO_WINDOW
        try:
            proc = subprocess.Popen(args, stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                                    creationflags=flags | 0x01000000)  # + BREAKAWAY_FROM_JOB
        except OSError:
            proc = subprocess.Popen(args, stdout=out, stderr=err, stdin=subprocess.DEVNULL, creationflags=flags)
    else:
        proc = subprocess.Popen(args, stdout=out, stderr=err, stdin=subprocess.DEVNULL, start_new_session=True)
    (workdir / "worker.pid").write_text(str(proc.pid))
    return proc.pid


def check():
    """Health check for the setup: dependencies installed, data folder writable, Whisper model present."""
    report = {"ok": True, "python": platform.python_version(), "system": platform.system(), "data": str(ft.DATA_DIR)}
    for mod in ("yt_dlp", "youtube_transcript_api", "faster_whisper", "requests"):
        try:
            __import__(mod)
            report[mod] = "ok"
        except Exception as e:
            report[mod] = f"missing: {e}"
            report["ok"] = False
    report["js_runtime"] = next((n for n in ("deno", "node") if shutil.which(n)), None)
    try:
        ft.EPISODES_DIR.mkdir(parents=True, exist_ok=True)
        probe = ft.DATA_DIR / ".write-test"
        probe.write_text("ok")
        probe.unlink()
        report["data_writable"] = True
    except OSError as e:
        report["data_writable"] = f"no: {e}"
        report["ok"] = False
    report["whisper_model_downloaded"] = any(ft.MODELS_DIR.glob("models--*whisper-small*")) if ft.MODELS_DIR.exists() else False
    try:
        report["cue_version"] = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        pass
    upd = update_info()
    if upd:
        report["cue_update"] = upd
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--data", default=str(ft.DATA_DIR), help="the user's data folder")
    ap.add_argument("--check", action="store_true", help="only check that everything is installed")
    ap.add_argument("--max", type=int, default=150, help="maximum seconds to wait in this call")
    ap.add_argument("--model", default="small")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--notion-page", default="", help="ID/URL of the Notion row: live progress if a Notion token is configured")
    ap.add_argument("--suggest", default="", help="search YouTube for short videos with captions about this question")
    ap.add_argument("--lookup", action="store_true", help="only say what cue already has for this link (folder, Notion page, transcript)")
    ap.add_argument("--locate", action="append", default=[], help="a quote to find in the transcript: exact time and words (repeatable)")
    args = ap.parse_args()
    ft.configure(args.data)

    if args.check:
        check()
    if args.suggest:
        try:
            videos = ft.suggest_videos(args.suggest)
            print(json.dumps({"ok": True, "query": args.suggest, "videos": videos}, ensure_ascii=False, indent=2))
            sys.exit(0)
        except Exception as e:
            print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}", **ft.classify_error(e, source="youtube")},
                             ensure_ascii=False, indent=2))
            sys.exit(1)
    if not args.url:
        ap.error("missing url")
    live = bool(args.notion_page and (os.environ.get("NOTION_TOKEN") or ft.load_env().get("NOTION_TOKEN")))

    url = args.url.strip().strip("<>\"'")
    try:
        source = ft.detect_source(url)
    except ft.FetchError as e:
        print(json.dumps({"ok": False, "error": str(e), **ft.classify_error(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)
    workdir = ft.EPISODES_DIR / ft.work_id(source, url)
    workdir.mkdir(parents=True, exist_ok=True)

    if args.lookup:
        print(json.dumps({"ok": True, "dir": str(workdir), "notion": read_json(workdir / "notion.json"),
                          "transcript_ready": (workdir / "transcript.txt").exists()}, ensure_ascii=False, indent=2))
        sys.exit(0)
    if args.locate:
        segs = ft.read_segments(workdir)
        if not segs:
            print(json.dumps({"ok": False, "error": "No transcript yet for this link", "code": "no_transcript",
                              "message": "There is no transcript for this link yet.", "retry_with_update": False}, ensure_ascii=False, indent=2))
            sys.exit(1)
        meta = read_json(workdir / "meta.json") or {}
        found = ft.locate_quotes(segs, args.locate)
        for f in found:
            if f["found"] and meta.get("timestamp_link"):
                f["link"] = meta["timestamp_link"].replace("{seconds}", str(int(f["start"])))
        print(json.dumps({"ok": True, "method": meta.get("transcript_method"), "quotes": found}, ensure_ascii=False, indent=2))
        sys.exit(0)
    result_path, pid_path, log_path = workdir / "result.json", workdir / "worker.pid", workdir / "log.txt"

    pid = int(pid_path.read_text()) if pid_path.exists() else None
    running = pid is not None and pid_alive(pid)
    result = read_json(result_path)

    if args.force and not running:
        result = None
    if not running and not (result and result.get("ok")):
        pid = start_worker(url, workdir, args.model, args.force or bool(result), args.notion_page)
        running = True

    deadline = time.time() + args.max
    while running and time.time() < deadline:
        time.sleep(5)
        running = pid_alive(pid)

    result = read_json(result_path)
    if running:
        line = last_progress(log_path)
        print(json.dumps({
            "ok": None,
            "state": "running",
            "dir": str(workdir),
            "progress": line,
            "notion_progress": ft.progress_text(line),
            "notion_live": live,
            "hint": ("Still running: Progress in Notion updates by itself, run the same command again."
                     if live else
                     "Still running: write notion_progress into the Progress column, then run the same command again."),
        }, ensure_ascii=False, indent=2))
        sys.exit(2)
    if not result:
        err = ft.FetchError("The process ended without a result")
        result = {"ok": False, "error": str(err), "log": last_progress(log_path), **ft.classify_error(err, [last_progress(log_path)], source)}
    # tell the user about a new version once the episode is done (or failed), not while it's running
    result.setdefault("dir", str(workdir))
    upd = update_info()
    if upd:
        result["cue_update"] = upd
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()

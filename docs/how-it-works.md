# How Cue works

Cue is a [Claude Code plugin](https://code.claude.com/docs/en/plugins): two skills (instructions Claude follows) plus a small Python transcription engine. Claude is the "brain"; Notion is where the notes live; the user's computer does the transcription.

## Pieces

| Path | What it does |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest |
| `.claude-plugin/marketplace.json` | Lets people install the plugin straight from this repository |
| `skills/setup/SKILL.md` | First run: interview, Notion space, tool installation, first episode |
| `skills/episode/SKILL.md` | Turns one episode (or the Notion inbox) into a page, concepts and actions |
| `scripts/transcribe.py` | Entry point. Idempotent: starts the work in the background and can be re-run until it's done |
| `scripts/fetch_transcript.py` | Finds the episode and produces a timestamped transcript |

## Transcription pipeline

1. **YouTube**: captions via `youtube-transcript-api` (fallback: `yt-dlp`). No captions → download the audio with `yt-dlp` and transcribe it with Whisper.
2. **Spotify**:
   - the episode page is read like a link preview, to get the title and show;
   - the same public episode is found in the Apple Podcasts index (iTunes Search API) or in the show's RSS feed;
   - last resort: a YouTube search for the same episode.
3. **Apple Podcasts**: iTunes Lookup API, with the RSS feed as a fallback for older episodes.
4. **Audio file link**: downloaded and transcribed.

Whisper runs locally with `faster-whisper` (model `small`, int8, CPU, voice-activity filter). The output is a text file in ~45-second blocks, each starting with `[mm:ss]`: that's what makes clickable chapter timestamps possible.

Long transcriptions run in a detached process. `transcribe.py` waits up to 150 seconds per call and returns exit code 2 with a progress line if it's still running. Claude re-runs the same command, and the transcription never starts over.

## Dependencies

`transcribe.py` declares its dependencies inline ([PEP 723](https://peps.python.org/pep-0723/)). `uv run --script` creates a cached environment with the right Python and packages the first time, so users never install Python themselves. `deno` (from PyPI) is included as the JavaScript runtime `yt-dlp` needs for YouTube.

## Data on the user's computer

Everything lives in the plugin's data folder (`~/.claude/plugins/data/cue-…/`), which survives plugin updates:

| File | Content |
|---|---|
| `config.json` | Language, uv command, IDs of the user's Notion pages, databases and views |
| `episodes/<source>-<id>/` | `meta.json`, `transcript.txt`, `notion.json` (link to the finished page) |
| `models/` | The Whisper model, downloaded on first use (~500 MB) |
| `.env` *(optional)* | `NOTION_TOKEN=` of a Notion integration, for live progress during long transcriptions |

## Notion structure

Created by the setup skill:

- a **home page**;
- **🧭 My context**;
- three databases:
  - **Episodes**, with the views 📥 Inbox and 📚 Library;
  - **Concepts**, with a two-way relation to Episodes;
  - **Actions**, with a two-way relation to Episodes and the view "To do".

Property names and select options are in English because the skills rely on them. The content is written in the user's language.

Databases are read through views (the connector's "view mode"). That mode has no quota on any Notion plan, unlike SQL queries.

## Running the engine by hand

```
uv run --script scripts/transcribe.py --check --data ~/.cue
uv run --script scripts/transcribe.py "https://www.youtube.com/watch?v=..." --data ~/.cue
```

## Releasing an update

Claude Code decides whether an installed plugin needs updating by comparing the `version` in `.claude-plugin/plugin.json`. **Every change meant for users needs a new version number**, otherwise people who already installed cue never receive it:

1. Bump `version` in `.claude-plugin/plugin.json` (e.g. `0.1.0` → `0.1.1` for fixes, `0.2.0` for new features).
2. Add a section to `CHANGELOG.md`.
3. Commit, tag (`git tag -a v0.1.1 -m "..."`) and push with `--follow-tags`, then publish a GitHub release from the tag.

Users get it automatically if they turned on auto-update for the `cue` marketplace; otherwise from `/plugin` → **Installed** → cue → **Update now** in Claude Code, or `claude plugin update cue@cue` in a terminal. (The exact steps in the desktop app are still to be verified.)

# Changelog

## v0.2.0 — safer, sturdier, and it tells you about updates

- **Safer permissions.** Cue now pre-approves only its own transcription script and its own config files, instead of any `uv` command. Episode transcripts and descriptions are treated as content, never as instructions: if a video contains text addressed to Claude, it's ignored and you're told.
- **YouTube keeps working when YouTube changes.** When a video can't be read because YouTube changed something, cue updates its YouTube downloader and tries again, by itself.
- **Clear errors.** Private, age-restricted, members-only and live videos, Spotify exclusives, no connection, full disk: each one now gets a plain explanation and the next step.
- **Update notice.** At the end of an episode, cue tells you (once) when a new version is available and how to update it.
- **Tests.** The transcription scripts have automatic tests, run on every change.

## v0.1.3

- Cue is now presented for **podcasts and videos**: interviews, talks, lectures and webinars on YouTube work exactly like podcast episodes (they always did, now the product says so).
- New repository address: github.com/NikolajSaudella/cue (the old one redirects).

## v0.1.2

- **Fix:** YouTube videos with automatic dubbing offer captions in many languages; cue sometimes picked a translated track (e.g. Arabic for an English talk). It now always uses the video's original language.

## v0.1.1 — fixes from the first real tests

- **Fix:** on Windows, closing the Claude app during a long transcription stopped Whisper halfway. The background transcription now keeps going.
- **Honest timing:** transcribing audio takes roughly 30-45 minutes per hour on a typical laptop (the docs said 10-15). YouTube episodes with captions are still ready in a couple of minutes.

## v0.1.0 — first public version

The first release of cue: podcasts you actually remember, and what they mean for you.

**What it does**
- Paste a YouTube, Spotify or Apple Podcasts link (or add it to the Notion inbox) and get a Notion page with: in short, key ideas, chapters with clickable timestamps, verbatim quotes, *what it means for me*, connections, actions, resources and questions.
- Concepts that link episodes together, including where guests agree or disagree.
- Concrete actions collected in one to-do list.
- Summaries in the language you choose; quotes stay in the original.

**Setup**
- Guided first run inside Claude: a 4-question interview, your Notion space created for you, transcription tools installed automatically (via uv), and a suggested 2-minute first episode.
- Fewer permission prompts: cue's own commands and files are pre-approved while its skills run.

**Under the hood**
- Transcription on your computer: YouTube captions when available, otherwise local Whisper (faster-whisper).
- Spotify episodes matched to the same public episode on Apple Podcasts or RSS.
- Works on Windows and macOS (macOS still to be tested by a real user).

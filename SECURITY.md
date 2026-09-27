# Security

## What cue does on your computer

- Runs its own transcription scripts (`scripts/`), with Python and their dependencies installed by [uv](https://github.com/astral-sh/uv), only after asking you.
- Downloads public audio and captions for the episodes you give it, plus a speech model the first time (~500 MB). Audio downloads accept only public web addresses (local and private network addresses are refused, redirects included), stop at ~1.5 GB and check the free disk space first.
- Saves audio (deleted after transcription) and transcripts only on your computer. Claude reads the transcript in your own Claude app to write the notes, under your plan's terms; Notion receives only the notes.
- Reads and writes only its own folder (`~/.claude/plugins/data/cue-…/`) and the Notion pages it created for you.

It has no server, no account and no analytics, and it never asks for passwords or API keys. Everything it runs is in this repository.

While it works, cue pre-approves only its own transcription script and its own config files: any other command needs your approval. Transcripts and video descriptions are written by strangers, so cue treats them as content and never follows instructions found in them.

## Reporting a problem

If you find a security issue, please **don't open a public issue**. Report it privately instead:

- on GitHub: **Security** tab → **Report a vulnerability**, or
- by message on [LinkedIn](https://www.linkedin.com/in/nikolajsaudella/).

You'll get an answer within a few days. Fixes go into a new version, listed in the [changelog](CHANGELOG.md).

## Supported versions

Only the latest version gets fixes. To update, see the FAQ in the [README](README.md#faq).

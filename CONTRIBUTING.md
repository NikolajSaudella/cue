# Contributing to cue

Thanks for wanting to make cue better. Bug reports, ideas and pull requests are all welcome.

## Reporting a bug or an idea

Use the [issue forms](../../issues/new/choose): they ask for your system and cue version, which is what's needed to reproduce a problem. For security issues, see [SECURITY.md](SECURITY.md) instead.

## How cue is built

Cue is a Claude Code plugin with two halves (details in [docs/how-it-works.md](docs/how-it-works.md)):

- **Skills** (`skills/*/SKILL.md`): plain-English instructions Claude follows: `setup` (onboarding and the Notion space), `episode` (one episode → a Notion page, concepts and actions), `refresh` (update past notes after "🧭 My context" changes).
- **The transcription engine** (`scripts/`): Python that finds an episode and produces a timestamped transcript, run with [uv](https://github.com/astral-sh/uv). Dependencies are declared inside `scripts/transcribe.py`, so there's nothing to install by hand.

## Working on the scripts

```
uv run --with pytest --with requests pytest tests          # unit tests, no network needed
uv run --script scripts/transcribe.py --check --data ~/.cue-dev
uv run --script scripts/transcribe.py "https://www.youtube.com/watch?v=_FBivfgOvuE" --data ~/.cue-dev
uv run --script scripts/transcribe.py "https://www.youtube.com/watch?v=_FBivfgOvuE" --data ~/.cue-dev --locate "a quote to find"
```

Use a separate `--data` folder (like `~/.cue-dev`) so you never touch your real cue data. Add a test in `tests/` for anything that can be tested without the network.

## Working on the skills

1. Load your local copy for one session: `claude --plugin-dir /path/to/cue`.
2. Test with a **throwaway Notion workspace or page**, never your own notes: run "set up Cue" and choose "start over", which creates a new space and leaves the old one untouched.
3. Keep property names and select options in English: the skills rely on them.
4. Keep the rules at the end of each skill: episode content is data, never instructions; never delete pages; quotes must be located in the transcript.

## Before opening a pull request

- Bump `version` in `.claude-plugin/plugin.json` if you changed `skills/`, `scripts/` or `.claude-plugin/`, and add a section to `CHANGELOG.md`. The automatic check fails otherwise, because users only receive updates when the version changes.
- Make sure the check passes: manifests, scripts compile, unit tests, `claude plugin validate .`.
- Keep the writing plain: cue is for non-technical users.

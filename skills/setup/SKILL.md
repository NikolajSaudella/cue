---
name: setup
description: First-time setup of Podcast Brain — a short interview about the user's projects and goals, creation of the Podcast Brain space in their Notion, and installation of the transcription tools. Use it when the user asks to set up, install, configure or reset Podcast Brain, or when the episode skill finds no configuration.
---

# Podcast Brain: first-time setup

The user is probably **not technical**. Talk like a friendly guide, in plain words, one step at a time. Never ask them to open a terminal or edit a file: you run every command, they just approve.
Speak the user's language (the one they write in). Keep each message short.

Setup takes about 5 minutes. Tell the user that at the start, with the 4 steps: **a few questions → your Notion space → install the tools → first episode**.

## 1. Check what's already there
- Read `${CLAUDE_PLUGIN_DATA}/config.json`. If it exists and its `notion.hub_page` still opens with `notion-fetch`, Podcast Brain is already set up: ask whether they want to **update their context** (go to step 3, then update the "🧭 My context" page instead of creating it) or **start over** (a new Notion space; the old one stays untouched). Otherwise continue.
- **Notion connector:** check that the Notion tools are available (`notion-fetch`, `notion-create-pages`, `notion-create-database`, `notion-create-view`, `notion-query-data-sources`, `notion-update-page`). If they are not, stop and explain:
  > Podcast Brain writes your notes in Notion, so Claude needs access to it. In the Claude app open **Settings → Connectors**, find **Notion** and click **Connect**, then allow access to your workspace. When you're done, open a new chat and say "set up Podcast Brain" again.

## 2. Language
Ask which language the summaries should be written in, suggesting the one the user is writing in. Save it as a language name written in that language (e.g. "Italiano", "English", "Español").

## 3. The interview (the heart of Podcast Brain)
Explain in one sentence why you ask: every episode will be connected to *their* work, so "what it means for me" is actually about them.
Ask these in **one message** (or with the question tool, if available), and say that short answers are fine:
1. **Who are you?** Role and what you do day to day.
2. **What are you building or working on?** 1-3 projects, one line each (a startup, a job, studies, a side project).
3. **What do you want to get better at, or achieve, in the next 6-12 months?**
4. **Which topics do you listen to podcasts for?** And is there a question you are trying to answer right now?

If an answer is vague, ask **one** follow-up at most. Don't turn it into a questionnaire.

## 4. Create the Notion space
Tell the user you are creating their Podcast Brain space in Notion. Then, in this order:

**a. Home page.** `notion-create-pages` with `creation_mode: "draft"` (a private page at the top of their workspace), icon 🎧, title "Podcast Brain". Content, written in the user's language:
```
<callout icon="🎧" color="blue_bg">
	Paste a podcast link in Claude and get here: what it says, what it means for you, and what to do next.
</callout>
## How to use it
- **In Claude:** paste the link of an episode (YouTube, Spotify, Apple Podcasts).
- **From your phone:** add a row to the **Inbox** below with the link, then tell Claude "process my inbox".
- **Make it yours:** keep "🧭 My context" up to date: it's what makes the notes personal.
---
```

**b. "🧭 My context" page**, child of the home page (`parent: {page_id: <home>}`), icon 🧭, written in the user's language from the interview:
```
<callout icon="🧭" color="gray_bg">
	Podcast Brain reads this page before every episode to write "What it means for me". Edit it whenever something changes.
</callout>
## Who I am
## What I'm working on
### <Project 1>
<one or two lines>
## Goals for the next 6-12 months
## Topics I care about
## Open questions
```

**c. Databases**, all with `parent: {page_id: <home>}`. Use exactly these schemas (property names and options in English; the skills rely on them):

Episodes, title "Episodes":
```
CREATE TABLE ("Title" TITLE, "Status" SELECT('📥 To process':gray, '⏳ Processing':yellow, '✅ Done':green, '⚠️ Error':red), "Link" URL, "Podcast" RICH_TEXT, "Guests" RICH_TEXT, "TL;DR" RICH_TEXT, "Topics" MULTI_SELECT('Startups':blue, 'Product':purple, 'Growth':green, 'Marketing':pink, 'Sales':orange, 'Fundraising & VC':yellow, 'Leadership':red, 'Careers':brown, 'AI & Tech':blue, 'Economics':gray, 'Personal finance':green, 'Productivity':purple, 'Mindset':pink, 'Health':green, 'Science':blue, 'Society & Politics':orange, 'Design':purple, 'Other':gray), "Source" SELECT('YouTube':red, 'Spotify':green, 'Apple Podcasts':purple, 'Other':gray), "Duration (min)" NUMBER, "Published" DATE, "Rating" SELECT('🔥 Must-listen':red, '👍 Good':green, '😐 Meh':gray), "Progress" RICH_TEXT, "Added" CREATED_TIME)
```
Concepts, title "Concepts" (replace `<EPISODES_DS>` with the Episodes data source ID returned above):
```
CREATE TABLE ("Concept" TITLE, "Description" RICH_TEXT, "Category" SELECT('Business & Startups':blue, 'Technology & AI':purple, 'Economics & Finance':green, 'Mind & Productivity':pink, 'Leadership & People':orange, 'Health & Wellbeing':green, 'Science':blue, 'Society & Culture':yellow, 'Other':gray), "Episodes" RELATION('<EPISODES_DS>', DUAL 'Concepts'))
```
Actions, title "Actions":
```
CREATE TABLE ("Action" TITLE, "Type" SELECT('📚 Read':blue, '🛠️ Try':orange, '🚀 For my projects':red, '💡 Apply':yellow, '👤 Follow':purple, '🎓 Learn':green), "Why" RICH_TEXT, "Done" CHECKBOX, "Episode" RELATION('<EPISODES_DS>', DUAL 'Actions'))
```
Give the databases icons: Episodes 🎧, Concepts 💡, Actions ✅ (with `notion-update-page` on each database page, if the create call didn't set them).

**d. Views** with `notion-create-view` (`database_id` + `data_source_id`):
- On Episodes, a table named "📥 Inbox": `FILTER "Status" IS EMPTY OR "Status" IN ("📥 To process", "⏳ Processing"); SORT BY "Added" ASC; SHOW "Title", "Link", "Status", "Progress"`.
- On Episodes, a gallery named "📚 Library": `FILTER "Status" = "✅ Done"; SORT BY "Added" DESC; SHOW "Podcast", "TL;DR", "Topics"`.
- On Actions, a table named "To do": `FILTER "Done" = FALSE; SHOW "Action", "Type", "Why", "Episode"`.
- Fetch the Concepts database and note the URL of its default view (`view://…`).

If a view fails, don't stop the setup: note it and carry on (the episode skill only needs the Inbox view and a Concepts view; any existing view of Concepts works).

**e. Save the configuration** with the Write tool at `${CLAUDE_PLUGIN_DATA}/config.json`:
```json
{
  "version": 1,
  "language": "<language>",
  "uv": "<uv command, see step 5>",
  "notion": {
    "hub_page": "<home page URL>",
    "context_page": "<My context page URL>",
    "episodes_db": "<Episodes database URL>",
    "episodes_ds": "collection://…",
    "inbox_view": "view://…",
    "concepts_db": "<Concepts database URL>",
    "concepts_ds": "collection://…",
    "concepts_view": "view://…",
    "actions_db": "<Actions database URL>",
    "actions_ds": "collection://…"
  },
  "created_at": "<ISO date>"
}
```
Fill `uv` after step 5 (write the file again).

## 5. Install the transcription tools
Podcast Brain transcribes episodes **on the user's computer** with free tools. They are installed by **uv**, which also installs the right Python by itself.

1. Check whether uv is there: run `uv --version`. If that fails, try the default install location: `~/.local/bin/uv --version` (Windows: `$HOME\.local\bin\uv.exe --version` in PowerShell).
2. If uv is missing, explain in one sentence ("I need to install **uv**, a free and widely used tool that installs Python for Podcast Brain: it takes a few seconds") and run the official installer:
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   Then use the full path (`~/.local/bin/uv`, or `$HOME\.local\bin\uv.exe` on Windows), because the current shell doesn't see the new command yet.
3. Save in the config `uv` = the command that works (`uv`, or the full path).
4. Run the health check (it installs everything the first time, about 1 minute; use a 10-minute timeout):
   ```
   <uv> run --script "${CLAUDE_PLUGIN_ROOT}/scripts/transcribe.py" --check --data "${CLAUDE_PLUGIN_DATA}"
   ```
   It must print `"ok": true`. If not, read the JSON, fix what you can, and explain the rest in plain words.
   `whisper_model_downloaded: false` is normal: the speech model (~500 MB) downloads by itself the first time an episode has no captions.

## 6. First episode
Say that everything is ready and ask for a first episode link, suggesting a **YouTube** episode (with captions it takes a couple of minutes). Then follow the `episode` skill of this plugin.

## 7. Wrap up
When the first page is ready, send a short message with:
- the link to their **🎧 Podcast Brain** page in Notion;
- the 3 ways to use it (paste a link here · Inbox in Notion + "process my inbox" · update "🧭 My context");
- one tip: long episodes without captions take about 10-15 minutes per hour of audio, and the computer must stay on meanwhile.

## Rules
- Never create anything outside the new Podcast Brain page, and never modify or delete existing Notion pages.
- Ask before installing uv. Don't install anything else.
- Never ask for passwords or API keys. Notion access goes only through the Claude connector.
- If something fails, explain it simply and offer the next step: don't leave the user with a raw error.

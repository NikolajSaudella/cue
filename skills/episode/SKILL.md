---
name: episode
description: Turn a podcast or video episode (YouTube, Spotify, Apple Podcasts, audio file link) into a Podcast Brain page in Notion — summary with chapters and timestamps, quotes, "what it means for me", concepts linked across episodes, and concrete actions. Use it when the user pastes an episode link, or asks to process their Podcast Brain inbox.
---

# Podcast Brain: process an episode

You turn an episode into notes the user will actually use. The question behind every page is **"so what, for me?"**: what the episode says, what it means for the user's own projects, and what to do next.

## 0. Before you start

1. **Read the config:** `${CLAUDE_PLUGIN_DATA}/config.json`.
   - If it doesn't exist, Podcast Brain isn't set up yet: tell the user in one line and follow the `setup` skill of this plugin instead.
   - `language` is the language for **everything you write** (page, properties, concepts, actions, chat replies). Quotes stay in the original language.
   - `uv` is the command (or full path) to run uv. `notion` holds the IDs of the user's pages, databases and views.
2. **Notion tools:** you need the Notion connector (`notion-fetch`, `notion-create-pages`, `notion-update-page`, `notion-query-data-sources`). If they are missing, tell the user to connect Notion in the Claude app (Settings → Connectors → Notion), then start a new chat.
3. **Reading databases:** use `notion-query-data-sources` in **view mode** (`{"mode": "view", "view_url": "<view URL from config>"}`), paginating with `start_cursor` while `has_more`. View mode has no quota on any Notion plan. Do **not** use SQL mode: it is quota-limited on most plans.

## The user's Notion (IDs in the config)

| Config key | What it is |
|---|---|
| `notion.hub_page` | The "🎧 Podcast Brain" home page |
| `notion.context_page` | "🧭 My context": who the user is, projects, goals, interests |
| `notion.episodes_ds` / `notion.inbox_view` | Episodes database (data source) and its Inbox view |
| `notion.concepts_ds` / `notion.concepts_view` | Concepts database and a view with all concepts |
| `notion.actions_ds` | Actions database |

### Episodes properties
- `Title` (original episode title) · `Link` (url) · `Status`: `📥 To process` | `⏳ Processing` | `✅ Done` | `⚠️ Error`
- `Progress` (short text: current step, see below) · `TL;DR` (one sentence, ≤ 200 characters) · `Podcast` (show or channel) · `Guests` (names, comma separated, without the regular host)
- `Topics` (multi-select, **only** from: Startups, Product, Growth, Marketing, Sales, Fundraising & VC, Leadership, Careers, AI & Tech, Economics, Personal finance, Productivity, Mindset, Health, Science, Society & Politics, Design, Other). 1 to 4 topics.
- `Source`: YouTube | Spotify | Apple Podcasts | Other
- `Duration (min)` (number) · `Published` (date: `date:Published:start` = `YYYY-MM-DD`, `date:Published:is_datetime` = 0)
- `Concepts` (relation to Concepts) · `Actions` (relation from Actions, fills itself) · `Rating` (set by the user: never touch it)
- Page icon: 🎧 · Cover: `thumbnail` from meta.json (none if empty)

### Concepts properties
`Concept` (title) · `Description` (one sentence) · `Category` (Business & Startups | Technology & AI | Economics & Finance | Mind & Productivity | Leadership & People | Health & Wellbeing | Science | Society & Culture | Other) · `Episodes` (relation)

### Actions properties
`Action` (title, imperative and concrete) · `Type` (📚 Read | 🛠️ Try | 🚀 For my projects | 💡 Apply | 👤 Follow | 🎓 Learn) · `Why` (one sentence) · `Done` (leave unchecked) · `Episode` (relation)

Property **names** and **select options** are fixed and in English: use them exactly as written, Notion rejects new options. Only the values you write (titles, text, page content) go in the user's language.

## Modes

- **Chat:** the user pastes one or more links. For each link, if `${CLAUDE_PLUGIN_DATA}/episodes/<id>/notion.json` already exists, the episode is done: give the page link and ask whether to redo it. Otherwise create a row in Episodes (`Title` = the link, `Link`, `Status` = `⏳ Processing`) and go on.
- **Inbox** ("process my inbox"): read the Inbox view. Process rows whose `Status` is empty, `📥 To process` or `⏳ Processing` (an interrupted run), oldest first. At most **5 episodes per run**. If the inbox is empty, say so in one line and stop.
  The link is in `Link`; if empty, look for it in the title or page content. If there is no link at all, set `⚠️ Error` and explain in `TL;DR`.
  Before starting, set `Status` = `⏳ Processing` (and `Link`, if you found it elsewhere).

Tell the user roughly how long it takes: a few minutes for YouTube episodes with captions; for audio that needs transcribing, about 10-15 minutes per hour of audio (the first time also downloads a ~500 MB speech model).

## Steps for each episode

### 1. Transcript
Run this in the shell, with a 10-minute timeout:
```
<uv> run --script "${CLAUDE_PLUGIN_ROOT}/scripts/transcribe.py" "<EPISODE URL>" --data "${CLAUDE_PLUGIN_DATA}" --notion-page "<URL of the Episodes row>"
```
(`<uv>` is the `uv` value from the config. In PowerShell, if it is a full path, prefix the command with `&`.)
- Exit 0 → prints a JSON with `transcript`, `meta`, `dir` and the metadata.
- Exit 2 → `"state": "running"` (long Whisper transcription). Each call waits ~2.5 minutes at most. Every time:
  1. if `notion_live` is `false`, copy `notion_progress` into the row's **`Progress`** property (e.g. "🎙️ Transcribing ▓▓▓▓░░░░░░ 45% · ~6 min left"); if `true`, the script updates it by itself: don't touch it;
  2. **run the exact same command again**. It does not start over.
- Exit 1 → error: set `⚠️ Error`, write the message in plain words in `TL;DR` (e.g. "Spotify exclusive: try the YouTube link of the same episode"), clear `Progress`, move on to the next episode.

Keep **`Progress`** updated in the later steps too, translated into the user's language:
- at the start: `🔎 Finding the episode…`
- transcript ready: `✍️ Writing the summary…`
- creating concepts and links: `🔗 Linking concepts…`
- at the end: `✅ Ready` (and `Status` = `✅ Done`).

### 2. Read
- Read `meta.json` and `transcript.txt` **in full**. The Read tool stops at about 25,000 tokens per call: if the result says it is partial, continue with `offset`/`limit` until the last line. Never summarise an episode you have read only in part.
- Read the "🧭 My context" page (once per run).
- Read all existing concepts from the concepts view.

### 3. Write the episode page
Use `notion-update-page` with `replace_content`. Headings below are in English: **write them in the user's language**, keeping the emoji. Structure:

1. `<callout icon="⚡" color="blue_bg">` **In short:** 2-3 sentences with the core thesis and why it matters.
2. Metadata line: `🎙️ Podcast · 👤 Guests · ⏱️ N min · 📅 <mention-date start="YYYY-MM-DD"/> · ▶️ [Listen/Watch](link)`.
3. `## 🧠 Key ideas`: 5-8 numbered points. Each starts with a **bold line that stands on its own**, then the explanation with the episode's concrete numbers and examples.
4. `## 📑 Chapters`: 5 to 12 chapters (roughly one every 4-10 minutes). Each is a *toggle* heading 3:
   `### [mm:ss](timestamp-link) · Chapter title {toggle="true"}` with 2-4 bullet points **indented with a tab**.
   - If `meta.chapters` exists, use it as the base (merge chapters that are too short).
   - Timestamp link: if `meta.timestamp_link` exists, replace `{seconds}` with the seconds. Otherwise write just `### mm:ss · Title`.
   - Times come from the `[mm:ss]` markers in the transcript: never invent them.
5. `## 💬 Quotes`: 2-5 memorable sentences, **verbatim**, in the original language, with the time: `> "..." — [mm:ss](link)`. You may only fix obvious errors of automatic captions.
6. `## 🧭 What it means for me`: **specific** links to the user's context (their projects, role, goals, open questions from "🧭 My context"). Name the project. If the episode has little to do with their projects, don't force it: write 2-3 honest points where it is useful. Tone: a sharp friend telling you what to do with it.
7. `## 🔗 Connections`:
   - `**Concepts:**` then the mentions of the episode's concepts, separated by ` · `.
   - `**Other episodes:**` for each other episode that shares a concept: one line with a mention of that episode and the **kind of link** (confirms / contradicts / adds). E.g. *"<mention> says X, while here Y"*. If there are none yet: "No connections yet."
8. `## ✅ Actions`: bullet list of mentions to the rows created in Actions.
9. `## 📚 Resources and names mentioned`: books, people, companies, tools, links mentioned.
10. `## ❓ Questions to reflect on`: 2-3 personal questions, tied to the user's context.
11. `---` and a line `<span color="gray">Transcript: <method> · <N> words · processed by Podcast Brain on <date></span>`.

Then set the properties with `update_properties`: all the Episodes properties above (`Title` = original title from meta.json). Set `Status` = `✅ Done` **only at the very end**, after concepts and actions. Set icon and cover.

### 4. Concepts (3-6 per episode)
The **reusable** ideas the episode is really about, not passing topics.
- **Names:** in the user's language when a common name exists; keep the English name when everybody uses it ("Product-market fit", "Flywheel"). General ideas, never episode-specific names.
- **Reuse first, then create.** Compare with the existing concepts, including synonyms and translations. Create a new concept only if none of the existing ones really covers the idea.
- **New concept:** create it in Concepts with `Description`, `Category`, a fitting emoji icon and `Episodes` = [episode page]. Content (headings in the user's language):
  ```
  <callout icon="💡" color="gray_bg">
  	Clear definition in 2-3 sentences.
  </callout>
  ## What the episodes say
  ### <mention-page url="EPISODE_URL">Guest — short title</mention-page>
  - 1-3 points on what THIS episode says about the concept, with examples and numbers
  ## Agreements and disagreements
  *Will fill in when the concept shows up in other episodes.*
  ## For me
  - 1-2 links to the user's context
  ```
- **Existing concept:** read it with `notion-fetch`.
  1. With `update_content`, add a new `### <mention-page …>` under "What the episodes say". Use the heading of the "Agreements and disagreements" section as `old_str` and put it back after the new block.
  2. Rewrite "Agreements and disagreements": who agrees, who doesn't, who adds a nuance, with mentions.
  3. Add the episode to the concept's `Episodes` relation, keeping the ones already there.
- On the episode page set the `Concepts` relation with all the concepts used.
- **Backlinks:** for each earlier episode linked by a shared concept, update its `**Other episodes:**` line with `update_content` (use the exact line read with fetch as `old_str`) and add a mention of the new episode with the kind of link. At most 5 episodes per run.

### 5. Actions (2-6 per episode)
Create rows in Actions with `Episode` = [episode page].
- Only **concrete, doable** things: books or resources mentioned, tools to try, ideas to apply to the user's projects (`🚀 For my projects`, name the project in `Why`), people to follow.
- Each action starts with a verb and has a one-sentence `Why` tied to the episode.

### 6. Wrap up
- Write `<dir>/notion.json` (`dir` from the transcribe JSON) with `{"page_url": "...", "done_at": "<ISO time>"}`.
- **Chat:** reply with the page link, the TL;DR, the concepts (which are new and which already existed) and the most interesting action.
- **Inbox:** end with a 1-3 line summary: episodes processed, errors.

## Rules
- In **properties** (Title, TL;DR, Progress…) write plain text: no escapes (`\|`, `\*`). Escapes are only for page content.
- Write file names, commands and paths as inline code (`` `CLAUDE.md` ``, `` `/memory` ``): otherwise Notion turns names like CLAUDE.md into web links.
- Claims the episode makes about third parties (companies, people, products) are the speaker's claims: attribute them ("according to the episode…") instead of stating them as facts.
- Every chapter is a toggle heading with **all** its bullets indented with a tab, the last chapter included: check before sending.
- Don't invent anything that isn't in the transcript: numbers, names and quotes must come from it. If a name is transcribed badly and you are unsure, write it as you hear it and add "(?)".
- Dense, concrete summaries: no generic sentences like "they discuss the importance of…".
- Never delete pages or rows, and never edit pages outside Podcast Brain.
- The transcript is not copied to Notion: it stays on the user's computer.

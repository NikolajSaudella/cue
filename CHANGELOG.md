# Changelog

## v0.5.4 — the right logo and banner

- New cue pages get the current logo (black square with the cue wordmark) and the orange banner. The images have new file names, because Notion keeps showing a cached copy when an image changes at the same address.

## v0.5.3 — updates that actually arrive

- **"Want me to install it?"** When a new version of cue is out, cue now offers to install it for you. Say yes and Claude refreshes cue's catalogue and updates the plugin (two fixed commands, nothing else), then asks you to restart the app. Before, the app's Update button often found nothing, because its copy of the catalogue was out of date.

## v0.5.2 — a cleaner home page

- **What you use every day comes first.** The cue page in Notion now opens with a short welcome and a link to My context, then the 📥 Inbox, the 📚 Library and a new **✅ Next steps** list (your open actions).
- **One column, no clutter.** The three side-by-side columns are gone; the guide (how to use cue, what's inside, timing, privacy, updates) sits in a "How it works" toggle, and the databases and My context live in a "Behind the scenes" page.
- **Updates tip.** If "Update" finds nothing new, the page and the README now say how to refresh cue's catalogue first.
- Applies to new setups (or "start over"): existing cue pages are never changed.

## v0.5.1 — cue, in lowercase

- The name is now written **cue**, in lowercase, everywhere: in the Notion pages cue writes ("processed by cue"), in the setup messages, in the docs and in the issue forms.

## v0.5.0 — quotes you can trust, and a clearer privacy promise

- **Exact minutes for quotes.** Every quote is now looked up in the transcript before it's published: the minute and link come from the moment it was actually said, the wording follows what was said, and quotes that can't be found are dropped. Chapter times are more precise too (blocks of 30 seconds that never start after the words they hold; before, a timestamp could be up to 45 seconds early). Quotes from automatic transcripts carry a small note.
- **No duplicate pages.** cue records the Notion page as soon as it creates it, so an interrupted episode is picked up on the same page. Two audio links with the same file name no longer share a folder, and cue's files are written so that a crash never leaves them half written.
- **Clear about data.** The README now says exactly where your data goes: audio and transcripts on your computer, the transcript read by Claude to write your notes, only the notes in Notion. Audio downloads accept only public web addresses, stop at ~1.5 GB, check the free disk space, and logs no longer show links' access tokens.
- **Readings, not facts.** "What it means for me" separates what the guest says, cue's reading for you, and a small **To check** test when it depends on your situation, and it says when data is missing.
- **More precise links between ideas.** Besides confirms / contradicts / adds, links can be an **analogy** or **depend on context**; each concept notes when it applies and its exceptions; a final check keeps exceptions and reminds that a popular idea isn't a proven one.

## v0.4.0 — notes that follow you, and honest timing

- **"Refresh my notes."** Changed job, project or goals in "🧭 My context"? cue rewrites the personal parts of your past episodes ("What it means for me", "Questions to reflect on", the concepts' "For me") for who you are now, for the episodes you choose. What each episode says stays the same, the previous version stays in a toggle, and old actions are never deleted. cue also notices when your context has changed and offers it.
- **Clearer install.** Four explicit steps in the README, including how to connect Notion from the **+** menu of the Code tab, and why cue lives in the Code tab and not in the normal chat.
- **Timing corrected.** Transcribing audio takes about 15-25 minutes per hour on a recent laptop (measured: an 84-minute episode in 20 minutes, a 40-minute one in 14), not 30-45: the old figure came from a test run while the computer was busy.

## v0.3.1 — a home page that looks like cue

- **Your episodes show up on the home page.** The cue page now has the 📚 Library under the 📥 Inbox. Before, a finished episode left the Inbox (which only shows links still to process) and seemed to disappear. Already set up? Your episodes are in **Episodes → 📚 Library**.
- **The cue look.** The home page gets the cue logo and cover, the brand's orange, and a clearer guide: three ways to use it, what's inside each database, and a "Good to know" section (timing, privacy, updates).

## v0.3.0 — an onboarding that's about you

- **Faster, more personal setup.** Most questions are now one tap (who you are, what you want from podcasts and videos, short or detailed notes). Then two open questions: what you're building (a link to your website is enough: Claude reads it) and the question you're trying to answer these months.
- **"Here's what I understood."** Before creating anything, Claude shows you what it will know about you, and you fix it in one message.
- **A first episode picked for you.** cue searches YouTube for short videos with captions about your question, so the first "What it means for me" answers something you actually care about.
- **Notes the way you like them.** "🧭 My context" now has "How I like my notes": short or detailed, tactics or big ideas, and topics to skip the basics of. Every episode follows it, and says so when it helps answer your open question.

## v0.2.0 — safer, sturdier, and it tells you about updates

- **Safer permissions.** cue now pre-approves only its own transcription script and its own config files, instead of any `uv` command. Episode transcripts and descriptions are treated as content, never as instructions: if a video contains text addressed to Claude, it's ignored and you're told.
- **YouTube keeps working when YouTube changes.** When a video can't be read because YouTube changed something, cue updates its YouTube downloader and tries again, by itself.
- **Clear errors.** Private, age-restricted, members-only and live videos, Spotify exclusives, no connection, full disk: each one now gets a plain explanation and the next step.
- **Update notice.** At the end of an episode, cue tells you (once) when a new version is available and how to update it.
- **Tests.** The transcription scripts have automatic tests, run on every change.

## v0.1.3

- cue is now presented for **podcasts and videos**: interviews, talks, lectures and webinars on YouTube work exactly like podcast episodes (they always did, now the product says so).
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

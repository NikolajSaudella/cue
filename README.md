<p>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/cue-logo-reversed.svg">
    <img src="docs/images/cue-logo.svg" alt="cue" width="160">
  </picture>
</p>

# cue

[![Claude plugin](https://img.shields.io/badge/Claude-plugin-ff5b1f)](https://code.claude.com/docs/en/plugins) [![License: MIT](https://img.shields.io/badge/license-MIT-171614)](LICENSE) [![Release](https://img.shields.io/github/v/release/NikolajSaudella/cue?label=version&color=171614)](https://github.com/NikolajSaudella/cue/releases)

**Podcasts and videos you actually remember — and what they mean for you.**

Paste a link to a podcast, a YouTube talk or a lecture. Cue writes a page in your Notion with what it says, what it means for *you*, and what to do next, and connects it to everything you've heard before. A free plugin for the Claude app.

*Why "cue"? A cue point is the exact spot in a track you jump back to; a retrieval cue is the hint that brings a memory back. Pronounced like the letter Q.*

[🇮🇹 Leggi in italiano](README.it.md)

<img src="docs/images/video-connections.jpg" alt="Every episode becomes ideas, and ideas connect across episodes: confirms, adds, disagrees">

▶ [Watch the 30-second video](https://github.com/user-attachments/assets/e10e5245-765c-46e8-b7ea-6ad10795b196)

## Try the live demo

**[Browse the demo →](https://app.notion.com/p/nikolaj1205/cue-demo-3e74ef8c88ab81df84e6fb5c93256e8b)** Real pages made by Cue from five Y Combinator episodes, for an example founder. No install needed.

<table>
  <tr>
    <td width="50%"><img src="docs/images/episode-for-me.png" alt="What it means for me"><br><sub>What it means for me: tied to your own projects</sub></td>
    <td width="50%"><img src="docs/images/concept-disagreement.png" alt="Two guests disagree"><br><sub>Connections: where guests agree or disagree</sub></td>
  </tr>
</table>

## What you get

- 🧠 **The key ideas**, with the real numbers and examples, and chapters with clickable timestamps
- 💬 **Quotes**, word for word, with the minute they were said
- 🧭 **What it means for you**: linked to your projects and goals, not generic advice
- 🔗 **A brain that grows**: ideas connect across everything you've processed, including where guests disagree
- ✅ **Actions**: concrete next steps, collected in one to-do list

Notes in the language you choose. Audio and transcripts stay on your computer.

## Install

You need the **Claude desktop app** (Windows or Mac) with a **Pro or Max** plan, and **Notion** connected to Claude (Settings → Connectors → Notion).

1. In the Claude app, open the **Code** tab and start a session in any folder.
2. Click **+** → **Plugins** → **Add plugin** → **Add marketplace**, and paste `https://github.com/NikolajSaudella/cue`
3. Select **cue** → **Install for you**. Then open a new chat and write **Set up Cue**.

Claude asks you 4 quick questions, creates your space in Notion, installs everything it needs (you just approve) and processes a first episode with you. About 5 minutes.

<details>
<summary>Using Claude Code in the terminal?</summary>

```
/plugin marketplace add NikolajSaudella/cue
/plugin install cue@cue
```
</details>

## Use it

- **Paste a link** in Claude: Spotify, Apple Podcasts, any YouTube video, or an audio file.
- **On your phone**: add the link to the 📥 Inbox in Notion, then tell Claude "process my inbox".
- **Keep "🧭 My context" up to date**: it's what makes the notes about you.

## FAQ

**Does it cost anything?** No. It runs on your Claude plan and free, open-source tools.

**Where does my data go?** Audio and transcripts stay on your computer; notes go only to your Notion. Cue has no server and no analytics.

**Is it safe?** The code is open, so anyone can read it. Cue only runs its own transcription scripts, installs Python through the official uv installer after asking you, and writes only to its own Notion pages and its own folder on your computer. It never asks for passwords or API keys.

**How long does it take?** A couple of minutes for YouTube videos with captions. Audio that needs transcribing takes roughly 30-45 minutes per hour on a typical laptop, in the background.

**How do I update it?** In the Claude app: **+** → **Plugins** → **Manage plugins** → **cue** → **Update**. To hear about new versions, click **Watch** → **Custom** → **Releases** at the top of this page.

**How do I remove it?** **+** → **Plugins** → **Manage plugins** → **cue** → **Uninstall**. Your Notion pages stay yours; cue's folder on your computer (transcripts and the speech model) goes away with it.

More questions, and how it works under the hood: [docs/how-it-works.md](docs/how-it-works.md).

---

**Next:** subscriptions to your favourite shows, a weekly digest, scheduled runs, and maybe other AI apps (ChatGPT / Codex). Ideas and bugs: [Issues](../../issues).

If Cue helps you, a ⭐ on GitHub helps others find it.

Built by [Nikolaj Saudella](https://www.linkedin.com/in/nikolajsaudella/): I was the product owner, [Claude Code](https://claude.com/claude-code) was the engineer. MIT License.

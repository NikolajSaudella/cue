<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/cue-logo-reversed.svg">
    <img src="docs/images/cue-logo.svg" alt="cue" width="180">
  </picture>
</p>

<h3 align="center">Podcast e video che ricordi davvero, e cosa significano per te.</h3>

<p align="center">Incolli il link di un podcast, di un talk su YouTube o di una lezione. Cue scrive una pagina nel tuo Notion con cosa dice, cosa significa <i>per te</i> e cosa fare, collegata a tutto quello che hai già ascoltato. Un plugin gratuito e open source per l'app Claude (serve un piano Claude Pro o Max).</p>

<p align="center"><b><a href="https://github.com/user-attachments/assets/0a614909-6b1b-490a-965a-43da737f889c">▶ Guarda il video di 30 secondi</a> · <a href="https://app.notion.com/p/nikolaj1205/cue-demo-3e74ef8c88ab81df84e6fb5c93256e8b">Sfoglia la demo</a> · <a href="#installazione">Installa</a> · <a href="README.md">🇬🇧 English</a></b></p>

<p align="center"><a href="https://code.claude.com/docs/en/plugins"><img src="https://img.shields.io/badge/Claude-plugin-ff5b1f" alt="Claude plugin"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-171614" alt="MIT license"></a> <a href="https://github.com/NikolajSaudella/cue/releases"><img src="https://img.shields.io/github/v/release/NikolajSaudella/cue?label=version&color=171614" alt="version"></a> <a href="https://github.com/NikolajSaudella/cue/actions/workflows/check.yml"><img src="https://github.com/NikolajSaudella/cue/actions/workflows/check.yml/badge.svg" alt="check"></a></p>

<a href="https://github.com/user-attachments/assets/0a614909-6b1b-490a-965a-43da737f889c"><img src="docs/images/video-unfold.jpg" alt="Un link dentro, tutto quello che conta fuori: in breve, citazioni, capitoli, cosa significa per me, azioni (clicca per il video di 30 secondi)"></a>

<p align="center"><sub><i>Perché "cue"? Il cue point è il punto preciso di una traccia da cui ripartire; il retrieval cue è lo spunto che fa tornare in mente un ricordo. Si pronuncia come la lettera Q.</i></sub></p>

## Guarda la differenza

Pagine vere della [demo](https://app.notion.com/p/nikolaj1205/cue-demo-3e74ef8c88ab81df84e6fb5c93256e8b) (in inglese): cinque video di Y Combinator, elaborati per un founder di esempio che costruisce software per ristoranti.

**Non solo un riassunto. Consigli per il tuo progetto.** Un talk su come trovare i primi 10 clienti diventa passi concreti per *questo* founder. [Apri la puntata →](https://app.notion.com/p/nikolaj1205/3e74ef8c88ab81778145e4edf8d00a5d)

<a href="https://app.notion.com/p/nikolaj1205/3e74ef8c88ab81778145e4edf8d00a5d"><img src="docs/images/see-for-me.png" alt="Cosa significa per me, scritto sul progetto del founder"></a>

**Quando due puntate tirano in direzioni diverse.** Un ospite dice che la tua rete di contatti è la fonte migliore di clienti, un altro che è una fonte meno sincera: cue li mette uno accanto all'altro. [Apri l'idea →](https://app.notion.com/p/nikolaj1205/3e74ef8c88ab8191a943ddd104cd34a2)

<a href="https://app.notion.com/p/nikolaj1205/3e74ef8c88ab8191a943ddd104cd34a2"><img src="docs/images/see-disagreement.png" alt="Due ospiti tirano in direzioni diverse sulla rete di contatti"></a>

**Un'idea. Quattro puntate.** "Do things that don't scale" torna in quattro video diversi, e l'idea tiene quello che ha detto ogni ospite. [Apri l'idea →](https://app.notion.com/p/nikolaj1205/3e74ef8c88ab811583d1d54e1713e67d)

<a href="https://app.notion.com/p/nikolaj1205/3e74ef8c88ab811583d1d54e1713e67d"><img src="docs/images/see-four-episodes.png" alt="Un'idea collegata a quattro puntate"></a>

## Cosa ottieni

- 🧠 **Le idee chiave**, con i numeri e gli esempi veri, e i capitoli con i minuti cliccabili
- 💬 **Le citazioni**, parola per parola, con il minuto
- 🧭 **Cosa significa per te**: legato ai tuoi progetti e obiettivi, non consigli generici
- 🔗 **Un cervello che cresce**: le idee si collegano tra tutto quello che hai elaborato, anche quando gli ospiti non sono d'accordo
- ✅ **Azioni**: passi concreti, raccolti in un'unica lista

Note nella lingua che scegli. Audio e trascrizioni sono salvati solo sul tuo computer.

## Installazione

Ti serve l'**[app Claude](https://claude.ai/download)** per computer (Windows o Mac) con piano **Pro o Max**, e un account **Notion** (va bene anche quello gratuito). Cue funziona nella scheda **Code** dell'app, non nella chat normale: solo Code può trascrivere sul tuo computer.

1. **Apri la scheda Code.** Nell'app Claude clicca **Code** in alto. Quando ti chiede una cartella, scegline una qualsiasi (va bene Documenti: cue non la tocca).
2. **Collega Notion.** Clicca **+** accanto alla casella di testo → **Connectors** → **Notion** → **Connect**, accedi e consenti l'accesso al tuo spazio di lavoro. Se Notion è già collegato, controlla solo che lì sia attivo.
3. **Aggiungi cue.** Clicca **+** → **Plugins** → **Add plugin** → **Add marketplace**, incolla `https://github.com/NikolajSaudella/cue`, poi seleziona **cue** → **Install for you**.
4. **Parti.** Apri una nuova sessione nella scheda Code e scrivi **Configura Cue**.

Claude ti fa qualche domanda veloce (quasi tutte con un clic, e basta il link al tuo sito), ti mostra cosa ha capito, crea il tuo spazio su Notion, installa quello che serve (tu approvi e basta) ed elabora una prima puntata scelta sulla domanda a cui stai lavorando. Circa 5 minuti.

<details>
<summary>Usi Claude Code dal terminale?</summary>

```
/plugin marketplace add NikolajSaudella/cue
/plugin install cue@cue
```

Per Notion usa il connettore del tuo account claude.ai (accedi con lo stesso account), oppure aggiungi il server di Notion con `claude mcp add --transport http notion https://mcp.notion.com/mcp` e accedi con `/mcp`.
</details>

## Come si usa

- **Incolla un link** in Claude: Spotify, Apple Podcasts, qualsiasi video YouTube o un file audio.
- **Dal telefono**: aggiungi il link nell'📥 Inbox di Notion, poi di' a Claude "elabora la mia inbox".
- **Tieni aggiornata "🧭 My context"**: è quello che rende le note su di te. Hai cambiato lavoro o progetto? Scrivi **"aggiorna le mie note"** e cue riscrive "Cosa significa per me" sulle puntate passate (la versione precedente resta in un blocco apribile).

## Domande frequenti

<details>
<summary><b>Costa qualcosa?</b></summary>

Il plugin è gratuito e open source. Ti serve un piano **Claude Pro o Max**, perché cue funziona nella scheda Code di Claude; anche gli strumenti di trascrizione che usa sono gratuiti.

</details>

<details>
<summary><b>Posso usarlo nella chat normale di Claude?</b></summary>

No, funziona nella scheda **Code** dell'app Claude, perché trascrive sul tuo computer. Stessa app, stesso piano, niente da pagare in più.

</details>

<details>
<summary><b>Quanto ci mette?</b></summary>

- **YouTube con sottotitoli:** pochi minuti in tutto.
- **Audio da trascrivere** (Spotify, Apple Podcasts, video senza sottotitoli): circa **15-25 minuti per ogni ora di audio**, in background.
- Dipende soprattutto dal processore e da quanto è occupato. La primissima volta cue scarica anche un modello vocale di circa 500 MB.

</details>

<details>
<summary><b>Su quali computer funziona?</b></summary>

Windows e Mac, con l'app Claude per computer. Finora provato su Windows 11: se lo provi su un Mac, raccontaci com'è andata nelle [Issues](../../issues).

</details>

<details>
<summary><b>Dove finiscono i miei dati?</b></summary>

**Cosa conserva cue:**
- **Il tuo computer:** le trascrizioni (l'audio viene cancellato dopo la trascrizione).
- **Il tuo Notion:** le note, mai la trascrizione completa.

**Con chi parla:**
- **Claude** legge la trascrizione per scrivere le note, alle condizioni del tuo piano Claude.
- **Il sito della puntata** (YouTube, l'hosting del podcast, la pagina pubblica di Spotify) per scaricare sottotitoli o audio, e la ricerca pubblica dei podcast di Apple per trovare il feed di una puntata Spotify.
- **Hugging Face**, una volta, per scaricare il modello vocale; **GitHub**, due volte al giorno, per vedere se c'è una nuova versione di cue. Non viene inviato niente su di te o sulle tue puntate.

Cue di suo non ha server, account né statistiche.

</details>

<details>
<summary><b>È sicuro?</b></summary>

Il codice è aperto, chiunque può leggerlo. Cue esegue solo i suoi programmi di trascrizione, scrive solo nelle sue pagine Notion e nella sua cartella, e non chiede mai password né chiavi API. Installa Python (con l'installer ufficiale di uv) solo dopo avertelo chiesto.

</details>

<details>
<summary><b>Come lo aggiorno o lo tolgo?</b></summary>

Nell'app Claude: **+** → **Plugins** → **Manage plugins** → **cue** → **Update** o **Uninstall**.

Se lo togli, le pagine Notion restano tue. Per sapere quando esce una nuova versione, clicca **Watch** → **Custom** → **Releases** in cima a questa pagina.

</details>

<details>
<summary><b>Qualcosa non funziona?</b></summary>

- **"Notion non è collegato":** nella scheda Code, **+** → **Connectors** → attiva Notion, poi apri una nuova sessione.
- **Troppe richieste di permesso:** i comandi di cue sono già approvati; per Notion scegli "Always allow" la prima volta.
- **Un video YouTube non va:** cue aggiorna da solo lo strumento di download e riprova. I video privati, con limite d'età o solo per membri non si possono leggere.
- **La trascrizione è lenta:** la colonna Progress su Notion mostra i minuti che mancano. Videochiamate ed esportazioni la rallentano.
- **Ancora bloccato?** Racconta a Claude cosa è successo con parole tue, o apri una [issue](../../issues).

</details>

Altre domande e come funziona sotto il cofano (in inglese): [docs/how-it-works.md](docs/how-it-works.md).

---

<p align="center"><b>In arrivo:</b> fare domande su tutto quello che hai ascoltato, iscrizioni ai tuoi programmi preferiti, un digest settimanale.<br>Idee e bug: <a href="../../issues">Issues</a> · Vuoi aiutare? <a href="CONTRIBUTING.md">CONTRIBUTING.md</a> · Se cue ti è utile, una ⭐ aiuta altri a trovarlo.</p>

<p align="center"><sub>Creato in meno di 48 ore da <a href="https://www.linkedin.com/in/nikolajsaudella/">Nikolaj Saudella</a>: io ho fatto il product owner, <a href="https://claude.com/claude-code">Claude Code</a> l'ingegnere. Licenza MIT.</sub></p>

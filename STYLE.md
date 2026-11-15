# Writing style

These rules apply to every page in `docs/`. The reader is a capable adult (a university graduate in Toronto) who is a complete beginner at French, practises about 30 minutes a day, and wants to speak, understand and write French up to CEFR level B2: conversations in Montreal and Quebec, bilingual work in Canada, texts and emails. Assume no grammar terms at all: every word such as "noun", "article", "tense" or "subjunctive" is explained the first time it appears. Don't talk down to them.

The goal of each page is that the reader can say, hear, read or write something new by the end of it, and knows why it works.

## Voice

- Talk to the reader as "you" in instructions ("Say the word out loud"). Use "we" when working through something together ("We want the verb to agree with the subject").
- Explanations are plain and direct. Grammar terms use the standard names a French teacher, a university course or the Language Portal of Canada would use, so the reader can follow other books and teachers later. Give the French name beside the English one the first time ("the **past participle**, *le participe passé*").
- Active voice, present tense, plain verbs.
- Be modest. Don't praise the language, accents, writers, apps or methods. Say what you hear and what to do.
- Use Canadian spelling in English: colour, centre, practise (the verb) and practice (the noun), so "a practice routine" but "practise the sound". Keep the original spelling in names and titles.

## How to explain

1. Sound first, then sight, then the name. Let the reader hear the example (an `fr` block with a play button), then see it written, then learn the term, then the formal rule.
2. The first time a grammar term appears, say what it means in words, and bold the term.
3. Start from what the reader already knows (from English, from earlier lessons, or from everyday life), and say where the comparison stops working. Name false friends where they come up.
4. Give a skill as numbered steps (where the tongue goes, how to build the verb form, what to check), then refer to the step numbers.
5. Every exercise has a target you can check: "say the line three times in a row at normal speed", "get 8 of 10 right".
6. Name a common mistake at the step where it happens, not only in a separate list.
7. Never write "clearly", "obviously", "it is easy", "simply", "just" (as in "just add -s") or "trivially". Show the step instead.
8. Keep one idea per paragraph, in 2 to 5 sentences.
9. Aim for about 20 words per sentence on average, never more than about 40, and vary the length. A page of identical short sentences reads like a machine wrote it.
10. Put labels next to what they label: the gloss next to the French line, the gender next to the noun, not "see the table above".
11. Leave out decoration. No fun facts or history asides that don't teach the skill. Quebec history has its own lessons.
12. One term per concept. If the book says "past participle", it doesn't also say "perfect participle", except once when introducing the term.
13. Say what to listen for. Every routine row names one thing to listen for ("the silent final s", "the vowel in *rue*").
14. Show rules with examples first, exceptions after. List an exception only if the reader will meet it at this level.

## French-book conventions

These keep the whole book consistent.

| Thing | Convention |
|---|---|
| Italics | Only for French words and phrases in running text: `*bonjour*`. Never for emphasis, English titles or terms. The site makes every italic French word clickable to hear it. |
| IPA | After the italic word, in slashes, no syllable dots, `ʁ` for r: `*bonjour* /bɔ̃ʒuʁ/`. Quebec pronunciations use square brackets: `*tu* /ty/, in Quebec [t͡sy]`. The first time a symbol appears, say the sound in words. |
| French in prose | Quotation marks are guillemets with non-breaking spaces inside: « Bonjour ». In English sentences, use straight double quotes for English words and italics for French. |
| French punctuation | Follows the OQLF table on spacing around punctuation. No space before `?`, `!` or `;` (the OQLF also allows a thin space; this book uses none). A non-breaking space before `:` and inside « ». The `fr` fence and the speaker labels are the one place a plain space before a colon is normal. `tools/check_french.py` checks this, and lesson 15-03 teaches it. |
| Numbers in French text | A space for thousands and a comma for decimals: 1 250, 4,50 $. Times as 14 h 30. Dates as le 5 mars 2027. The dollar sign follows the number. |
| tu and vous | Dialogues use vous with strangers, in shops and at work, and tu with friends and family. A dialogue says which it is in the lead-in sentence. Quebec habits (a quick tu in a casual shop, vous kept longer with older people) are explained in the "In Quebec" section. |
| Casual Quebec forms | Always marked: `{qc}` at the end of an `fr` line, and a sentence that says it is casual. Examples are *chu* for *je suis* and *t'sais*. The book teaches the standard form first and the casual form for recognising. |
| Sacres | Taught as "recognise, don't use". Named in the lessons that cover them, never inside dialogues the reader practises aloud. |
| Register labels | In notes and explanations, use these labels: formal, neutral, casual, Quebec, France, spoken, written. A word with no label is neutral and used everywhere. |
| Verbs | Infinitives in lists and tables. Conjugation tables show je, tu, il/elle/on, nous, vous, ils/elles, with the Quebec-casual forms in notes only. |
| Nouns | Always with an article (*le*, *la*, *un*, *une*), or a gender mark `(m.)` or `(f.)` after *l'* and in the plural. |
| Titles and headings | English titles and headings are in sentence case. French headings follow the same rule: only the first word and proper nouns take a capital. French words in an English title are fine where natural ("Être and introducing yourself"). |
| Names of tenses | In English prose, use the French name in lowercase when there is no common English one: passé composé, imparfait, futur simple, subjonctif. Say what it does in English the first time. |

## Language by stage

| Stages | Language of the explanations |
|---|---|
| 1 to 8 | English. French appears in `fr` blocks, italics and tables. |
| 9 and 10 | Instructions and section headings in French. Explanations still have English beside the French where a concept is new. |
| 11 to 16 | Explanations in French, written as `.fr` and `.en` pairs. A button on the page switches between them. Section headings are French (see `LESSON_TEMPLATE.md`). |

## The `fr` fence, `.fr`/`.en` pairs and New words tables

French examples and dialogues go in a fenced block named `fr`. One sentence or utterance per line:

````markdown
```fr
Serveuse: Bonjour! Qu'est-ce que je vous sers? | Hello! What can I get you?
Vous: Un café, s'il vous plaît. | A coffee, please.
Marc: Chu ben fatigué. {qc} | I'm really tired.
```
````

- An optional speaker label comes first: letters, digits or hyphens, then a colon and a space, with no space before the colon (`Serveuse:`, `Agente-2:`).
- ` | ` (space, bar, space) separates the English gloss. A line without it has no gloss.
- Flags go at the end of the French part: `{qc}` for a deliberately casual Quebec form, `{x}` for a deliberate error in a fix-the-error exercise.
- A blank line separates groups. A line starting with `#` is a comment.
- In VS Code the block shows as plain text. On the site each line gets a play button and a mic button, and the English hides behind a "Show translation" button, so the reader tries first.

In stages 11 to 16 (and in French explanations before that), a French paragraph is followed by its English version. The `{: .fr }` line is the last line of the paragraph:

```markdown
Le futur simple sert à parler de projets.
{: .fr }

The futur simple is used to talk about plans.
{: .en }
```

Every `.fr` paragraph needs an `.en` partner right after it. `tools/lint.py` checks this.

Every lesson ends with a `## New words` table (`## Nouveaux mots` in the French stages). It feeds the Anki decks and the vocabulary ledger:

```markdown
| French | English | Notes |
|---|---|---|
| *le café* | coffee | |
| *l'eau* (f.) | water | |
| *magasiner* | to shop | Quebec; France: *faire du shopping* |
```

Nouns carry an article or a gender mark, verbs are infinitives, adjectives show the masculine form and the feminine after a slash if it is irregular (*beau / belle*). Notes use the register labels above.

## Copyright

- Every dialogue, text and exercise is written for the book. Never copy a song lyric, a TV or film transcript, or an exercise from a textbook, even a few lines.
- Media lists are links only, to free and legal sources, each checked to exist.
- OQLF and Language Portal of Canada rules are summarised in our own words, with a link at the point of use.
- Lexique (CC BY-SA 4.0) and ipa-dict (MIT) are check tools only, and are credited on the credits page.

## Facts that change

Prices, app names, app features, government programs, test formats and laws change. Each lesson that uses one:

- takes it from the official site at writing time (never from memory),
- states the year ("as of 2026"),
- links the source at the point of use.

If a number or a product is not needed to learn the skill, leave it out. Politics and institutions are described neutrally, with dates and sources.

## Markdown that works on the site and in VS Code

The same files are read in VS Code's preview and built into the website (Zensical). These rules keep both working.

### Boxes

Use HTML containers with the `markdown` attribute. Leave a blank line after the opening tag and a blank line before the closing tag, or the content inside won't be processed. `DESIGN.md` shows how each one looks.

```html
<div class="example" markdown>

### Example 1: ordering a coffee

...

</div>

<div class="note" markdown>

...

</div>

<div class="warning" markdown>

...

</div>

<div class="practice" markdown>

## Practice routine (30 min)

| Minutes | Task | What to listen for |
|---|---|---|
| 5 | ... | ... |

</div>

<div class="move-on" markdown>

## Move on when

- [ ] ...

</div>
```

Collapsible answer:

```html
<details class="solution" markdown>
<summary>Answer</summary>

...

</details>
```

Don't use `!!!`, `???` or `===` blocks. They need indented content, which VS Code shows as a raw code block.

### Links, headings and figures

- Link between pages with relative paths to the `.md` file: `[gender and articles](../02-sounds-spelling-and-everyday-things/04-gender-and-articles.md)`.
- Keep punctuation out of headings that other pages link to, so the anchor stays stable.
- Figures are SVG files drawn by the scripts in `tools/figures/`. Alt text says what the figure shows.
- Code blocks are rare in this book. When one appears, it names its language.

## Patterns to avoid

These are signs of AI-generated text, collected from Wikipedia's "Signs of AI writing" page (including its 2026 updates) and from studies of words that language models overuse (Kobak et al. 2024; Juzek and Ward 2025; Liang et al. 2024). One or two of them can appear by chance in human writing; the problem is when they pile up. Treat them as hard rules here anyway, because the whole book is drafted with AI help and would otherwise drift toward them.

### Words: never use

delve, tapestry, testament, pivotal, underscore (as a verb), intricate, intricacies, meticulous, meticulously, showcase, garner, bolster, interplay, vibrant, multifaceted, realm, groundbreaking, renowned, nestled, seamless, seamlessly, commendable, noteworthy, invaluable, transformative, unparalleled, unveil, harness (as a verb), elucidate, burgeoning, foster, leverage (in any sense), quietly, deep dive, boasts, journey, unlock, elevate, master (as a verb), "key role", "key factor", "key takeaway", "key insight", "key concept".

Book senses are allowed: "key" only as in "answer key" (or a keyboard key), and grammar names such as passé composé, subjonctif or futur antérieur. French words that look like these English words (*vital*, *crucial*) are French and are not checked.

### Words: use rarely

crucial, vital, essential, comprehensive, notably, additionally, moreover, furthermore, consequently, ultimately, enhance, valuable, insights, practical, remarkable, nuanced, significant, robust, powerful, modern, rich, lush, best practice (name the practice and the reason instead). Prefer a plain word: "needed", "also", "so", "big".

### Phrases and patterns: never use

- "serves as", "stands as", "functions as" where "is" works. Write "The imparfait is the tense for habits", not "The imparfait serves as the tense for habits".
- Inflated importance: "plays a crucial role", "is a testament to", "is a cornerstone of", "sets the stage for", "marks a shift".
- A trailing "-ing" clause that adds vague commentary: "..., highlighting the importance of liaison", "..., underscoring...", "..., showcasing...".
- Disclaimers: "It's important to note that", "It's worth noting", "It is worth mentioning". State the warning directly instead: "Watch out: ...".
- Summary endings: a closing paragraph starting "In summary", "In conclusion", "To sum up" or "Overall,". Lessons end with the new words, the key terms and the link to the next lesson, not a recap.
- Chatbot lines: "Great question", "Certainly!", "Let's dive in", "Let's unpack this", "I hope this helps", "Let me know". Plain "Let's say it slowly" is fine.
- Vague attribution: "teachers agree", "experts say", "it is widely believed". Name the source or drop the claim.
- Negative parallelism: "not only X but also Y", "it's not X, it's Y", "no X, no Y, just Z". The one exception is correcting a specific mistake: "say the final vowel, don't swallow it".
- False ranges: "from X to Y" where X and Y are not two ends of one scale ("from Paris to poutine"). Real ranges are fine: "from 1 to 100", "from A1 to B2".
- Groups of three used for rhythm ("short, clear and natural"). A real list of three things is fine.
- Hedging about sources: "while details are limited", "based on available information".
- Hype about apps, methods or tricks: "revolutionize", "game-changing", "supercharge", "magic", "secret", "hack". Say what the thing does and what it can't do.
- Praise of the language, accents or writers: "timeless", "beloved", "iconic", "masterpiece", "breathtaking", "hauntingly beautiful", "musical", "romantic". Describe what you hear instead: "the stress falls on the last syllable of the group".

### Punctuation and characters

- Em dashes (the long dash character) almost never: at most one per 500 words, and never with spaces around them. Studies cited on Wikipedia found Claude uses em dashes more than professional writers do, so this takes active effort. Use a comma, a colon, parentheses or a new sentence instead. In this book the target is none at all.
- En dashes only in numeric ranges ("pages 9 to 16" or "9-16"), or write "9 to 16".
- Straight quotes and apostrophes only in English text and in `fr` blocks (`"` and `'`). In French prose, the only quotation marks are guillemets.
- No emoji, and no unicode bullets. Use Markdown `-` lists.
- Few exclamation marks in English prose. (Inside an `fr` block, `!` and `?` are part of the French and are fine.)

### Formatting

- Headings are in sentence case: "How to order at a café", not "How To Order At A Café". Proper nouns keep their capitals: Montréal, Québec, Toronto, Canada, Ontario, French, English, OQLF, CEFR, A1 to B2, IPA, Mauril, Radio-Canada, Anki, Windows, Edge, Chrome. Add a name to the allowlist in `tools/lint.py` when a lesson needs one, instead of lowercasing it.
- A term is bold once, where it is defined, and nowhere else. Don't use bold for emphasis.
- Don't write bullet lists where every item starts with a bold label and a colon, except in `## Key terms`. Use a sentence, a table or a real subheading.
- Each page has one H1 (the title). Don't skip heading levels (H2 straight to H4).
- Don't put `---` lines between sections.
- Use a list for real steps or real collections of items. If prose reads fine, use prose.
- Use tables for real tables of values (conjugations, practice routines, New words). A two-row table that should be a sentence should be a sentence.

### Don't over-correct

Wikipedia now also flags the opposite extreme: text that never uses a dash or a semicolon, uses only commas and periods, and keeps every sentence between 8 and 20 words. Write like a teacher sitting next to you at a café: plain "is" and "has" sentences, a colon or semicolon or parentheses where they fit, an occasional "usually" or "often", and sentences of different lengths.

## Self-check before a page is committed

1. Run `.venv/Scripts/python tools/lint.py <file or folder>`. It searches for em dashes, en dashes outside numeric ranges, curly quotes, emoji and every word in "never use", and checks headings, template sections, the routine minutes, `.fr`/`.en` pairs and `fr` fence lines.
2. Search for "serves as", "stands as", "important to note", "worth noting", "In summary", "In conclusion", "Overall,", "not only", "Let's dive", "simply", "just add".
3. Run `.venv/Scripts/python tools/check_french.py <file or folder>`. Every French line must pass, or be marked `{qc}` or `{x}` on purpose.
4. Recompute every answer, conjugation and table value, and the routine minutes (they add up to 30). Python is fine.
5. Check that each changing fact has a source link and "as of 2026", and that no copyrighted lyric, transcript or exercise appears.
6. Read the page once from top to bottom for rhythm. If several sentences in a row have the same length and shape, rewrite some of them.

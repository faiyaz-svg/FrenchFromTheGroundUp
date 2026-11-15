# Lesson template

Every lesson follows this layout, in this order. A lesson is short: 10 to 15 minutes of reading (about 700 to 1200 words of prose, never more than 1500), then a 30-minute practice routine the reader repeats on several days until the "Move on when" boxes are ticked. `fr` blocks, tables and figures don't count toward the word budget. For lessons with `.fr`/`.en` pairs, the English side is what is counted.

`STYLE.md` has the writing rules and the French-book conventions (italics, IPA, punctuation, tu and vous, the `fr` fence). `DESIGN.md` shows how each box looks.

## The layout

Stages 1 to 8, written in English:

```markdown
# Title of the lesson

<span class="tag tag-grammar">Grammar</span> <span class="tag tag-a1">A1</span>

After this lesson you can <one sentence: what the reader can say, hear, read or write>.

Before this: [Lesson name](../01-first-sounds-and-greetings/10-etre-and-introductions.md), [Lesson name](...). You need: nothing, or a pencil.

## The idea

2 to 4 short sections (### headings) that build the idea: sound first, then the
written form, then the name, then the rule. Each new grammar term is **bold**
where it is defined.

## Hear it

`fr` blocks and examples, each with a sentence before it saying what to listen
for. IPA for new sounds. Some lessons fold this into "The idea"; then leave
this heading out.

## Try it

3 to 5 exercises, each with its answer in a closed box.

## Say it

3 to 5 lines to say out loud, in an `fr` block. The reader uses the mic button
to check what they said.

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

## Common mistakes

At most 3, each one short: what goes wrong, why, and the fix.

## In Quebec

Optional. How people say it in Montreal. Casual forms are marked {qc} and called casual.

## New words

| French | English | Notes |
|---|---|---|
| *le café* | coffee | |

## Key terms

- **Term**: one-line definition.

Next: [Next lesson title](02-next-lesson.md)
```

## The tag line

Right under the title: one span for the lesson's area, one for the level, and `tag-review` when the lesson has the `review` flag in `tools/lessons.yml`.

| Area | Markup |
|---|---|
| Sounds | `<span class="tag tag-sounds">Sounds</span>` |
| Grammar | `<span class="tag tag-grammar">Grammar</span>` |
| Words | `<span class="tag tag-words">Words</span>` |
| Listen | `<span class="tag tag-listen">Listen</span>` |
| Speak | `<span class="tag tag-speak">Speak</span>` |
| Read | `<span class="tag tag-read">Read</span>` |
| Write | `<span class="tag tag-write">Write</span>` |
| Quebec | `<span class="tag tag-quebec">Quebec</span>` |
| Review | `<span class="tag tag-review">Review</span>` |

| Level | Markup |
|---|---|
| A1 (stages 1 to 4) | `<span class="tag tag-a1">A1</span>` |
| A2 (stages 5 to 8) | `<span class="tag tag-a2">A2</span>` |
| B1 (stages 9 to 12) | `<span class="tag tag-b1">B1</span>` |
| B2 (stages 13 to 16) | `<span class="tag tag-b2">B2</span>` |

## The language switch

| Stages | Language | Section headings |
|---|---|---|
| 1 to 8 | English explanations | English |
| 9 and 10 | French instructions and section labels, English beside new concepts | French |
| 11 to 16 | French explanations written as `.fr` and `.en` pairs | French |

In the French stages the same sections appear in the same order, with these fixed names. `tools/lint.py` accepts both the English and the French names in any lesson.

| English | French |
|---|---|
| After this lesson you can (goal line) | `## Objectif` |
| Before this: (line) | `## Avant de commencer` |
| `## The idea` | `## L'idée` |
| `## Hear it` | `## Écoutez` |
| `## Try it` | `## À vous` |
| `## Say it` | `## Dites-le` |
| `## Practice routine (30 min)` | `## Routine (30 min)` |
| `## Move on when` | `## Pour passer à la suite` |
| `## Common mistakes` | `## Erreurs fréquentes` |
| `## In Quebec` | `## Au Québec` |
| `## New words` | `## Nouveaux mots` |
| `## Key terms` | `## Termes clés` |
| `Next:` | `Suite :` |

French headings use sentence case like English ones. In the French stages the goal and the "before" line are sections with their own headings, and the first sentence of each is a `.fr`/`.en` pair. The `Suite :` line has a non-breaking space before the colon.

## "Before this" and "You need"

- "Before this:" links the earlier lessons this one uses. A lesson may only depend on lessons before it in `tools/lessons.yml`. Never use a word or rule that a later lesson teaches, unless it is glossed in place. If you need it, explain it in one sentence here and say which later lesson covers it.
- "You need:" names anything beyond the book: headphones, a pencil, the Mauril app. Say "nothing" if nothing.

## French blocks and paragraphs

Write dialogues and examples in an `fr` fence. The line format is in `STYLE.md`:

````markdown
```fr
Serveuse: Bonjour! Qu'est-ce que je vous sers? | Hello! What can I get you?
Vous: Un café, s'il vous plaît. | A coffee, please.
```
````

In stages 11 to 16, explanations are `.fr` and `.en` pairs (the `{: .fr }` line ends the paragraph, and the `.en` paragraph follows right after). Dialogues can stay in `fr` fences, which already hold their own English glosses.

## Figures

Figures (the IPA vowel chart, tense timelines, the layout of a French email) are SVG files drawn by Python. A lesson that needs one has a script `tools/figures/<stage-folder>/<lesson-slug>.py` that writes `docs/assets/figures/<stage-folder>/<lesson-slug>-<name>.svg`. Embed with a relative link and alt text that says what the figure shows.

## The practice routine

Each routine fills 30 minutes, and the minutes in the table must add up to 30. The default shape:

| Minutes | Task |
|---|---|
| 5 | Anki: today's cards |
| 12 | The new lesson: read it, then Try it |
| 6 | Listening: the stage's media list, or Mauril |
| 7 | Speaking out loud: shadowing, then Say it |

- Writing lessons take 4 minutes from listening or speaking, and give them to the writing task.
- From B1 (stage 9) the lesson block is 10 minutes, and the 2 minutes saved go to extra reading or listening.
- Every row has one thing to listen for.

```markdown
<div class="practice" markdown>

## Practice routine (30 min)

| Minutes | Task | What to listen for |
|---|---|---|
| 5 | Anki: today's cards, say each French word before you flip | The vowel in each word |
| 12 | Read the lesson. Do Try it with the answers closed | Where you hesitate |
| 6 | Listen to a slow dialogue from the stage media list. Stop and repeat each line | The final sound of each line |
| 7 | Shadow the Hear it lines, then do Say it with the mic | Your rhythm against the audio |

Repeat this routine on at least three days before you tick the boxes below.

</div>
```

## The "Move on when" checklist

3 to 5 boxes, each one something the reader can test: a score, a count, a recording, saying a line without looking.

```markdown
<div class="move-on" markdown>

## Move on when

- [ ] You can say all four lines in Say it at normal speed, with no stops.
- [ ] You score 8 out of 10 on the [fill in the blank](../practice/fill-in-the-blank.md) drill for this stage.

</div>
```

## Answers

Every exercise in "Try it" has its answer in a closed box right after it:

```markdown
<details class="solution" markdown>
<summary>Answer</summary>

*Je suis*, *tu es*, *elle est*.

</details>
```

## New words and key terms

- The New words table lists every word or phrase the lesson teaches, in the format in `STYLE.md`. Include only words the lesson teaches. It feeds the Anki deck, so the reader should be able to learn each row as a card.
- Key terms list grammar and language terms with one-line definitions, in the format `- **Term**: definition.` They feed the glossary page. A lesson with no new grammar term can have a short list or one entry.
- Common mistakes feed the common-mistakes page, so each one stands alone.

## A short example lesson

This skeleton shows the shape. A real lesson has 700 to 1200 words of prose.

````markdown
# Être and introducing yourself

<span class="tag tag-grammar">Grammar</span> <span class="tag tag-a1">A1</span>

After this lesson you can say who you are and where you are from, using the verb *être*.

Before this: [Greetings and politeness](08-greetings-and-politeness.md). You need: nothing.

## The idea

A **verb** is the word that says what someone is or does. *Être* means "to be". It changes
with the person, so you learn its six forms as a set.

## Hear it

Listen for the silent *s* in *tu es* /ty ɛ/: you hear only the open vowel of *è*.

```fr
Marc: Bonjour, je m'appelle Marc. Et vous? | Hello, my name is Marc. And you?
Léa: Moi, c'est Léa. Je suis de Toronto. | I'm Léa. I'm from Toronto.
Marc: Ah, tu es anglophone? | Ah, you're an English speaker?
```

## Try it

Fill in the form of *être*: *Nous ___ à Montréal.*

<details class="solution" markdown>
<summary>Answer</summary>

*Nous sommes à Montréal.*

</details>

## Say it

```fr
Je suis de Toronto.
Tu es de Montréal?
```

<div class="practice" markdown>

## Practice routine (30 min)

| Minutes | Task | What to listen for |
|---|---|---|
| 5 | Anki: today's cards | The vowel in each word |
| 12 | Read the lesson and do Try it | Where you hesitate |
| 6 | Listen to a slow dialogue | The silent final letters |
| 7 | Shadow the Hear it lines, then Say it | Your rhythm |

</div>

<div class="move-on" markdown>

## Move on when

- [ ] You can say the six forms of *être* from memory.

</div>

## Common mistakes

Writing *je es* instead of *je suis*. The forms of *être* don't follow a pattern, so learn them as a set.

## New words

| French | English | Notes |
|---|---|---|
| *être* | to be | |
| *anglophone* | English-speaking | |

## Key terms

- **Verb**: a word that says what someone is or does.

Next: [Your first slow dialogues](11-first-slow-dialogues.md)
````

## Lesson types

The layout fits every lesson. A few types add something:

- Sound lessons: IPA for each new sound, a figure or a mouth description, minimal pairs to hear, and a note on how Quebec French differs.
- Speaking lessons: a model dialogue in an `fr` block, a role-play for the reader's side, and lines for Say it.
- Listening lessons: dialogues to hear with the translation hidden, and questions about the details.
- Writing lessons: a model text, a template with blanks, and a short task. The "In Quebec" section gives OQLF conventions where they apply.
- Review lessons (the last of each stage): no new grammar. They bring back the stage's words and rules in one longer dialogue or task, and the "New words" table can be short.
- Quebec lessons: always mark casual forms with `{qc}` and explain when it is polite to use them.

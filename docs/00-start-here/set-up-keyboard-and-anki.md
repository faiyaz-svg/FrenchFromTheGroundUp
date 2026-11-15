# Set up keyboard and Anki

You need two tools for the routine: a way to type French accents and Anki for the flashcards. This page gets both working. It is short on purpose.

## Typing accents

The full steps are in the lesson Typing accents on your keyboard<!-- link: ../01-first-sounds-and-greetings/02-typing-accents.md -->. Until you reach it, here is the short version. On Windows, you can add a Canadian French or Canadian Multilingual Standard keyboard in Settings, under Time & language, then Language & region. Either one lets you type *é*, *è*, *ê*, *à*, *ç* and the other French letters. The lesson shows the keys and how to practise them.

## Anki

Anki is a free flashcard program that shows each card shortly before you would forget it.

- On a computer, Anki is free from [apps.ankiweb.net](https://apps.ankiweb.net/).
- On Android, AnkiDroid is free (its page says optional donations are welcome).
- On an iPhone, the app is AnkiMobile. As of 2026 the Anki site does not list a price on its front page, and it describes purchases as funding Anki's development. Check the current price in the App Store before you buy.

Make a free AnkiWeb account if you want your cards to sync between devices.

## Import the stage decks

The book builds one Anki deck per stage, as a `.apkg` file. The decks are in `docs/downloads/anki/` and are added stage by stage as the stages are written. Today the folder may be empty.

1. Download the deck for your stage.
2. In Anki, open File, then Import, and choose the file. On a phone, open the file and choose Anki.
3. Each lesson's New words table is a part of the deck, so you can study a stage's cards while you read its lessons.

## Cards that read French aloud

The cards use Anki's built-in text to speech, with a line like `{{tts fr_CA:French}}`. This reads the French side of the card in a Canadian French voice. It needs:

- Anki 2.1.20 or newer on a computer,
- AnkiDroid 2.17 or newer,
- AnkiMobile 2.0.56 or newer,
- a French (Canada) voice installed on the device (see [set up voices and audio](set-up-voices-and-audio.md)).

To check which voices Anki sees, add `{{tts-voices:}}` to a card template, preview a card and read the list. The details are in the [Anki manual](https://docs.ankiweb.net/templates/fields.html). Remove that line when you are done.

## How many new cards a day

With 30 minutes of study in total, 5 minutes go to cards. Set New cards/day to 10 or 15 in the deck options. If reviews take more than 5 minutes, lower it to 8 until the pile shrinks. A lower number you keep is better than a high one you abandon.

Say each French word out loud before you flip the card. That is the point of the speaking minutes inside the 5.

Next: [Set up Mauril and free media](set-up-mauril-and-free-media.md)

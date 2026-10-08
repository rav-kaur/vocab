# Listen-mode audio

The **Listen** tab plays one recording per set, for both decks (Essential
1-20 and Advanced 1-20). Each word is spoken with structure:

    "Word: abate."
    "Abate means: reduce, diminish."
    "In a sentence: her stress ... abated ..."

with pauses in between, so you can study hands-free with headphones and the
screen off. (Prefer the bare version without the spoken labels? Add
`--no-labels` to any command below.)

The recordings are not checked into the repo (they are large and easy to
regenerate). You generate them once on your own computer with the script here.

## Generate the recordings

You need internet on your computer (it uses Microsoft's free neural voices, no
API key).

1. Install the one dependency:

   ```
   python -m pip install edge-tts
   ```

2. Make one set first to pick a voice you like:

   ```
   python generate_audio.py --deck advanced --set 1
   ```

   Open the game, go to the **Listen** tab, switch the Deck dropdown to
   Advanced, choose Advanced 1, and press play.

3. Generate everything (both decks, 40 sets):

   ```
   python generate_audio.py
   ```

   Or one deck at a time:

   ```
   python generate_audio.py --deck essential
   python generate_audio.py --deck advanced
   ```

Files land in `../audio/` as `essential-1.mp3 ... essential-20.mp3` and
`advanced-1.mp3 ... advanced-20.mp3`. Re-running overwrites them.

(On Windows, if `python` is not found, use the full path to python.exe, e.g.
`& $py generate_audio.py`.)

## Change the voice

```
python generate_audio.py --voice en-US-JennyNeural --deck advanced --set 1
```

Voices worth trying: `en-US-AriaNeural` (default), `en-US-JennyNeural`,
`en-US-MichelleNeural`, `en-US-GuyNeural`, `en-US-EricNeural`,
`en-GB-SoniaNeural`, `en-GB-RyanNeural`. Full list: `--list-voices`.

## Adjust pacing

The pauses come from the three clips in `silence/` (short after the word,
medium after the definition, longer between words). Swap those files, or
change `--rate` (for example `--rate -15%` for slower speech).

## Notes

- Plain MP3, so it plays on the Listen tab, on your phone's lock screen, and
  through headphone controls.
- Offline: recordings stream fine online. For guaranteed offline playback on a
  phone, we can add a "download for offline" step later.

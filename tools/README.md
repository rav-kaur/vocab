# Listen-mode audio

The **Listen** tab in the game plays one recording per set. Each word is
spoken with structure so it is easy to follow by ear:

    "Word: abate."
    "Abate means: reduce, diminish."
    "In a sentence: her stress ... abated ..."

with pauses in between, so you can study hands-free with headphones and the
screen off. (Prefer the bare version without the spoken labels? Add
`--no-labels` to any command below.)

The recordings are not checked into the repo (they are large and easy to
regenerate). You generate them once on your own computer with the script here.

## Generate the recordings

You need internet on your computer for this (it uses Microsoft's free neural
voices, no API key).

1. Install the one dependency:

   ```
   pip install edge-tts
   ```

2. From this `tools` folder, make one set first to pick a voice you like:

   ```
   python generate_audio.py --set 1
   ```

   Open the game, go to the **Listen** tab, choose Essential 1, and press play.

3. When you are happy with the voice, generate all 20 sets:

   ```
   python generate_audio.py
   ```

Files are written to `../audio/essential-1.mp3` through `essential-20.mp3`.
Re-running overwrites them, so you can regenerate any time the word list
changes.

## Change the voice

```
python generate_audio.py --voice en-US-JennyNeural --set 1
```

Voices worth trying: `en-US-AriaNeural` (default), `en-US-JennyNeural`,
`en-US-MichelleNeural`, `en-US-GuyNeural`, `en-US-EricNeural`,
`en-GB-SoniaNeural`, `en-GB-RyanNeural`. See the full list with:

```
python generate_audio.py --list-voices
```

## Adjust pacing

The pauses come from the three clips in `silence/` (short after the word,
medium after the definition, longer between words). Swap those files for
longer or shorter silences to change the rhythm, or change `--rate` (for
example `--rate -15%` for slower speech):

```
python generate_audio.py --rate -15%
```

## No-install alternative (Windows, lower quality)

If you would rather not install anything, Windows can generate audio with its
built-in voices via PowerShell (System.Speech). The voice is more robotic than
edge-tts. Ask and I can provide that script instead.

## Notes

- The files are plain MP3, so they play on the Listen tab, on your phone's lock
  screen, and through headphone controls.
- Offline: recordings stream fine online. For guaranteed offline playback on a
  phone, we can add a "download for offline" step later.

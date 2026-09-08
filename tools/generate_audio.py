#!/usr/bin/env python3
"""
Generate audio recordings for the GRE Vocab "Listen" mode.

For each word it speaks, with spoken labels for structure:
    "Word: <word>."
    "<Word> means: <definition>."
    "In a sentence: <example>."
with pauses in between, then a longer pause before the next word.
Use --no-labels for the bare word/definition/example version.
It writes one MP3 per set into ../audio/essential-<N>.mp3

VOICE: uses Microsoft's free neural voices via the `edge-tts` package.
No API key. You just need internet on this computer.

------------------------------------------------------------------
ONE-TIME SETUP (run once):
    pip install edge-tts

GENERATE EVERYTHING (all 20 sets, ~a few minutes):
    python generate_audio.py

TRY ONE SET FIRST (recommended, to check the voice you like):
    python generate_audio.py --set 1

PICK A DIFFERENT VOICE:
    python generate_audio.py --voice en-US-JennyNeural --set 1

Good English voices to try (run the line above with each):
    en-US-AriaNeural     (warm, clear  - default)
    en-US-JennyNeural    (friendly)
    en-US-MichelleNeural (calm)
    en-US-GuyNeural      (male)
    en-US-EricNeural     (male, steady)
    en-GB-SoniaNeural    (British female)
    en-GB-RyanNeural     (British male)
List every available voice:
    python generate_audio.py --list-voices
------------------------------------------------------------------

No `ffmpeg` needed - pauses come from the small clips in ./silence/.
"""
import argparse, asyncio, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORDS = os.path.join(HERE, "audio_words.json")
SIL_DIR = os.path.join(HERE, "silence")
OUT_DIR = os.path.join(REPO, "audio")

DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_RATE = "-8%"    # slightly slower so the content is easy to process
DEFAULT_PITCH = "+0Hz"

# which silence clip goes after each segment
PAUSE_AFTER_WORD = "sil_short.mp3"   # ~0.4s
PAUSE_AFTER_DEF  = "sil_med.mp3"     # ~0.85s
PAUSE_BETWEEN    = "sil_long.mp3"    # ~1.5s  (before next word)


def load_silence():
    out = {}
    for fn in (PAUSE_AFTER_WORD, PAUSE_AFTER_DEF, PAUSE_BETWEEN):
        p = os.path.join(SIL_DIR, fn)
        if not os.path.exists(p):
            sys.exit(f"Missing silence clip: {p}")
        with open(p, "rb") as f:
            out[fn] = f.read()
    return out


async def tts_bytes(edge_tts, text, voice, rate, pitch, retries=3):
    """Return MP3 bytes for a piece of text."""
    text = (text or "").strip()
    if not text:
        return b""
    last = None
    for _ in range(retries):
        try:
            buf = bytearray()
            com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            async for chunk in com.stream():
                if chunk["type"] == "audio":
                    buf.extend(chunk["data"])
            if buf:
                return bytes(buf)
        except Exception as e:  # transient network hiccup -> retry
            last = e
            await asyncio.sleep(1.5)
    raise RuntimeError(f"TTS failed for {text!r}: {last}")


def _cap(s):
    return s[:1].upper() + s[1:] if s else s


def segments_for_word(w, labels=True):
    """Return a list of (spoken_text, pause_clip) for one word."""
    if labels:
        return [
            (f"Word: {w['w']}.", PAUSE_AFTER_WORD),
            (f"{_cap(w['w'])} means: {w['def']}.", PAUSE_AFTER_DEF),
            (f"In a sentence: {w['example']}", PAUSE_BETWEEN),
        ]
    return [
        (w["w"], PAUSE_AFTER_WORD),
        (w["def"], PAUSE_AFTER_DEF),
        (w["example"], PAUSE_BETWEEN),
    ]


async def build_set(edge_tts, words, sil, voice, rate, pitch, setnum, labels=True):
    items = [w for w in words if w["setNum"] == setnum]
    if not items:
        return None
    chunks = bytearray()
    for n, w in enumerate(items, 1):
        print(f"    [{n:>2}/{len(items)}] {w['w']}")
        for text, pause in segments_for_word(w, labels):
            chunks += await tts_bytes(edge_tts, text, voice, rate, pitch)
            chunks += sil[pause]
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"essential-{setnum}.mp3")
    with open(out, "wb") as f:
        f.write(chunks)
    kb = len(chunks) // 1024
    print(f"  -> saved audio/essential-{setnum}.mp3  ({kb} KB)")
    return out


async def main_async(args):
    try:
        import edge_tts
    except ImportError:
        sys.exit("edge-tts is not installed.  Run:  pip install edge-tts")

    if args.list_voices:
        voices = await edge_tts.list_voices()
        for v in sorted(voices, key=lambda x: x["ShortName"]):
            if v["Locale"].startswith("en"):
                print(f"{v['ShortName']:<26} {v['Gender']:<7} {v['Locale']}")
        return

    with open(WORDS, encoding="utf-8") as f:
        words = json.load(f)
    sil = load_silence()
    sets = sorted({w["setNum"] for w in words})
    if args.set:
        sets = [args.set]
    elif args.sample:
        sets = [1]

    labels = not args.no_labels
    print(f"Voice: {args.voice}   Rate: {args.rate}   Spoken labels: {'on' if labels else 'off'}")
    print(f"Generating {len(sets)} set(s) into {OUT_DIR}\n")
    for s in sets:
        print(f"Set {s}:")
        await build_set(edge_tts, words, sil, args.voice, args.rate, args.pitch, s, labels)
    print("\nDone. Open the game and go to the Listen tab.")


def main():
    ap = argparse.ArgumentParser(description="Generate GRE vocab Listen-mode audio.")
    ap.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts voice name")
    ap.add_argument("--rate", default=DEFAULT_RATE, help="speech rate, e.g. -8%% or +0%%")
    ap.add_argument("--pitch", default=DEFAULT_PITCH, help="pitch, e.g. +0Hz")
    ap.add_argument("--set", type=int, help="generate only this set number (1-20)")
    ap.add_argument("--sample", action="store_true", help="generate only Set 1")
    ap.add_argument("--no-labels", action="store_true",
                    help='omit the spoken "Word:", "means:", "In a sentence:" labels')
    ap.add_argument("--list-voices", action="store_true", help="list English voices and exit")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

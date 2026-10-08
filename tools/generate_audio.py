#!/usr/bin/env python3
"""
Generate audio recordings for the GRE Vocab "Listen" mode.

Covers both decks: Essential (Essential 1-20) and Advanced (Advanced 1-20).
For each word it speaks, with spoken labels for structure:
    "Word: <word>."
    "<Word> means: <definition>."
    "In a sentence: <example>."
with pauses in between, then a longer pause before the next word.
Use --no-labels for the bare word/definition/example version.

It writes one MP3 per set:
    ../audio/essential-<N>.mp3   and   ../audio/advanced-<N>.mp3

VOICE: uses Microsoft's free neural voices via `edge-tts`. No API key.

------------------------------------------------------------------
ONE-TIME SETUP:
    pip install edge-tts   (or:  python -m pip install edge-tts)

GENERATE EVERYTHING (both decks, all 40 sets):
    python generate_audio.py

JUST ONE DECK:
    python generate_audio.py --deck advanced
    python generate_audio.py --deck essential

TRY ONE SET FIRST (to pick a voice):
    python generate_audio.py --deck advanced --set 1

PICK A VOICE:
    python generate_audio.py --voice en-US-JennyNeural --deck advanced --set 1
    python generate_audio.py --list-voices
------------------------------------------------------------------
No ffmpeg needed - pauses come from the clips in ./silence/.
"""
import argparse, asyncio, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORDS = os.path.join(HERE, "audio_words.json")
SIL_DIR = os.path.join(HERE, "silence")
OUT_DIR = os.path.join(REPO, "audio")

DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_RATE = "-8%"
DEFAULT_PITCH = "+0Hz"

PAUSE_AFTER_WORD = "sil_short.mp3"
PAUSE_AFTER_DEF  = "sil_med.mp3"
PAUSE_BETWEEN    = "sil_long.mp3"


def load_silence():
    out = {}
    for fn in (PAUSE_AFTER_WORD, PAUSE_AFTER_DEF, PAUSE_BETWEEN):
        p = os.path.join(SIL_DIR, fn)
        if not os.path.exists(p):
            sys.exit(f"Missing silence clip: {p}")
        with open(p, "rb") as f:
            out[fn] = f.read()
    return out


def _cap(s):
    return s[:1].upper() + s[1:] if s else s


def segments_for_word(w, labels=True):
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


async def tts_bytes(edge_tts, text, voice, rate, pitch, retries=3):
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
        except Exception as e:
            last = e
            await asyncio.sleep(1.5)
    raise RuntimeError(f"TTS failed for {text!r}: {last}")


async def build_set(edge_tts, words, sil, voice, rate, pitch, coll, setnum, labels=True):
    items = [w for w in words if w.get("coll") == coll and w["setNum"] == setnum]
    if not items:
        return None
    chunks = bytearray()
    for n, w in enumerate(items, 1):
        print(f"    [{n:>2}/{len(items)}] {w['w']}")
        for text, pause in segments_for_word(w, labels):
            chunks += await tts_bytes(edge_tts, text, voice, rate, pitch)
            chunks += sil[pause]
    os.makedirs(OUT_DIR, exist_ok=True)
    fn = f"{coll.lower()}-{setnum}.mp3"
    with open(os.path.join(OUT_DIR, fn), "wb") as f:
        f.write(chunks)
    print(f"  -> saved audio/{fn}  ({len(chunks)//1024} KB)")
    return fn


async def main_async(args):
    try:
        import edge_tts
    except ImportError:
        sys.exit("edge-tts is not installed.  Run:  python -m pip install edge-tts")

    if args.list_voices:
        for v in sorted(await edge_tts.list_voices(), key=lambda x: x["ShortName"]):
            if v["Locale"].startswith("en"):
                print(f"{v['ShortName']:<26} {v['Gender']:<7} {v['Locale']}")
        return

    with open(WORDS, encoding="utf-8") as f:
        words = json.load(f)
    sil = load_silence()

    if args.deck == "all":
        colls = ["Essential", "Advanced"]
    else:
        colls = [args.deck.capitalize()]
    labels = not args.no_labels

    print(f"Voice: {args.voice}   Rate: {args.rate}   Labels: {'on' if labels else 'off'}")
    for coll in colls:
        setnums = sorted({w["setNum"] for w in words if w.get("coll") == coll})
        if args.set:
            setnums = [args.set] if args.set in setnums else []
        elif args.sample and coll == "Essential":
            setnums = [1]
        elif args.sample:
            setnums = []
        for s in setnums:
            print(f"{coll} {s}:")
            await build_set(edge_tts, words, sil, args.voice, args.rate, args.pitch, coll, s, labels)
    print("\nDone. Open the game and go to the Listen tab.")


def main():
    ap = argparse.ArgumentParser(description="Generate GRE vocab Listen-mode audio.")
    ap.add_argument("--deck", choices=["all", "essential", "advanced"], default="all",
                    help="which deck to generate (default: all)")
    ap.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts voice name")
    ap.add_argument("--rate", default=DEFAULT_RATE, help="speech rate, e.g. -8%% or +0%%")
    ap.add_argument("--pitch", default=DEFAULT_PITCH, help="pitch, e.g. +0Hz")
    ap.add_argument("--set", type=int, help="generate only this set number (1-20) within the deck(s)")
    ap.add_argument("--sample", action="store_true", help="generate only Essential 1")
    ap.add_argument("--no-labels", action="store_true",
                    help='omit the spoken "Word:", "means:", "In a sentence:" labels')
    ap.add_argument("--list-voices", action="store_true", help="list English voices and exit")
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()

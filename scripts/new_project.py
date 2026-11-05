#!/usr/bin/env python
"""Project setup for /tt-edit.

  1) put the track in a new folder (whole track, or a fragment):
     python new_project.py audio --src song.mp3 --dir <slug> [--from 41.2 --to 71.0]
  2) long track? list the strongest fragments first (prints JSON, cuts nothing):
     python new_project.py suggest --src song.mp3 [--len 30]
  3) after the format / text questions, write the HyperFrames scaffold:
     python new_project.py scaffold --dir <slug> [--size 1500x1500] [--no-hud] [--title "NAME"]

`audio` writes <slug>/assets/track.mp3 (an MP3 source is cut with -c copy, so the audio stays original;
anything else is encoded to MP3 320k). `scaffold` writes package.json, hyperframes.json, meta.json,
index.html (world host, hud host unless --no-hud, the <audio>), empty compositions/, renders/, snaps/,
and copies the skill fonts into assets/fonts/. Existing files are never overwritten.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
HF_FALLBACK = "0.8.181"  # the version all the example videos were made with


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def duration(p):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)])
    if r.returncode:
        sys.exit(f"ffprobe failed on {p}:\n{r.stderr}")
    return float(r.stdout.strip())


def codec(p):
    r = sh(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=nw=1:nk=1", str(p)])
    return r.stdout.strip()


def cmd_audio(a):
    src, d = Path(a.src), Path(a.dir)
    out = d / "assets" / "track.mp3"
    if out.exists():
        sys.exit(f"{out} already exists; pick another --dir")
    out.parent.mkdir(parents=True, exist_ok=True)
    cut = []
    if a.start is not None:
        cut += ["-ss", f"{a.start:.3f}"]
    if a.end is not None:
        cut += ["-to", f"{a.end:.3f}"]
    is_mp3 = codec(src) == "mp3"
    enc = ["-c:a", "copy"] if is_mp3 else ["-c:a", "libmp3lame", "-b:a", "320k"]
    r = sh(["ffmpeg", "-y", "-v", "error", *cut, "-i", str(src), "-map", "0:a:0", "-map_metadata", "-1", *enc, str(out)])
    if r.returncode:
        sys.exit(r.stderr)
    dur = duration(out)
    print(json.dumps({"track": str(out).replace("\\", "/"), "duration": round(dur, 3), "streamCopied": is_mp3,
                      "fragment": [a.start, a.end] if cut else None}, ensure_ascii=False))
    if not is_mp3:
        print("note: source is not MP3, encoded to MP3 320k", file=sys.stderr)


def cmd_suggest(a):
    import librosa
    import numpy as np

    y, sr = librosa.load(a.src, sr=22050, mono=True)
    hop = 512
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
    t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    _, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop, units="time")
    dur = len(y) / sr
    L = min(a.len, dur)
    step = 0.5
    starts = np.arange(0, max(dur - L, 0) + 1e-6, step)
    score = np.array([rms[(t >= s) & (t < s + L)].mean() for s in starts])
    picks = []
    for i in np.argsort(-score):
        s = float(starts[i])
        if all(abs(s - p) >= L * 0.75 for p, _ in picks):
            picks.append((s, float(score[i])))
        if len(picks) == 3:
            break
    top = picks[0][1] if picks else 1
    res = []
    for s, sc in picks:
        if len(beats):
            s = float(beats[np.argmin(np.abs(beats - s))])  # start on a beat
        res.append({"from": round(s, 2), "to": round(min(s + L, dur), 2), "relativeEnergy": round(sc / top, 2)})
    print(json.dumps({"duration": round(dur, 2), "length": L, "candidates": res}, ensure_ascii=False, indent=1))


def hf_version():
    r = sh(["npx", "--no-install", "hyperframes", "--version"], shell=sys.platform == "win32")
    m = re.search(r"\d+\.\d+\.\d+", r.stdout or "")
    return m.group(0) if m else HF_FALLBACK


def put(p, text):
    if p.exists():
        print(f"keep {p}")
        return
    p.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {p}")


def cmd_scaffold(a):
    d = Path(a.dir)
    track = d / "assets" / "track.mp3"
    if not track.exists():
        sys.exit(f"{track} not found; run `audio` first")
    w, h = (int(x) for x in a.size.lower().split("x"))
    res = "square" if w == h else ("portrait" if h > w else "landscape")
    dur = f"{duration(track):.2f}"
    slug = re.sub(r"[^a-z0-9-]+", "-", d.name.lower()).strip("-") or "tt-edit"
    title = a.title or d.name
    ver = hf_version()
    for sub in ("compositions", "renders", "snaps", "assets/fonts"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    for f in (SKILL / "assets" / "fonts").glob("*.ttf"):
        if not (d / "assets" / "fonts" / f.name).exists():
            shutil.copy2(f, d / "assets" / "fonts" / f.name)

    npx = f"npx --yes hyperframes@{ver}"
    put(d / "package.json", json.dumps({"name": slug, "private": True, "type": "module", "scripts": {
        "check": f"{npx} check", "render": f"{npx} render"}}, indent=2) + "\n")
    put(d / "hyperframes.json", json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "media": {"autoProxy": True}, "authoringSkill": "music-to-video"}, indent=2) + "\n")
    put(d / "meta.json", json.dumps({"id": slug, "name": slug}, indent=2) + "\n")

    def host(i, z, name):
        return (f'      <div\n        id="{name}"\n        data-composition-id="{name}"\n'
                f'        data-composition-src="compositions/{name}.html"\n        data-start="0"\n'
                f'        data-duration="{dur}"\n        data-track-index="{i}"\n        data-track-kind="graphics"\n'
                f'        data-width="{w}"\n        data-height="{h}"\n      ></div>\n')

    hosts = host(1, 1, "world") + ("" if a.no_hud else host(2, 2, "hud"))
    put(d / "index.html", f"""<!doctype html>
<html lang="ru" data-resolution="{res}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 100%; height: 100%; background: #000; }}
      #world {{ z-index: 1; }}
      #hud {{ z-index: 2; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}">
{hosts}      <audio id="track" class="clip" src="assets/track.mp3" data-start="0" data-duration="{dur}" data-track-index="0" data-volume="1"></audio>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
    print(f"hyperframes@{ver}, {w}x{h}, {dur} s. Now write compositions/world.html" + ("" if a.no_hud else " and compositions/hud.html"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("audio")
    p.add_argument("--src", required=True)
    p.add_argument("--dir", required=True)
    p.add_argument("--from", dest="start", type=float)
    p.add_argument("--to", dest="end", type=float)
    p = sp.add_parser("suggest")
    p.add_argument("--src", required=True)
    p.add_argument("--len", type=float, default=30)
    p = sp.add_parser("scaffold")
    p.add_argument("--dir", required=True)
    p.add_argument("--size", default="1500x1500")
    p.add_argument("--no-hud", action="store_true")
    p.add_argument("--title")
    a = ap.parse_args()
    {"audio": cmd_audio, "suggest": cmd_suggest, "scaffold": cmd_scaffold}[a.cmd](a)


if __name__ == "__main__":
    main()

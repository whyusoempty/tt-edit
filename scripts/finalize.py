#!/usr/bin/env python
"""Put the original audio back into the render and verify the result.

    python finalize.py --raw renders/raw.mp4 --audio assets/track.mp3 --out renders/NAME.mp4 [--fps 30]

Why: the HyperFrames renderer lowers the track by about 3 dB, and re-encoding a hot master to AAC loses
another ~0.6 LU. MP3/AAC sources are stream-copied (bit-exact); anything else goes to AAC 320k with a warning.

Prints a report and writes next to --out:
  <name>.report.json   size, frames, durations, loudness, audio MD5 match, black intervals
  <name>.sheet.jpg     12 evenly spaced frames, for a last look
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(f"failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    return r


def probe(p, *args):
    return json.loads(sh(["ffprobe", "-v", "error", "-of", "json", *args, str(p)]).stdout)


def audio_md5(p):
    out = sh(["ffmpeg", "-v", "error", "-i", str(p), "-map", "0:a:0", "-f", "md5", "-"]).stdout
    return out.strip().split("=")[-1]


def loudness(p):
    err = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(p), "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = err[err.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return {"lufs": float(i.group(1)) if i else None, "truePeak": float(tp.group(1)) if tp else None}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    raw, src, out = Path(a.raw), Path(a.audio), Path(a.out)

    sa = probe(src, "-show_entries", "stream=codec_name:format=duration", "-select_streams", "a:0")
    codec = sa["streams"][0]["codec_name"]
    dur = float(sa["format"]["duration"])
    copy = codec in ("mp3", "aac")
    acodec = ["-c:a", "copy"] if copy else ["-c:a", "aac", "-b:a", "320k"]
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-i", str(src), "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", *acodec, "-t", f"{dur:.3f}", "-movflags", "+faststart", str(out)])

    v = probe(out, "-count_frames", "-select_streams", "v:0", "-show_entries",
              "stream=width,height,r_frame_rate,nb_read_frames,duration")["streams"][0]
    oa = probe(out, "-select_streams", "a:0", "-show_entries", "stream=codec_name,duration")["streams"][0]
    md5_src, md5_out = audio_md5(src), audio_md5(out)
    ls, lo = loudness(src), loudness(out)

    bd = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-map", "0:v:0",
             "-vf", "blackdetect=d=0.05:pix_th=0.06", "-f", "null", "-"]).stderr
    black = [[float(m.group(1)), float(m.group(2))] for m in re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", bd)]

    frames = int(v["nb_read_frames"])
    step = max(1, frames // 12)
    sheet = out.with_suffix(".sheet.jpg")
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(out), "-vf",
        f"select='not(mod(n\\,{step}))',scale=375:-1,drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile=4x3",
        "-frames:v", "1", "-q:v", "3", str(sheet)])

    rep = {
        "file": str(out),
        "sizeMB": round(out.stat().st_size / 1e6, 1),
        "video": {"w": v["width"], "h": v["height"], "fps": v["r_frame_rate"], "frames": frames,
                  "expectedFrames": int(round(dur * a.fps)), "duration": float(v.get("duration", 0))},
        "audio": {"codec": oa["codec_name"], "duration": float(oa.get("duration", 0)), "sourceDuration": round(dur, 3),
                  "streamCopied": copy, "bitExact": md5_src == md5_out, "source": ls, "output": lo},
        "black": black,
        "sheet": str(sheet),
    }
    out.with_suffix(".report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if not copy:
        print(f"\nWARNING: source codec {codec} cannot be stream-copied into MP4; encoded AAC 320k. Compare loudness above.")
    if copy and md5_src != md5_out:
        print("\nWARNING: audio is not bit-exact with the source.")
    if abs(frames - rep["video"]["expectedFrames"]) > 1:
        print("\nWARNING: frame count differs from duration x fps.")


if __name__ == "__main__":
    main()

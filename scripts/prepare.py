#!/usr/bin/env python
"""Track analysis for /tt-edit.

    python prepare.py --audio assets/track.mp3 --lyrics LYRICS.txt --out transcript [--lang ru]

Writes into --out:
  vocals.wav, instrumental.wav   Demucs two-stem split
  words-prompt.json              faster-whisper large-v3 word timestamps, lyrics as the prompt
  words-raw.json                 the same without the prompt (cross-check)
  timing.json                    lines and words in the USER'S spelling + beats, kicks, gaps, sections, energy,
                                 and a rough "sound" profile (brightness, sub, hats, four-on-floor, lo-fi, key)
  TRANSCRIPT.md                  the same as tables, plus the list of words to verify by ear

Stages whose outputs already exist are skipped; --force redoes them.
The user's lyrics are the source of truth for every word; Whisper only supplies the times.
"""
import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HOP = 256
SR = 22050


def log(*a):
    print(*a, flush=True)


def run(cmd):
    log("$", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def probe_duration(p):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out.strip())


# ---------- stage 1: vocals / instrumental ----------
def separate(audio, out, force):
    voc, inst = out / "vocals.wav", out / "instrumental.wav"
    if voc.exists() and inst.exists() and not force:
        log("demucs: cached")
        return voc, inst
    tmp = out / "_demucs"
    base = [sys.executable, "-m", "demucs", "--two-stems=vocals", "-o", str(tmp)]
    try:
        run(base + [str(audio)])
    except subprocess.CalledProcessError:
        log("demucs failed on the default device, retrying on CPU")
        run(base + ["-d", "cpu", str(audio)])
    found = list(tmp.rglob("vocals.wav"))
    if not found:
        sys.exit("demucs produced no vocals.wav")
    d = found[0].parent
    shutil.move(str(d / "vocals.wav"), voc)
    shutil.move(str(d / "no_vocals.wav"), inst)
    shutil.rmtree(tmp, ignore_errors=True)
    return voc, inst


# ---------- stage 2: word timestamps ----------
_model = {}


def whisper_words(voc, lang, prompt):
    from faster_whisper import WhisperModel

    def go(device, ctype):
        key = device + ctype
        if key not in _model:
            _model[key] = WhisperModel("large-v3", device=device, compute_type=ctype)
        segs, _ = _model[key].transcribe(
            str(voc), language=lang, word_timestamps=True, initial_prompt=prompt, vad_filter=False, beam_size=5
        )
        return [
            {"w": w.word.strip(), "s": round(float(w.start), 3), "e": round(float(w.end), 3), "p": round(float(w.probability), 2)}
            for s in segs for w in s.words
        ]

    if "cpu" not in _model.get("_dev", ""):
        try:
            words = go("cuda", "float16")
            _model["_dev"] = "cuda"
            return words
        except Exception as e:  # no CUDA build, no cuDNN, ...
            log(f"whisper on CUDA failed ({type(e).__name__}), using CPU int8")
            _model["_dev"] = "cpu"
    return go("cpu", "int8")


def transcribe(voc, out, lang, lyrics_flat, force):
    res = {}
    for name, prompt in (("words-prompt.json", lyrics_flat), ("words-raw.json", None)):
        p = out / name
        if p.exists() and not force:
            log(f"whisper {name}: cached")
            res[name] = json.loads(p.read_text(encoding="utf-8"))
            continue
        log(f"whisper {name} ...")
        words = whisper_words(voc, lang, prompt)
        p.write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
        res[name] = words
    return res["words-prompt.json"], res["words-raw.json"]


# ---------- lyrics ----------
def norm(w):
    return re.sub(r"[\W_]+", "", w.lower().replace("ё", "е"))


def parse_lyrics(text):
    """Lines as sung; [Припев] / (x2) style markers are dropped."""
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or re.fullmatch(r"[\[(].*[\])]", s):
            continue
        toks = []
        for t in s.split():
            if norm(t):
                toks.append({"w": t, "n": norm(t)})
            elif toks:
                toks[-1]["w"] += " " + t  # a dash or other bare punctuation sticks to the previous word
        if toks:
            lines.append(toks)
    return lines


# ---------- stage 3: audio features ----------
def vocal_features(voc):
    import librosa
    import numpy as np

    y, sr = librosa.load(str(voc), sr=SR, mono=True)
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=HOP)[0]
    db = 20 * np.log10(rms + 1e-9)
    db -= np.percentile(db, 99)
    t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=HOP)
    voiced = db > -32
    gaps, i, n = [], 0, len(voiced)
    while i < n:
        if not voiced[i]:
            j = i
            while j < n and not voiced[j]:
                j += 1
            a, b = float(t[i]), float(t[j - 1])
            if b - a >= 0.18:
                gaps.append([round(a, 2), round(b, 2)])
            i = j
        else:
            i += 1
    on = librosa.onset.onset_detect(y=y, sr=sr, hop_length=HOP, units="time", backtrack=True)
    start = float(t[np.argmax(voiced)]) if voiced.any() else 0.0
    return {"gaps": gaps, "onsets": [round(float(x), 3) for x in on], "start": round(start, 2)}


def music_features(track, inst, dur):
    import librosa
    import numpy as np

    yi, sr = librosa.load(str(inst), sr=SR, mono=True)
    tempo, beats = librosa.beat.beat_track(y=yi, sr=sr, hop_length=HOP, units="time")
    tempo = float(np.atleast_1d(tempo)[0])
    # kicks: onsets of the band under 150 Hz
    S = np.abs(librosa.stft(yi, n_fft=2048, hop_length=HOP))
    f = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low = S[f < 150].sum(axis=0)
    env = np.maximum(0.0, np.diff(low, prepend=low[0]))
    env = env / (env.max() + 1e-9)
    pk = librosa.util.peak_pick(env, pre_max=3, post_max=3, pre_avg=12, post_avg=12, delta=0.1, wait=int(0.18 * sr / HOP))
    kicks = librosa.frames_to_time(pk, sr=sr, hop_length=HOP)
    # energy of the full mix, 0..1 every 0.5 s
    y, _ = librosa.load(str(track), sr=SR, mono=True)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=HOP)[0]
    tt = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=HOP)
    grid = np.arange(0, dur, 0.5)
    e = np.array([rms[(tt >= g) & (tt < g + 0.5)].mean() if ((tt >= g) & (tt < g + 0.5)).any() else 0 for g in grid])
    e = (e - e.min()) / (e.max() - e.min() + 1e-9)
    w = max(1, int(round(1.0 / (HOP / sr))))
    sm = np.convolve(rms, np.ones(w) / w, mode="same")
    peak = float(tt[int(np.argmax(sm))])
    # coarse sections: agglomerative clustering on beat-synced timbre + harmony
    k = int(min(8, max(2, round(dur / 12))))
    mf = librosa.feature.mfcc(y=y, sr=sr, hop_length=HOP, n_mfcc=13)
    ch = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=HOP)
    feat = np.vstack([librosa.util.normalize(mf, axis=1), ch])
    bf = librosa.time_to_frames(beats, sr=sr, hop_length=HOP) if len(beats) > k + 2 else None
    if bf is not None:
        fs = librosa.util.sync(feat, bf)
        b = librosa.segment.agglomerative(fs, k)
        edges = [0.0] + [float(beats[max(0, i - 1)]) for i in b[1:]]
    else:
        b = librosa.segment.agglomerative(feat, k)
        edges = [float(x) for x in librosa.frames_to_time(b, sr=sr, hop_length=HOP)]
    edges = sorted(set(round(x, 2) for x in edges)) + [round(dur, 2)]
    sections = [{"id": f"S{i + 1}", "start": edges[i], "end": edges[i + 1]} for i in range(len(edges) - 1)]
    return {
        "tempoBpm": round(tempo, 1),
        "beatSec": round(60 / tempo, 3) if tempo else None,
        "beats": [round(float(x), 3) for x in beats],
        "kicks": [round(float(x), 3) for x in kicks],
        "energy": [[round(float(g), 1), round(float(v), 2)] for g, v in zip(grid, e)],
        "energyPeak": round(peak, 2),
        "sections": sections,
    }


# ---------- stage 3b: what the track sounds like (rough, for the model's genre guess) ----------
KS_MAJ = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
KS_MIN = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def sound_features(track, voc, inst, mf, dur):
    import librosa
    import numpy as np

    y2, sr = librosa.load(str(track), sr=SR, mono=False)
    if y2.ndim == 1:
        y2 = np.vstack([y2, y2])
    y = y2.mean(axis=0)
    rms_all = float(np.sqrt(np.mean(y ** 2))) + 1e-9
    width = float(np.sqrt(np.mean(((y2[0] - y2[1]) / 2) ** 2)) / rms_all)

    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP))
    f = librosa.fft_frequencies(sr=sr, n_fft=2048)
    P = S ** 2
    tot = P.sum() + 1e-12

    def band(a, b):
        return float(P[(f >= a) & (f < b)].sum() / tot)

    bands = {"sub_20_60": band(20, 60), "bass_60_250": band(60, 250), "mid_250_4k": band(250, 4000), "high_4k_up": band(4000, sr / 2 + 1)}
    centroid = float(np.median(librosa.feature.spectral_centroid(S=S, sr=sr)))
    rolloff = float(np.percentile(librosa.feature.spectral_rolloff(S=S, sr=sr, roll_percent=0.95), 90))
    flatness = float(np.median(librosa.feature.spectral_flatness(S=S)))
    rms = librosa.feature.rms(S=S, frame_length=2048)[0]
    db = 20 * np.log10(rms + 1e-9)
    dyn = float(np.percentile(db, 95) - np.percentile(db, 10))
    crest = float(20 * np.log10(np.max(np.abs(y)) / rms_all))
    H, Pc = librosa.decompose.hpss(S[f >= 150])  # above the 808 / bass, which is sustained and would read as "harmonic"
    perc = float((Pc ** 2).sum() / ((H ** 2).sum() + (Pc ** 2).sum() + 1e-12))

    yv, _ = librosa.load(str(voc), sr=SR, mono=True)
    yi, _ = librosa.load(str(inst), sr=SR, mono=True)
    ev, ei = float(np.mean(yv ** 2)), float(np.mean(yi ** 2))
    vocal_share = ev / (ev + ei + 1e-12)

    # hi-hat density: onsets of the instrumental above 5 kHz
    Si = np.abs(librosa.stft(yi, n_fft=2048, hop_length=HOP))
    hi = Si[f > 5000].sum(axis=0)
    env = np.maximum(0.0, np.diff(hi, prepend=hi[0]))
    hats = librosa.onset.onset_detect(onset_envelope=env / (env.max() + 1e-9), sr=sr, hop_length=HOP, units="time")
    hats_per_sec = len(hats) / max(dur, 1e-6)

    # four-on-the-floor: share of beats with a kick within 70 ms
    beats, kicks = np.array(mf["beats"]), np.array(mf["kicks"])
    four = float(np.mean([np.min(np.abs(kicks - b)) < 0.07 for b in beats])) if len(beats) and len(kicks) else 0.0

    # key, Krumhansl-Schmuckler on the instrumental chroma
    chroma = librosa.feature.chroma_cqt(y=yi, sr=sr, hop_length=HOP * 2).mean(axis=1)
    best = max(((np.corrcoef(np.roll(prof, k), chroma)[0, 1], k, mode)
                for prof, mode in ((KS_MAJ, "major"), (KS_MIN, "minor")) for k in range(12)))
    key = f"{NOTES[best[1]]} {best[2]}"

    bpm = mf["tempoBpm"] or 0
    words = []
    if bpm >= 130 and four < 0.6:
        words.append(f"темп {bpm:.0f}, но без прямой бочки — может ощущаться вдвое медленнее (~{bpm / 2:.0f}, half-time)")
    elif bpm and bpm < 70:
        words.append(f"темп {bpm:.0f} — возможно, librosa взяла половину, реальный ~{bpm * 2:.0f}")
    if four >= 0.7:
        words.append("прямая бочка почти на каждую долю (хаус, техно, синтвейв, диско, гиперпоп)")
    if hats_per_sec >= 4:
        words.append(f"частые хэты ~{hats_per_sec:.1f}/с (трэп, фонк, драм-н-бейс)")
    if bands["sub_20_60"] >= 0.12:
        words.append("мощный саб-бас (808, трэп, фонк, дабстеп)")
    elif bands["sub_20_60"] + bands["bass_60_250"] >= 0.55:
        words.append("басовитый, плотный низ")
    if centroid < 1500:
        words.append("тёмный, глухой")
    elif centroid > 3000:
        words.append("яркий, звонкий")
    if rolloff < 9000:
        words.append("срезанный верх — лоу-фай, винтаж, кассета")
    if flatness > 0.05:
        words.append("шумный, перегруженный (дисторшн, гитары, нойз)")
    if dyn < 9:
        words.append("сильно сжатый громкий мастер")
    elif dyn > 18:
        words.append("большая динамика, тихие и громкие места")
    if perc >= 0.4:
        words.append("барабаны впереди")
    elif perc < 0.15:
        words.append("мелодичный, мало ударных (эмбиент, баллада, акустика)")
    if vocal_share >= 0.45:
        words.append("вокал впереди микса")
    elif vocal_share < 0.15:
        words.append("вокал утоплен в миксе")
    if width < 0.12:
        words.append("почти моно")
    elif width > 0.5:
        words.append("широкая стереобаза")
    words.append(f"тональность примерно {key} ({'мажор' if 'major' in key else 'минор'})")

    r = lambda v, n=3: round(float(v), n)
    return {
        "bands": {k: r(v) for k, v in bands.items()},
        "centroidHz": r(centroid, 0), "rolloff95Hz": r(rolloff, 0), "flatness": r(flatness, 4),
        "dynamicRangeDb": r(dyn, 1), "crestDb": r(crest, 1), "percussiveShare": r(perc), "vocalShare": r(vocal_share),
        "hatsPerSec": r(hats_per_sec, 2), "fourOnFloor": r(four, 2), "stereoWidth": r(width), "key": key,
        "summary": words,
    }


# ---------- stage 4: align the user's words to Whisper's times ----------
def align(lines, words, vf):
    U = [tok for ln in lines for tok in ln]
    Wn = [norm(w["w"]) for w in words]
    for tok in U:
        tok.update(s=None, e=None, p=None, src=None)
    sm = difflib.SequenceMatcher(None, [t["n"] for t in U], Wn, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                w = words[j1 + k]
                U[i1 + k].update(s=w["s"], e=w["e"], p=w["p"], src="match" if op == "equal" else "fuzzy")
        elif op == "replace":
            a, b = words[j1]["s"], words[j2 - 1]["e"]
            total = sum(len(t["n"]) for t in U[i1:i2])
            acc = 0
            for t in U[i1:i2]:
                s = a + (b - a) * acc / total
                acc += len(t["n"])
                t.update(s=s, e=a + (b - a) * acc / total, p=min(w["p"] for w in words[j1:j2]), src="spread")
    # words Whisper never produced: share the time between their neighbours
    i = 0
    while i < len(U):
        if U[i]["s"] is not None:
            i += 1
            continue
        j = i
        while j < len(U) and U[j]["s"] is None:
            j += 1
        a = U[i - 1]["e"] if i > 0 else vf["start"]
        b = U[j]["s"] if j < len(U) else a + 0.4 * (j - i)
        total = sum(len(t["n"]) for t in U[i:j]) or 1
        acc = 0
        for t in U[i:j]:
            s = a + (b - a) * acc / total
            acc += len(t["n"])
            t.update(s=s, e=a + (b - a) * acc / total, p=0.0, src="interp")
        i = j
    # clean up with the vocal envelope. Whisper tends to start a word exactly where the previous one ended,
    # even across a pause; onset snapping was tested and made things worse, so weak words are only flagged.
    if U and U[0]["s"] < vf["start"]:
        U[0]["s"] = vf["start"]
    prev_e = None
    for t in U:
        contiguous = prev_e is not None and t["s"] - prev_e < 0.03
        for g0, g1 in vf["gaps"]:
            if t["s"] < g1 < t["e"] and (t["s"] >= g0 - 0.02 or contiguous):
                t["s"], t["src"] = g1, t["src"] + "+gap"  # the real onset is the end of the silence
            elif t["s"] < g0 < t["e"] <= g1 + 0.02 and g0 - t["s"] > 0.08:
                t["e"] = g0
        prev_e = t["e"]
    ons = vf["onsets"]
    prev = -1.0
    for t in U:
        t["s"] = max(t["s"], prev + 0.02)
        t["e"] = max(t["e"], t["s"] + 0.04)
        t["check"] = bool(t["p"] < 0.35) or t["src"].startswith(("interp", "spread"))
        t["near"] = [o for o in ons if abs(o - t["s"]) <= 0.3] if t["check"] else []
        prev = t["s"]
    out = []
    for n, ln in enumerate(lines):
        out.append({
            "id": f"L{n + 1}",
            "start": round(ln[0]["s"], 2),
            "end": round(ln[-1]["e"], 2),
            "text": " ".join(t["w"] for t in ln),
            "words": [{"w": t["w"], "s": round(t["s"], 2), "e": round(t["e"], 2), "p": t["p"], "src": t["src"], "check": t["check"], **({"near": t["near"]} if t["check"] else {})} for t in ln],
        })
    return out


def write_md(path, track, dur, mf, vf, lines, raw, snd):
    L = [
        "# Транскрипция и тайминги",
        "",
        f"Трек: `{track}`, {dur:.2f} с, {mf['tempoBpm']} BPM (доля {mf['beatSec']} с). Вокал с {vf['start']:.2f} с, "
        f"пик энергии {mf['energyPeak']:.2f} с.",
        "",
        "Паузы в вокале: " + (", ".join(f"{a:.2f}–{b:.2f}" for a, b in vf["gaps"]) or "нет") + ".",
        "",
        "Секции (грубо): " + ", ".join(f"{s['id']} {s['start']:.2f}–{s['end']:.2f}" for s in mf["sections"]) + ".",
        "",
        "## Звучание (грубо, по спектру; жанр угадывает модель, пользователь поправляет)",
        "",
        *[f"- {w}" for w in snd["summary"]],
        "",
        "Цифры: " + ", ".join(f"{k} {v}" for k, v in snd.items() if k not in ("summary", "bands"))
        + "; полосы " + ", ".join(f"{k} {v}" for k, v in snd["bands"].items()) + ".",
        "",
        "## Строки (текст пользователя, времена Whisper + огибающая вокала)",
        "",
        "| # | Начало | Конец | Текст | Слова (начало, с) |",
        "|---|---|---|---|---|",
    ]
    for ln in lines:
        ws = ", ".join(f"{w['w']} {w['s']:.2f}" + ("*" if w["check"] else "") for w in ln["words"])
        L.append(f"| {ln['id']} | {ln['start']:.2f} | {ln['end']:.2f} | {ln['text']} | {ws} |")
    weak = [(ln["id"], w) for ln in lines for w in ln["words"] if w["check"]]
    L += ["", "## Проверить по огибающей вокала", ""]
    if weak:
        L += ["Слова со звёздочкой: низкая уверенность или время восстановлено. Обычно Whisper ставит такое слово "
              "вплотную к концу предыдущего, то есть чуть раньше, чем оно спето. Сверь с ближайшими онсетами вокала "
              "и при нужде поправь `s` в `timing.json`.", ""]
        L += ["| Строка | Слово | Начало | Источник | Уверенность | Онсеты вокала рядом |", "|---|---|---|---|---|---|"]
        L += [f"| {i} | {w['w']} | {w['s']:.2f} | {w['src']} | {w['p']} | {', '.join(f'{o:.2f}' for o in w['near'])} |" for i, w in weak]
    else:
        L.append("Всё совпало уверенно.")
    L += ["", "## Как модель услышала без подсказки", "", " ".join(w["w"] for w in raw), ""]
    Path(path).write_text("\n".join(L), encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--lyrics", required=True, help="UTF-8 text, one sung line per line, repeats written out")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", default="ru", help='Whisper language code, or "auto"')
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    audio, out = Path(a.audio), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    text = Path(a.lyrics).read_text(encoding="utf-8-sig")
    lines = parse_lyrics(text)
    if not lines:
        sys.exit("lyrics file has no words")
    flat = " ".join(t["w"] for ln in lines for t in ln)
    dur = probe_duration(audio)

    voc, inst = separate(audio, out, a.force)
    words, raw = transcribe(voc, out, None if a.lang == "auto" else a.lang, flat, a.force)
    log("audio features ...")
    vf = vocal_features(voc)
    mf = music_features(audio, inst, dur)
    snd = sound_features(audio, voc, inst, mf, dur)
    aligned = align(lines, words, vf)

    timing = {
        "track": str(audio).replace("\\", "/"),
        "duration": round(dur, 3),
        "frames": int(round(dur * a.fps)),
        "fps": a.fps,
        **{k: mf[k] for k in ("tempoBpm", "beatSec", "energyPeak", "sections")},
        "sound": snd,
        "vocalStart": vf["start"],
        "vocalGaps": vf["gaps"],
        "lines": aligned,
        "beats": mf["beats"],
        "kicks": mf["kicks"],
        "onsets": vf["onsets"],
        "energy": mf["energy"],
        "method": "Demucs two-stem -> faster-whisper large-v3 word timestamps (with and without the lyrics prompt) "
                  "-> aligned to the user's lyrics -> corrected with the vocal RMS envelope and onsets.",
    }
    (out / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(out / "TRANSCRIPT.md", str(audio).replace("\\", "/"), dur, mf, vf, aligned, raw, snd)
    log(f"\nduration {dur:.2f} s, {mf['tempoBpm']} BPM, vocals from {vf['start']:.2f} s, gaps {vf['gaps']}")
    log("sound: " + "; ".join(snd["summary"]))
    for ln in aligned:
        log(f"{ln['id']:>4} {ln['start']:6.2f}-{ln['end']:6.2f}  {ln['text']}")
    log(f"\nwrote {out / 'timing.json'} and {out / 'TRANSCRIPT.md'}")


if __name__ == "__main__":
    main()

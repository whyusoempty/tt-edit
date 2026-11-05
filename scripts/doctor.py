#!/usr/bin/env python
"""Check that everything /tt-edit needs is installed. Prints what is missing and how to get it.

    python doctor.py            exit code 0 = ready, 1 = something required is missing
"""
import glob
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

WIN = sys.platform == "win32"


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, shell=WIN)
        return r.returncode, (r.stdout or r.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def blender_path():
    p = shutil.which("blender")
    if p:
        return p
    pats = {
        "win32": [r"C:\Program Files\Blender Foundation\Blender*\blender.exe"],
        "darwin": ["/Applications/Blender.app/Contents/MacOS/Blender"],
    }.get(sys.platform, ["/snap/bin/blender", "/usr/bin/blender", "/opt/blender*/blender"])
    for pat in pats:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bad, rows = False, []

    def row(name, ok, info, fix="", required=True):
        nonlocal bad
        bad |= required and not ok
        rows.append(("OK " if ok else ("NO " if required else "-- ")) + f"{name}: {info}" + ("" if ok or not fix else f"\n     -> {fix}"))

    for tool in ("ffmpeg", "ffprobe", "node", "npx"):
        p = shutil.which(tool)
        row(tool, bool(p), p or "not in PATH",
            "ffmpeg: https://ffmpeg.org/download.html (Windows: winget install Gyan.FFmpeg)" if tool.startswith("ff")
            else "Node.js 20+: https://nodejs.org")

    code, out = run(["npx", "--yes", "hyperframes", "--version"])
    row("hyperframes CLI", code == 0, out.splitlines()[-1] if out else "?", "npm i -g hyperframes  (or it runs via npx)")

    skills = Path.home() / ".claude" / "skills"
    have = [s for s in ("hyperframes", "hyperframes-core", "hyperframes-animation", "hyperframes-cli") if (skills / s).exists()]
    row("HyperFrames skills", len(have) >= 2, ", ".join(have) or "none in ~/.claude/skills",
        "npx hyperframes skills update   then restart Claude Code")

    row("python", sys.version_info >= (3, 9), sys.version.split()[0], "Python 3.9+")
    for mod, pipname in (("numpy", "numpy"), ("librosa", "librosa"), ("soundfile", "soundfile"),
                         ("demucs", "demucs"), ("faster_whisper", "faster-whisper"), ("torch", "torch")):
        ok = importlib.util.find_spec(mod) is not None
        row(f"python: {mod}", ok, "installed" if ok else "missing", f"pip install {pipname}")
    ok = importlib.util.find_spec("PIL") is not None
    row("python: PIL", ok, "installed" if ok else "missing", "pip install pillow  (only for Blender textures)", required=False)

    card = run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])[1] if shutil.which("nvidia-smi") else ""
    cuda = ""
    if importlib.util.find_spec("torch"):
        cuda = run([sys.executable, "-c", "import torch;print(torch.cuda.is_available())"])[1]
    note = "" if cuda == "True" else " (torch without CUDA: Demucs/Whisper run on CPU, slower but fine for short tracks)"
    row("GPU", True, (card or "no NVIDIA GPU found") + note, required=False)

    b = blender_path()
    row("Blender (optional)", bool(b), b or "not found — styles that need Blender will be offered without it",
        "https://www.blender.org/download/", required=False)

    print("\n".join(rows))
    print("\nREADY" if not bad else "\nMISSING REQUIRED PARTS (see -> above)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

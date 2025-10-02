#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, os, subprocess, shutil, sys, math
import os
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)
def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        print(p.stdout)
        raise SystemExit(f"Command failed: {' '.join(cmd)}")
    return p.stdout

def extract_wav(src, wav_path, sr=16000):
    run(["ffmpeg", "-y", "-i", src, "-ac", "1", "-ar", str(sr), "-vn", wav_path])

def has_whisperx():
    try: 
        import whisperx  # noqa
        return True
    except Exception:
        return False

def transcribe_word_timestamps(wav_path, prefer_whisperx=True, device_hint=None):
    """
    Returns list of dicts: [{"text": "...", "start": float, "end": float}, ...]
    """
    words = []
    device = device_hint
    if not device:
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"

    if prefer_whisperx and has_whisperx():
        import whisperx
        print("[i] Using WhisperX")
        asr_model = whisperx.load_model("medium", device)
        result = asr_model.transcribe(wav_path)

        align_model, meta = whisperx.load_align_model(language_code=result["language"], device=device)
        aligned = whisperx.align(result["segments"], align_model, meta, wav_path, device)
        for seg in aligned["segments"]:
            for w in seg.get("words", []):
                t = (w.get("word") or "").strip()
                if t and (w.get("start") is not None) and (w.get("end") is not None):
                    words.append({"text": t, "start": float(w["start"]), "end": float(w["end"])})
    else:
        print("[i] Using faster-whisper")
        from faster_whisper import WhisperModel
        compute_type = "float16" if device == "cuda" else "int8"
        model = WhisperModel("medium", device=device, compute_type=compute_type)
        segments, info = model.transcribe(wav_path, word_timestamps=True, vad_filter=True)
        for seg in segments:
            for w in seg.words:
                t = w.word.strip()
                if t:
                    words.append({"text": t, "start": float(w.start), "end": float(w.end)})

    cleaned = []
    for w in words:
        if any(ch.isalnum() for ch in w["text"]):
            cleaned.append(w)
    return cleaned

def ass_header(font="Vazirmatn", fontsize=64, playres=(1080, 1920), alignment=500):
    w, h = playres
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
LayoutResX: {w}
LayoutResY: {h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{fontsize},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,4,2,{alignment},80,80,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def fmt_ass_ts(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int((t - int(t)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def chunk_words_into_readable_lines(words, max_gap=0.60, max_words=8):
    lines = []
    if not words:
        return lines
    line = {"start": words[0]["start"], "end": words[0]["end"], "words": [words[0]]}
    for i in range(1, len(words)):
        prev = words[i - 1]
        cur = words[i]
        gap = cur["start"] - prev["end"]
        if gap > max_gap or len(line["words"]) >= max_words:
            line["end"] = line["words"][-1]["end"]
            lines.append(line)
            line = {"start": cur["start"], "end": cur["end"], "words": [cur]}
        else:
            line["words"].append(cur)
    line["end"] = line["words"][-1]["end"]
    lines.append(line)
    return lines

def is_rtl_text(text):
    rtl_chars = 0
    total_chars = 0
    
    for char in text:
        if char.isalpha():
            total_chars += 1
            if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F' or '\u0590' <= char <= '\u05FF':
                rtl_chars += 1
    
    if total_chars == 0:
        return False
    
    return rtl_chars / total_chars > 0.5

def make_ass(lines, style="Caption"):
    """
    S17-17 FINAL: Yellow 125% with Strong Outline
    """
    
    def fix_punct(s: str) -> str:
        s = s.replace(".", "").replace(",", "").replace("،", "")
        return s.replace("?", "؟").replace(";", "؛")

    out = []

    for ln in lines:
        words = [w for w in ln["words"] if (w.get("text") or "").strip()]
        if not words:
            continue

        probe = " ".join((w["text"] or "").strip() for w in words)
        rtl = is_rtl_text(probe)

        line_start = float(words[0]["start"])
        line_end = float(words[-1]["end"])

        if not rtl:
            kao_tokens = []
            for w in words:
                t = fix_punct((w["text"] or "").strip())
                if not t: continue
                duration_cs = int((float(w["end"]) - float(w["start"])) * 100)
                seg = r"{\k" + str(duration_cs) + r"\c&H00FFFF&\b1}" + t + r"{\b0\c&HFFFFFF&}"
                kao_tokens.append(seg)
            kao_text = r"{\an2}" + " ".join(kao_tokens)
            out.append(f"Dialogue: 0,{fmt_ass_ts(line_start)},{fmt_ass_ts(line_end)},Caption,,0,0,0,,{kao_text}")
            continue

        n = len(words)
        
        # S17-17 FINAL: Yellow 125% + Strong Outline
        kao_tokens = []
        for i in range(n-1, -1, -1):
            w = words[i]
            t = fix_punct((w["text"] or "").strip())
            if not t: continue
            start_ms = int((float(w["start"]) - line_start) * 1000)
            end_ms = int((float(w["end"]) - line_start) * 1000)
            kao_tokens.append(r"{\t(" + str(start_ms) + "," + str(end_ms) + r",\c&H00FFFF&\3c&H000000&\bord5\b1\fscx125\fscy125)}" + t + r"{\t(" + str(end_ms) + "," + str(end_ms+1) + r",\c&HFFFFFF&\3c&H000000&\bord4\b0\fscx100\fscy100)}")
        out.append(f"Dialogue: 0,{fmt_ass_ts(line_start)},{fmt_ass_ts(line_end)},Caption,,0,0,0,,{{\\an2\\q2}}" + " ".join(kao_tokens))

    return "\n".join(out) + "\n"



def main():
    ap = argparse.ArgumentParser(description="S17-17 Final: RTL Karaoke Subtitle Generator")
    ap.add_argument("--in", dest="inp", required=True, help="Input video/audio file")
    ap.add_argument("--out", dest="out", default="out_ass.mp4", help="Output video")
    ap.add_argument("--ass", dest="ass", default="karaoke.ass", help="ASS output path")
    ap.add_argument("--font", dest="font", default="Vazirmatn", help="Subtitle font")
    ap.add_argument("--fontsize", dest="fontsize", type=int, default=64, help="Font size")
    ap.add_argument("--align", dest="align", type=int, default=3, help="Alignment")
    ap.add_argument("--playres", dest="playres", default="1080x1920", help="PlayResXxY")
    ap.add_argument("--burn", dest="burn", action="store_true", help="Burn subtitles")
    ap.add_argument("--gap", dest="gap", type=float, default=0.60, help="Max gap")
    ap.add_argument("--maxwords", dest="maxwords", type=int, default=8, help="Max words")
    ap.add_argument("--cpu", dest="cpu", action="store_true", help="Force CPU")
    args = ap.parse_args()

    wav_path = os.path.splitext(os.path.basename(args.inp))[0] + ".wav"
    print("[i] Extracting WAV…")
    extract_wav(args.inp, wav_path, sr=16000)

    device_hint = "cpu" if args.cpu else None
    print("[i] Transcribing + word timestamps…")
    words = transcribe_word_timestamps(wav_path, prefer_whisperx=True, device_hint=device_hint)
    if not words:
        raise SystemExit("No words recognized.")

    print("[i] Chunking into readable lines…")
    lines = chunk_words_into_readable_lines(words, max_gap=args.gap, max_words=args.maxwords)

    print("[i] Building ASS…")
    w, h = map(int, args.playres.lower().split("x"))
    header = ass_header(font=args.font, fontsize=args.fontsize, playres=(w, h), alignment=args.align)
    body   = make_ass(lines, style="Caption")
    with open(args.ass, "w", encoding="utf-8") as f:
        f.write(header + body)
    print(f"[✓] Wrote ASS: {args.ass}")

    if args.burn:
        print("[i] Burning subtitles with FFmpeg…")
        run(["ffmpeg", "-y", "-i", args.inp, "-vf", f"ass={args.ass}", "-c:a", "copy", args.out])
        print(f"[✓] Wrote video: {args.out}")

if __name__ == "__main__":
    main()
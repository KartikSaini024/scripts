import os
import subprocess
import sys
from pathlib import Path


# =========================================================
# LANGUAGE OPTIONS
# =========================================================

LANGUAGE_OPTIONS = {
    "1":  ("English",    "en"),
    "2":  ("Hindi",      "hi"),
    "3":  ("Spanish",    "es"),
    "4":  ("French",     "fr"),
    "5":  ("German",     "de"),
    "6":  ("Japanese",   "ja"),
    "7":  ("Korean",     "ko"),
    "8":  ("Russian",    "ru"),
    "9":  ("Arabic",     "ar"),
    "10": ("Portuguese", "pt"),
    "11": ("Italian",    "it"),
    "12": ("Chinese",    "zh-CN"),
    "13": ("Turkish",    "tr"),
    "14": ("Dutch",      "nl"),
    "15": ("Polish",     "pl"),
}

SUBTITLE_SIZE_OPTIONS = {
    "1": ("Small",  16),
    "2": ("Medium", 22),
    "3": ("Large",  28),
}

SUBTITLE_COLOR_OPTIONS = {
    "1": ("White",  "&H00FFFFFF"),
    "2": ("Yellow", "&H00FFFF00"),
    "3": ("Cyan",   "&H00FFFF00"),
    "4": ("Green",  "&H0000FF00"),
}


# =========================================================
# HELPERS
# =========================================================

def hr(char="─", width=70):
    print(char * width)


def section(title: str):
    print()
    hr()
    print(f"  {title}")
    hr()


def ok(msg: str):
    print(f"  ✔  {msg}")


def info(msg: str):
    print(f"  →  {msg}")


def warn(msg: str):
    print(f"  ⚠  {msg}")


def format_timestamp(seconds: float) -> str:
    hours   = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs    = int(seconds % 60)
    millis  = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def create_srt(segments: list, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, start=1):
            start = format_timestamp(seg["start"])
            end   = format_timestamp(seg["end"])
            text  = seg["text"].strip()
            f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")


def escape_path_for_ffmpeg(path: str) -> str:
    """
    FFmpeg's subtitles filter needs:
      - backslashes doubled  (\\ → \\\\)
      - colons escaped       (:  → \\:)
    The value is then wrapped in single quotes inside -vf.
    """
    return path.replace("\\", "\\\\").replace(":", "\\:")


def build_subtitle_style(font_size: int, primary_color: str) -> str:
    """ASS/FFmpeg force_style: centered bottom, thin black outline for readability."""
    return (
        f"FontName=Arial,"
        f"FontSize={font_size},"
        f"Bold=1,"
        f"PrimaryColour={primary_color},"
        f"OutlineColour=&H00000000,"   # solid black outline
        f"BackColour=&H00000000,"
        f"BorderStyle=1,"              # outline + shadow mode (not box)
        f"Outline=1,"                  # 1px thin outline
        f"Shadow=0,"
        f"Alignment=2,"                # center-bottom
        f"MarginV=20"
    )


def burn_subtitles(
    video_path: str,
    srt_path: str,
    output_path: str,
    font_size: int,
    primary_color: str,
) -> None:
    section("Burning subtitles into video")

    escaped  = escape_path_for_ffmpeg(srt_path)
    style    = build_subtitle_style(font_size, primary_color)
    vf_value = f"subtitles='{escaped}':force_style='{style}'"

    cmd = [
        "ffmpeg", "-y",
        "-i",    video_path,
        "-vf",   vf_value,
        # ── Audio: AAC is universally supported on Windows / macOS / mobile ──
        "-c:a",  "aac",
        "-b:a",  "192k",
        # ── Video: re-encode with H.264 baseline for max compatibility ────────
        "-c:v",  "libx264",
        "-preset", "fast",
        "-crf",  "23",
        # ── Container flags for fast start / web playback ─────────────────────
        "-movflags", "+faststart",
        output_path,
    ]

    info("FFmpeg command:\n  " + " ".join(cmd))
    print()
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print()
        warn("FFmpeg exited with an error. Check output above for details.")
        sys.exit(1)


def translate_text(text: str, target_lang: str) -> str:
    from deep_translator import GoogleTranslator
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception as exc:
        warn(f"Translation failed ({exc}), keeping original.")
        return text


def pick_option(prompt: str, options: dict, allow_skip: bool = False) -> str:
    print(f"\n{prompt}\n")
    for key, val in options.items():
        label = val[0] if isinstance(val, tuple) else val
        print(f"    {key:>2}.  {label}")
    if allow_skip:
        print("     0.  Skip / keep default")
    while True:
        choice = input("\n  Choice: ").strip()
        if allow_skip and choice == "0":
            return "0"
        if choice in options:
            return choice
        warn("Invalid choice — please try again.")


# =========================================================
# MAIN
# =========================================================

def main():
    print()
    hr("═")
    print("        Universal Video Subtitle Generator & Translator")
    print("                    powered by faster-whisper")
    hr("═")

    # ── INPUT FILE ─────────────────────────────────────────────────────
    section("Input Video")
    video_path = input("  Enter video file path:\n  > ").strip().strip('"').strip("'")

    if not os.path.exists(video_path):
        warn("File not found. Please check the path and try again.")
        sys.exit(1)

    video_path = str(Path(video_path).resolve())
    ok(f"Found: {video_path}")

    # ── TARGET LANGUAGE ────────────────────────────────────────────────
    section("Output Subtitle Language")
    lang_choice = pick_option(
        "Select the language to translate subtitles INTO:",
        LANGUAGE_OPTIONS,
    )
    target_name, target_code = LANGUAGE_OPTIONS[lang_choice]
    ok(f"Target language: {target_name} ({target_code})")

    # ── SUBTITLE APPEARANCE ────────────────────────────────────────────
    section("Subtitle Appearance")
    size_choice = pick_option("Subtitle size:", SUBTITLE_SIZE_OPTIONS)
    _, font_size = SUBTITLE_SIZE_OPTIONS[size_choice]

    color_choice = pick_option("Subtitle color:", SUBTITLE_COLOR_OPTIONS)
    color_name, primary_color = SUBTITLE_COLOR_OPTIONS[color_choice]
    ok(f"Style: {SUBTITLE_SIZE_OPTIONS[size_choice][0]} / {color_name}")

    # ── WHISPER MODEL ──────────────────────────────────────────────────
    MODEL_OPTIONS = {
        "1": ("small          — fastest, lower accuracy",          "small"),
        "2": ("medium         — balanced speed & accuracy",        "medium"),
        "3": ("large-v3       — best accuracy, slower",            "large-v3"),
        "4": ("large-v3-turbo — fast + excellent  ★ recommended",  "large-v3-turbo"),
    }

    section("Whisper Transcription Model")
    model_choice = pick_option("Select model:", MODEL_OPTIONS)
    model_name   = MODEL_OPTIONS[model_choice][1]
    ok(f"Model: {model_name}")

    # ── GPU DETECTION ──────────────────────────────────────────────────
    section("Hardware")
    try:
        import torch
        if torch.cuda.is_available():
            device, compute_type = "cuda", "float16"
            ok("CUDA GPU detected — using float16")
        else:
            device, compute_type = "cpu", "int8"
            info("No GPU found — using CPU int8")
    except ImportError:
        device, compute_type = "cpu", "int8"
        info("torch not available — using CPU int8")

    # ── OUTPUT PATHS ───────────────────────────────────────────────────
    video_stem   = Path(video_path).stem
    output_dir   = Path(video_path).parent
    srt_path     = str(output_dir / f"{video_stem}.{target_code}.srt")
    output_video = str(output_dir / f"{video_stem}.subtitled.mp4")

    # ── LOAD MODEL & TRANSCRIBE ────────────────────────────────────────
    section("Transcription")
    info(f"Loading Whisper model '{model_name}'…")

    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    info("Transcribing — language will be auto-detected…\n")
    segments_gen, info_obj = model.transcribe(
        video_path,
        beam_size=5,
        best_of=5,
        temperature=0,
        vad_filter=True,
    )

    detected_lang = info_obj.language
    ok(f"Detected language: {detected_lang}")

    # ── TRANSLATE & COLLECT ────────────────────────────────────────────
    same_lang = detected_lang.split("-")[0] == target_code.split("-")[0]

    if same_lang:
        info(f"Source and target both '{target_name}' — skipping translation.\n")
    else:
        info(f"Translating '{detected_lang}' → '{target_name}'…\n")

    collected: list[dict] = []
    for i, seg in enumerate(segments_gen, start=1):
        original   = seg.text.strip()
        translated = original if same_lang else translate_text(original, target_code)

        collected.append({"start": seg.start, "end": seg.end, "text": translated})

        stamp = f"[{seg.start:7.2f}s → {seg.end:7.2f}s]"
        if same_lang:
            print(f"  {stamp}  {translated}")
        else:
            print(f"  {stamp}")
            print(f"    orig : {original}")
            print(f"    sub  : {translated}")
        print()

    if not collected:
        warn("No speech segments found — exiting.")
        sys.exit(1)

    # ── WRITE SRT ──────────────────────────────────────────────────────
    section("Writing SRT")
    create_srt(collected, srt_path)
    ok(f"Saved: {srt_path}")

    # ── BURN SUBTITLES ─────────────────────────────────────────────────
    burn_subtitles(
        video_path,
        srt_path,
        output_video,
        font_size=font_size,
        primary_color=primary_color,
    )

    # ── DONE ───────────────────────────────────────────────────────────
    print()
    hr("═")
    print("  ✔  All done!")
    print(f"     SRT file    →  {srt_path}")
    print(f"     Final video →  {output_video}")
    hr("═")
    print()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()

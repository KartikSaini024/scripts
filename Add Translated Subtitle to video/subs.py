import os
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel


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
    "1": ("White",  "&HFFFFFF"),
    "2": ("Yellow", "&H00FFFF"),
    "3": ("Cyan",   "&HFFFF00"),
    "4": ("Green",  "&H00FF00"),
}


# =========================================================
# HELPERS
# =========================================================

def format_timestamp(seconds):
    hours   = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs    = int(seconds % 60)
    millis  = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def create_srt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, segment in enumerate(segments, start=1):
            start = format_timestamp(segment["start"])
            end   = format_timestamp(segment["end"])
            text  = segment["text"].strip()
            f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")


def escape_path_for_ffmpeg(path: str) -> str:
    """
    FFmpeg's subtitles filter on Windows needs:
      - backslashes doubled  (\ → \\)
      - colons escaped       (: → \\:)
    The whole thing is then wrapped in single quotes inside the -vf string.
    """
    p = path.replace("\\", "\\\\").replace(":", "\\:")
    return p


def build_subtitle_style(font_size: int, primary_color: str) -> str:
    """
    Build an ASS/FFmpeg force_style string that puts subtitles at
    center-bottom with a semi-transparent background box.
    """
    return (
        f"FontName=Arial,"
        f"FontSize={font_size},"
        f"PrimaryColour={primary_color},"
        f"OutlineColour=&H00000000,"
        f"BackColour=&H80000000,"
        f"BorderStyle=3,"          # opaque box
        f"Outline=0,"
        f"Shadow=0,"
        f"Alignment=2,"            # center-bottom
        f"MarginV=20"
    )


def burn_subtitles(video_path: str, srt_path: str, output_path: str,
                   font_size: int, primary_color: str):
    print("\nBurning subtitles into video...\n")

    escaped = escape_path_for_ffmpeg(srt_path)
    style   = build_subtitle_style(font_size, primary_color)

    vf_value = f"subtitles='{escaped}':force_style='{style}'"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", vf_value,
        "-c:a", "copy",
        output_path,
    ]

    print(f"Running: {' '.join(cmd)}\n")
    subprocess.run(cmd, check=True)


def translate_text(text: str, target_lang: str) -> str:
    from deep_translator import GoogleTranslator
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception:
        return text


def pick_option(prompt: str, options: dict, allow_skip=False) -> str:
    print(f"\n{prompt}\n")
    for key, val in options.items():
        label = val[0] if isinstance(val, tuple) else val
        print(f"  {key}. {label}")
    if allow_skip:
        print("  0. Skip / keep default")
    while True:
        choice = input("\nChoice: ").strip()
        if allow_skip and choice == "0":
            return "0"
        if choice in options:
            return choice
        print("  Invalid choice, try again.")


# =========================================================
# MAIN
# =========================================================

def main():
    print("=" * 70)
    print("      Universal Video Subtitle Generator & Translator")
    print("=" * 70)

    # ------------------------------------------------------------------
    # INPUT FILE
    # ------------------------------------------------------------------
    video_path = input("\nEnter video file path:\n> ").strip().strip('"')

    if not os.path.exists(video_path):
        print("\nERROR: File not found.")
        return

    video_path = str(Path(video_path).resolve())

    # ------------------------------------------------------------------
    # TARGET LANGUAGE
    # ------------------------------------------------------------------
    lang_choice = pick_option(
        "Select OUTPUT subtitle language (language to translate INTO):",
        LANGUAGE_OPTIONS
    )
    target_name, target_code = LANGUAGE_OPTIONS[lang_choice]

    # ------------------------------------------------------------------
    # SUBTITLE APPEARANCE
    # ------------------------------------------------------------------
    size_choice = pick_option(
        "Select subtitle size:",
        SUBTITLE_SIZE_OPTIONS
    )
    _, font_size = SUBTITLE_SIZE_OPTIONS[size_choice]

    color_choice = pick_option(
        "Select subtitle color:",
        SUBTITLE_COLOR_OPTIONS
    )
    _, primary_color = SUBTITLE_COLOR_OPTIONS[color_choice]

    # ------------------------------------------------------------------
    # WHISPER MODEL
    # ------------------------------------------------------------------
    MODEL_OPTIONS = {
        "1": ("small         – fastest, lower accuracy",    "small"),
        "2": ("medium        – balanced",                   "medium"),
        "3": ("large-v3      – best accuracy, slow",        "large-v3"),
        "4": ("large-v3-turbo– fast + excellent (recommended)", "large-v3-turbo"),
    }

    model_choice = pick_option("Select Whisper transcription model:", MODEL_OPTIONS)
    model_name   = MODEL_OPTIONS[model_choice][1]

    # ------------------------------------------------------------------
    # GPU DETECTION
    # ------------------------------------------------------------------
    try:
        import torch
        if torch.cuda.is_available():
            device, compute_type = "cuda", "float16"
            print("\n[GPU detected – using CUDA float16]")
        else:
            device, compute_type = "cpu", "int8"
            print("\n[No GPU – using CPU int8]")
    except Exception:
        device, compute_type = "cpu", "int8"
        print("\n[torch not available – using CPU int8]")

    # ------------------------------------------------------------------
    # OUTPUT PATHS
    # ------------------------------------------------------------------
    video_name = Path(video_path).stem
    output_dir = Path(video_path).parent

    srt_path     = str(output_dir / f"{video_name}.{target_code}.srt")
    output_video = str(output_dir / f"{video_name}.subtitled.mp4")

    # ------------------------------------------------------------------
    # LOAD MODEL & TRANSCRIBE
    # ------------------------------------------------------------------
    print(f"\nLoading Whisper model '{model_name}'…\n")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    print("Transcribing — language will be detected automatically…\n")
    segments_gen, info = model.transcribe(
        video_path,
        beam_size=5,
        best_of=5,
        temperature=0,
        vad_filter=True,
    )

    detected_lang = info.language
    print(f"Detected language: {detected_lang}")

    # ------------------------------------------------------------------
    # TRANSLATE
    # ------------------------------------------------------------------
    same_lang = (detected_lang == target_code)
    if same_lang:
        print(f"\nSource and target language are both '{target_name}' – skipping translation.\n")
    else:
        print(f"\nTranslating from '{detected_lang}' → '{target_name}'…\n")

    collected = []
    for i, seg in enumerate(segments_gen, start=1):
        original = seg.text.strip()

        if same_lang:
            translated = original
        else:
            translated = translate_text(original, target_code)

        collected.append({"start": seg.start, "end": seg.end, "text": translated})

        print(f"[{seg.start:.2f}s → {seg.end:.2f}s]")
        if not same_lang:
            print(f"  ORIGINAL:   {original}")
        print(f"  SUBTITLE:   {translated}")
        print("-" * 50)

    # ------------------------------------------------------------------
    # WRITE SRT
    # ------------------------------------------------------------------
    print(f"\nWriting SRT → {srt_path}")
    create_srt(collected, srt_path)

    # ------------------------------------------------------------------
    # BURN SUBTITLES
    # ------------------------------------------------------------------
    burn_subtitles(
        video_path,
        srt_path,
        output_video,
        font_size=font_size,
        primary_color=primary_color,
    )

    print("\n" + "=" * 70)
    print("  Done!")
    print(f"  SRT file   : {srt_path}")
    print(f"  Final video: {output_video}")
    print("=" * 70)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()

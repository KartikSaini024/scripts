# =========================================================
# UNIVERSAL VIDEO SUBTITLE GENERATOR + TRANSLATOR
# =========================================================
# FEATURES
# ---------------------------------------------------------
# ✔ Auto language detection
# ✔ Whisper transcription
# ✔ Automatic translation
# ✔ Manual translation mode
# ✔ Optional original subtitles at TOP CENTER
# ✔ Burn subtitles into video
# ✔ Live transcript preview
# ✔ Transcript txt export
# ✔ Model name in output filename
# ✔ Retry handling for Google rate limits
#
# REQUIREMENTS
# ---------------------------------------------------------
# pip install faster-whisper deep-translator torch
#
# FFmpeg must be installed and available in PATH
# =========================================================

import os
import subprocess
import sys
import time

from pathlib import Path

# =========================================================
# LANGUAGES
# =========================================================

LANGUAGE_OPTIONS = {
    "1": ("English", "en"),
    "2": ("Hindi", "hi"),
    "3": ("Spanish", "es"),
    "4": ("French", "fr"),
    "5": ("German", "de"),
    "6": ("Japanese", "ja"),
    "7": ("Korean", "ko"),
    "8": ("Russian", "ru"),
    "9": ("Arabic", "ar"),
    "10": ("Portuguese", "pt"),
    "11": ("Italian", "it"),
    "12": ("Chinese", "zh-CN"),
    "13": ("Turkish", "tr"),
    "14": ("Dutch", "nl"),
    "15": ("Polish", "pl"),
}

# =========================================================
# SUBTITLE STYLE
# =========================================================

SUBTITLE_SIZE_OPTIONS = {
    "1": ("Small", 16),
    "2": ("Medium", 22),
    "3": ("Large", 28),
}

SUBTITLE_COLOR_OPTIONS = {
    "1": ("White", "&H00FFFFFF"),
    "2": ("Yellow", "&H0000FFFF"),
    "3": ("Cyan", "&H00FFFF00"),
    "4": ("Green", "&H0000FF00"),
}

# =========================================================
# MODELS
# =========================================================

MODEL_OPTIONS = {
    "1": ("large-v3-turbo ★ recommended", "large-v3-turbo"),
    "2": ("large-v3", "large-v3"),
    "3": ("medium", "medium"),
    "4": ("small", "small"),
}

# =========================================================
# HELPERS
# =========================================================

def hr(char="─", width=70):
    print(char * width)

def section(title):
    print()
    hr()
    print(" " + title)
    hr()

def ok(msg):
    print(f"✔ {msg}")

def info(msg):
    print(f"→ {msg}")

def warn(msg):
    print(f"⚠ {msg}")

# =========================================================
# TIMESTAMP
# =========================================================

def format_timestamp(seconds):

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    millis = int((seconds - int(seconds)) * 1000)

    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

# =========================================================
# SRT WRITER
# =========================================================

def create_srt(segments, output_path):

    with open(output_path, "w", encoding="utf-8") as f:

        for idx, seg in enumerate(segments, start=1):

            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])

            text = seg["text"].strip()

            f.write(
                f"{idx}\n"
                f"{start} --> {end}\n"
                f"{text}\n\n"
            )

# =========================================================
# MENU
# =========================================================

def pick_option(prompt, options):

    print()
    print(prompt)

    for k, v in options.items():
        print(f"{k}. {v[0]}")

    while True:

        choice = input("\nChoice: ").strip()

        if choice in options:
            return choice

        warn("Invalid choice")

def yes_no(prompt):

    while True:

        val = input(f"{prompt} (y/n): ").strip().lower()

        if val in ["y", "yes"]:
            return True

        if val in ["n", "no"]:
            return False

        warn("Please enter y or n")

# =========================================================
# FFMPEG
# =========================================================

def escape_path_for_ffmpeg(path):

    path = os.path.abspath(path)

    path = path.replace("\\", "/")
    path = path.replace(":", "\\:")
    path = path.replace("'", "\\'")

    return path

def build_subtitle_style(
    font_size,
    primary_color,
    alignment,
    margin_v,
):

    return (
        f"FontName=Arial,"
        f"FontSize={font_size},"
        f"Bold=1,"
        f"PrimaryColour={primary_color},"
        f"OutlineColour=&H00000000,"
        f"BorderStyle=1,"
        f"Outline=1,"
        f"Shadow=0,"
        f"Alignment={alignment},"
        f"MarginV={margin_v},"
        f"MarginL=20,"
        f"MarginR=20"
    )

def burn_subtitles(
    video_path,
    translated_srt,
    original_srt,
    output_path,
    font_size,
    primary_color,
    burn_original_top,
):

    section("Burning subtitles")

    filters = []

    # translated subs (bottom center)

    translated_style = build_subtitle_style(
        font_size,
        primary_color,
        alignment=2,
        margin_v=20,
    )

    translated_escaped = escape_path_for_ffmpeg(
        translated_srt
    )

    filters.append(
        f"subtitles='{translated_escaped}':"
        f"force_style='{translated_style}'"
    )

    # original subs (top center)

    if burn_original_top and original_srt:

        original_style = build_subtitle_style(
            int(font_size * 0.85),
            "&H00FFFFFF",
            alignment=8,
            margin_v=40,
        )

        original_escaped = escape_path_for_ffmpeg(
            original_srt
        )

        filters.append(
            f"subtitles='{original_escaped}':"
            f"force_style='{original_style}'"
        )

    vf = ",".join(filters)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        output_path,
    ]

    print()
    info("Running ffmpeg...\n")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        warn("FFmpeg failed")
        sys.exit(1)

# =========================================================
# VIDEO HELPERS
# =========================================================

def get_video_duration(video_path):

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    try:

        out = subprocess.check_output(
            cmd
        ).decode().strip()

        return float(out)

    except:
        return 0

def extract_audio_chunk(
    video_path,
    start,
    duration,
    out_path,
):

    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-ss",
        str(start),
        "-t",
        str(duration),
        "-i",
        video_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        out_path,
    ]

    result = subprocess.run(cmd)

    return result.returncode == 0

# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language_robust(
    model,
    video_path,
    num_probes=5,
    probe_duration=20,
):

    import tempfile

    duration = get_video_duration(video_path)

    if duration <= probe_duration:

        _, info_obj = model.transcribe(
            video_path,
            beam_size=1,
            language=None,
        )

        return info_obj.language, 1.0

    margin = duration * 0.05

    usable = duration - (margin * 2)

    step = usable / num_probes

    starts = [
        margin + i * step
        for i in range(num_probes)
    ]

    votes = []

    with tempfile.TemporaryDirectory() as tmpdir:

        for idx, start in enumerate(starts, start=1):

            chunk = os.path.join(
                tmpdir,
                f"probe_{idx}.wav"
            )

            if not extract_audio_chunk(
                video_path,
                start,
                probe_duration,
                chunk,
            ):
                continue

            try:

                _, info_obj = model.transcribe(
                    chunk,
                    beam_size=1,
                    language=None,
                )

                lang = info_obj.language
                prob = info_obj.language_probability

                votes.append((lang, prob))

                print(
                    f"Probe {idx}: "
                    f"{lang} "
                    f"({prob:.0%})"
                )

            except Exception as e:
                warn(str(e))

    if not votes:

        _, info_obj = model.transcribe(
            video_path,
            beam_size=1,
            language=None,
        )

        return info_obj.language, 0.0

    weights = {}

    for lang, prob in votes:
        weights[lang] = weights.get(lang, 0) + prob

    winner = max(weights, key=weights.get)

    confidence = (
        sum(1 for l, _ in votes if l == winner)
        / len(votes)
    )

    return winner, confidence

# =========================================================
# TRANSLATION
# =========================================================

_LANG_CODE_MAP = {
    "zh": "zh-CN",
}

def normalize_lang(code):

    return _LANG_CODE_MAP.get(
        code.lower(),
        code
    )

def chunk_list(lst, size):

    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def translate_batch(texts, target_lang):

    from deep_translator import GoogleTranslator

    target_lang = normalize_lang(target_lang)

    translated = []

    SEP = "|||SEP|||"

    batches = list(chunk_list(texts, 15))

    total = len(batches)

    for batch_idx, batch in enumerate(
        batches,
        start=1
    ):

        print()
        info(f"Batch {batch_idx}/{total}")

        joined = f" {SEP} ".join(batch)

        try:

            result = GoogleTranslator(
                source="auto",
                target=target_lang,
            ).translate(joined)

            parts = result.split(SEP)

            if len(parts) != len(batch):
                raise Exception("Separator mismatch")

            batch_failed = False

            for orig, trans in zip(batch, parts):

                orig_clean = orig.strip()
                trans_clean = trans.strip()

                if (
                    not trans_clean
                    or trans_clean == orig_clean
                ):
                    batch_failed = True
                    break

            if not batch_failed:

                translated.extend(
                    [p.strip() for p in parts]
                )

                continue

            warn("Batch appears rate-limited")

        except Exception as e:

            warn(f"Batch failed: {e}")

        # fallback line-by-line

        for idx, text in enumerate(batch, start=1):

            success = False

            orig_clean = text.strip()

            for attempt in range(5):

                try:

                    translated_text = GoogleTranslator(
                        source="auto",
                        target=target_lang,
                    ).translate(orig_clean)

                    translated_clean = (
                        translated_text.strip()
                        if translated_text
                        else ""
                    )

                    failed = (
                        not translated_clean
                        or translated_clean == orig_clean
                    )

                    if failed:

                        wait_time = (
                            2 + (attempt * 2)
                        )

                        warn(
                            f"Retry {attempt+1}/5 "
                            f"(waiting {wait_time}s)"
                        )

                        time.sleep(wait_time)

                        continue

                    translated.append(
                        translated_clean
                    )

                    print()
                    print(f"[{idx}/{len(batch)}]")

                    print(
                        "ORIG:",
                        orig_clean
                    )

                    print(
                        "TRAN:",
                        translated_clean
                    )

                    success = True

                    break

                except Exception as ex:

                    wait_time = (
                        2 + (attempt * 2)
                    )

                    warn(str(ex))

                    warn(
                        f"Retrying in "
                        f"{wait_time}s..."
                    )

                    time.sleep(wait_time)

            if not success:

                warn(
                    "Failed after retries. "
                    "Keeping original."
                )

                translated.append(orig_clean)

            time.sleep(0.5)

    return translated

# =========================================================
# MANUAL TRANSLATION MODE
# =========================================================

def manual_translation_workflow(
    raw_segments,
    transcript_path,
):

    section("Manual Translation Mode")

    original_lines = [
        seg["text"].strip()
        for seg in raw_segments
    ]

    with open(
        transcript_path,
        "w",
        encoding="utf-8"
    ) as f:

        for line in original_lines:
            f.write(line + "\n")

    ok(f"Transcript saved:\n{transcript_path}")

    print()
    hr()

    print(
        "COPY EVERYTHING BELOW INTO GOOGLE TRANSLATE"
    )

    hr()
    print()

    for line in original_lines:
        print(line)

    print()
    hr()

    print("AFTER TRANSLATING:")
    print("1. Copy translated text")
    print("2. Paste below")
    print("3. Type END on its own line")

    hr()
    print()

    translated_lines = []

    while True:

        line = input()

        if line.strip() == "END":
            break

        translated_lines.append(line)

    if len(translated_lines) != len(raw_segments):

        warn(
            f"Line count mismatch\n"
            f"Expected: {len(raw_segments)}\n"
            f"Received: {len(translated_lines)}"
        )

        sys.exit(1)

    ok("Manual translation received")

    return translated_lines

# =========================================================
# MAIN
# =========================================================

def main():

    print()
    hr("═")

    print("Universal Subtitle Generator")

    hr("═")

    # =====================================================
    # INPUT
    # =====================================================

    section("Input Video")

    video_path = input(
        "Video path:\n> "
    ).strip('"').strip("'")

    if not os.path.exists(video_path):

        warn("File not found")
        sys.exit(1)

    video_path = str(
        Path(video_path).resolve()
    )

    ok(video_path)

    # =====================================================
    # TARGET LANGUAGE
    # =====================================================

    section("Target Language")

    lang_choice = pick_option(
        "Translate subtitles INTO:",
        LANGUAGE_OPTIONS
    )

    target_name, target_code = (
        LANGUAGE_OPTIONS[lang_choice]
    )

    ok(f"{target_name} ({target_code})")

    # =====================================================
    # TRANSLATION MODE
    # =====================================================

    section("Translation Mode")

    TRANSLATION_MODE_OPTIONS = {
        "1": (
            "Automatic Google Translate",
            "auto"
        ),
        "2": (
            "Manual paste-in translation",
            "manual"
        ),
    }

    translation_mode_choice = pick_option(
        "Choose translation mode:",
        TRANSLATION_MODE_OPTIONS
    )

    translation_mode = (
        TRANSLATION_MODE_OPTIONS[
            translation_mode_choice
        ][1]
    )

    ok(f"Mode: {translation_mode}")

    # =====================================================
    # BILINGUAL SUBS
    # =====================================================

    section("Bilingual Subtitles")

    burn_original_top = yes_no(
        "Also burn ORIGINAL subtitles at TOP CENTER?"
    )

    # =====================================================
    # APPEARANCE
    # =====================================================

    section("Subtitle Appearance")

    size_choice = pick_option(
        "Subtitle size:",
        SUBTITLE_SIZE_OPTIONS
    )

    _, font_size = SUBTITLE_SIZE_OPTIONS[
        size_choice
    ]

    color_choice = pick_option(
        "Subtitle color:",
        SUBTITLE_COLOR_OPTIONS
    )

    color_name, primary_color = (
        SUBTITLE_COLOR_OPTIONS[color_choice]
    )

    ok(color_name)

    # =====================================================
    # MODEL
    # =====================================================

    section("Whisper Model")

    model_choice = pick_option(
        "Select model:",
        MODEL_OPTIONS
    )

    model_name = MODEL_OPTIONS[
        model_choice
    ][1]

    ok(model_name)

    # =====================================================
    # HARDWARE
    # =====================================================

    section("Hardware")

    try:

        import torch

        if torch.cuda.is_available():

            device = "cuda"
            compute_type = "float16"

            ok("CUDA detected")

        else:

            device = "cpu"
            compute_type = "int8"

            warn("Using CPU")

    except:

        device = "cpu"
        compute_type = "int8"

    # =====================================================
    # LOAD MODEL
    # =====================================================

    section("Loading Model")

    from faster_whisper import WhisperModel

    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
    )

    ok("Model loaded")

    # =====================================================
    # LANGUAGE DETECTION
    # =====================================================

    section("Language Detection")

    detected_lang, confidence = (
        detect_language_robust(
            model,
            video_path,
        )
    )

    ok(
        f"Detected: "
        f"{detected_lang} "
        f"({confidence:.0%})"
    )

    # =====================================================
    # TRANSCRIBE
    # =====================================================

    section("Transcribing")

    segments_gen, _ = model.transcribe(
        video_path,
        beam_size=5,
        vad_filter=True,
        language=detected_lang,
    )

    raw_segments = []

    for seg in segments_gen:

        text = seg.text.strip()

        raw_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": text,
        })

        print(
            f"[{seg.start:7.2f}s → "
            f"{seg.end:7.2f}s]"
        )

        print("TEXT:", text)
        print()

    if not raw_segments:

        warn("No speech found")
        sys.exit(1)

    # =====================================================
    # OUTPUT PATHS
    # =====================================================

    output_dir = Path(video_path).parent

    stem = Path(video_path).stem

    model_safe = model_name.replace("/", "-")

    transcript_txt = str(
        output_dir /
        f"{stem}.{model_safe}.transcript.txt"
    )

    translated_srt = str(
        output_dir /
        f"{stem}.{model_safe}.{target_code}.srt"
    )

    original_srt = str(
        output_dir /
        f"{stem}.{model_safe}.original.srt"
    )

    output_video = str(
        output_dir /
        f"{stem}.{model_safe}.subtitled.mp4"
    )

    # =====================================================
    # TRANSLATION
    # =====================================================

    same_lang = (
        normalize_lang(detected_lang).split("-")[0]
        ==
        normalize_lang(target_code).split("-")[0]
    )

    if same_lang:

        translated_texts = [
            s["text"]
            for s in raw_segments
        ]

    else:

        if translation_mode == "auto":

            section("Translating")

            translated_texts = translate_batch(
                [s["text"] for s in raw_segments],
                target_code,
            )

        else:

            translated_texts = (
                manual_translation_workflow(
                    raw_segments,
                    transcript_txt,
                )
            )

    # =====================================================
    # FINAL SEGMENTS
    # =====================================================

    translated_segments = []
    original_segments = []

    section("Final Preview")

    for raw, translated in zip(
        raw_segments,
        translated_texts,
    ):

        translated_segments.append({
            "start": raw["start"],
            "end": raw["end"],
            "text": translated,
        })

        original_segments.append({
            "start": raw["start"],
            "end": raw["end"],
            "text": raw["text"],
        })

        print(
            f"[{raw['start']:7.2f}s → "
            f"{raw['end']:7.2f}s]"
        )

        print("ORIG:", raw["text"])
        print("SUB :", translated)

        print()

    # =====================================================
    # WRITE SRT
    # =====================================================

    section("Writing SRT")

    create_srt(
        translated_segments,
        translated_srt,
    )

    create_srt(
        original_segments,
        original_srt,
    )

    ok(translated_srt)

    # =====================================================
    # BURN SUBTITLES
    # =====================================================

    burn_subtitles(
        video_path,
        translated_srt,
        original_srt,
        output_video,
        font_size,
        primary_color,
        burn_original_top,
    )

    # =====================================================
    # DONE
    # =====================================================

    print()
    hr("═")

    print("DONE")

    print("Transcript TXT:", transcript_txt)
    print("Translated SRT:", translated_srt)
    print("Original SRT  :", original_srt)
    print("Video         :", output_video)

    hr("═")

# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":
    main()

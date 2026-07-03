#!/usr/bin/env python3
"""Record promo.html and export neudb-launch-15s.mp4."""

import shutil
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
PROMO = DIR / "promo.html"
RAW_WEBM = DIR / "raw.webm"
OUTPUT_MP4 = DIR / "neudb-launch-15s.mp4"
DURATION_MS = 15_000
VIEWPORT = {"width": 1920, "height": 1080}


def run_playwright_record():
    from playwright.sync_api import sync_playwright

    if RAW_WEBM.exists():
        RAW_WEBM.unlink()

    promo_url = PROMO.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(DIR),
            record_video_size=VIEWPORT,
        )
        page = context.new_page()
        page.goto(promo_url, wait_until="networkidle")
        page.wait_for_timeout(DURATION_MS + 500)
        video = page.video
        page.close()
        context.close()
        browser.close()
        if video:
            saved = video.path()
            if saved and Path(saved).exists():
                shutil.move(saved, RAW_WEBM)


def run_ffmpeg_fallback():
    """Slideshow fallback when Playwright is unavailable."""
    logo = DIR.parent / "brand" / "logo-mark.jpg"
    if not logo.exists():
        raise FileNotFoundError(f"Logo not found: {logo}")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "4", "-i", str(logo),
        "-f", "lavfi", "-t", "4", "-i", "color=c=black:s=1920x1080",
        "-f", "lavfi", "-t", "4", "-i", "color=c=black:s=1920x1080",
        "-f", "lavfi", "-t", "3", "-i", "color=c=black:s=1920x1080",
        "-filter_complex",
        (
            "[1]drawtext=text='Your AI forgets every chat.':fontsize=48:fontcolor=white@0.5:"
            "x=(w-text_w)/2:y=(h-text_h)/2-40[v1];"
            "[2]drawtext=text='neuDB remembers.':fontsize=64:fontcolor=white:"
            "x=(w-text_w)/2:y=(h-text_h)/2[v2];"
            "[3]drawtext=text='pip install neudb':fontsize=44:fontcolor=white:"
            "x=(w-text_w)/2:y=(h-text_h)/2[v3];"
            "[0]scale=400:-1,format=rgba,colorchannelmixer=aa=1.0[logo];"
            "[1][logo]overlay=(W-w)/2:(H-h)/2-80:shortest=1[logo1];"
            f"[logo1][v1]xfade=transition=fade:duration=0.5:offset=3.5[s1];"
            f"[s1][v2]xfade=transition=fade:duration=0.5:offset=7.5[s2];"
            f"[s2][v3]xfade=transition=fade:duration=0.5:offset=11.5[out]"
        ),
        "-map", "[out]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-t", "15",
        str(OUTPUT_MP4),
    ]
    subprocess.run(cmd, check=True)


def export_mp4():
    if not RAW_WEBM.exists():
        raise FileNotFoundError(f"Missing recording: {RAW_WEBM}")

    duration_s = DURATION_MS / 1000
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(RAW_WEBM),
            "-t", str(duration_s),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-movflags", "+faststart",
            str(OUTPUT_MP4),
        ],
        check=True,
    )


def verify():
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=width,height",
            "-of", "default=noprint_wrappers=1",
            str(OUTPUT_MP4),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    print(result.stdout)
    size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
    print(f"Output: {OUTPUT_MP4} ({size_mb:.2f} MB)")


def main():
    try:
        run_playwright_record()
        export_mp4()
    except ImportError:
        print("Playwright not installed — using ffmpeg fallback.", file=sys.stderr)
        run_ffmpeg_fallback()
    except Exception as exc:
        print(f"Playwright failed ({exc}) — using ffmpeg fallback.", file=sys.stderr)
        run_ffmpeg_fallback()

    verify()
    print("Done.")


if __name__ == "__main__":
    main()
"""Render lightweight YouTube Shorts from a still image.

The YouTube publisher accepts MP4 uploads only. This renderer provides a
deterministic fallback for AI/image creatives while keeping user-supplied MP4
files untouched. It intentionally uses ffmpeg as a local, bounded process so
no media is sent to another provider.
"""

from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path

from app.core.exceptions import ExternalServiceException


class YouTubeVideoRenderer:
    """Create a valid vertical MP4 from an image for YouTube Shorts."""

    width = 1080
    height = 1920
    duration_seconds = 12
    frame_rate = 30

    async def render_from_bytes(self, image: bytes, *, extension: str = ".jpg") -> bytes:
        if not image:
            raise ExternalServiceException(message="YouTube video rendering requires a non-empty image")
        if len(image) > 50 * 1024 * 1024:
            raise ExternalServiceException(message="The source image exceeds the 50 MB limit")
        return await asyncio.to_thread(self._render_sync, image, extension)

    @classmethod
    def _render_sync(cls, image: bytes, extension: str) -> bytes:
        safe_extension = extension if extension in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
        with tempfile.TemporaryDirectory(prefix="winsta-youtube-") as directory:
            root = Path(directory)
            source = root / f"source{safe_extension}"
            output = root / "short.mp4"
            source.write_bytes(image)
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-y",
                "-loop",
                "1",
                "-framerate",
                str(cls.frame_rate),
                "-i",
                str(source),
                "-f",
                "lavfi",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t",
                str(cls.duration_seconds),
                "-vf",
                f"scale={cls.width}:{cls.height}:force_original_aspect_ratio=increase,"
                f"crop={cls.width}:{cls.height},format=yuv420p",
                "-r",
                str(cls.frame_rate),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(output),
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, timeout=90)
            except FileNotFoundError as exc:
                raise ExternalServiceException(
                    message="YouTube video rendering is unavailable because ffmpeg is not installed"
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise ExternalServiceException(message="YouTube video rendering timed out") from exc
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or b"").decode("utf-8", errors="replace")[-300:]
                raise ExternalServiceException(
                    message=f"YouTube video rendering failed: {detail or 'ffmpeg error'}"
                ) from exc
            if not output.exists() or output.stat().st_size == 0:
                raise ExternalServiceException(message="YouTube video renderer produced no MP4 output")
            content = output.read_bytes()
            if len(content) > 50 * 1024 * 1024:
                raise ExternalServiceException(message="Rendered YouTube video exceeds the 50 MB limit")
            return content


youtube_video_renderer = YouTubeVideoRenderer()

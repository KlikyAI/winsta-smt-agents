from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.exceptions import ExternalServiceException
from app.modules.social_media.services.youtube_video import youtube_video_renderer


@pytest.mark.asyncio
async def test_youtube_renderer_returns_mp4_bytes() -> None:
    def fake_ffmpeg(command: list[str], **_: object) -> None:
        Path(command[-1]).write_bytes(b"\x00\x00\x00\x18ftypmp42")

    with patch("app.modules.social_media.services.youtube_video.subprocess.run", side_effect=fake_ffmpeg) as run:
        result = await youtube_video_renderer.render_from_bytes(b"image-bytes", extension=".png")

    assert result[4:8] == b"ftyp"
    command = run.call_args.args[0]
    assert "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p" in command
    assert "-t" in command
    assert str(youtube_video_renderer.duration_seconds) in command


@pytest.mark.asyncio
async def test_youtube_renderer_rejects_empty_image() -> None:
    with pytest.raises(ExternalServiceException, match="non-empty image"):
        await youtube_video_renderer.render_from_bytes(b"")

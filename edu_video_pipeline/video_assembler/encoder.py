"""
video_assembler/encoder.py

Robust video encoder for the educational video pipeline.

Key features:
- Safe, explicit detection of MoviePy and FFmpeg (via imageio-ffmpeg shim or system PATH)
- Consistent output resolution & FPS across all clips to avoid concat errors
- Helpful, user-facing error messages with actionable next steps
- Graceful resource cleanup for all MoviePy clip objects
- Duration handling: derives from frame count if not explicitly provided
- Optional metadata hook (no-op by default, ready for ffmpeg tagging in future)

Dependencies expected:
    pip install "moviepy<2" imageio-ffmpeg pydub

System:
    sudo apt-get update && sudo apt-get install -y ffmpeg   (optional if shim is used)
"""

from __future__ import annotations

import os
import logging
import tempfile
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Iterable

# -----------------------------------------------------------------------------
# Robust import & FFmpeg detection
# -----------------------------------------------------------------------------
def _ensure_ffmpeg_env() -> Optional[str]:
    """
    Try to locate an ffmpeg binary and set IMAGEIO_FFMPEG_EXE if available.

    Returns:
        The resolved ffmpeg executable path if found; otherwise None.
    """
    # 1) Prefer imageio-ffmpeg shim if present
    try:
        import imageio_ffmpeg  # type: ignore
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            os.environ.setdefault("IMAGEIO_FFMPEG_EXE", ffmpeg_path)
            return ffmpeg_path
    except Exception:
        pass

    # 2) Fall back to system ffmpeg on PATH
    #    We avoid shutil.which to keep imports minimal.
    candidate = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    try:
        # This will raise if not found.
        subprocess.run([candidate, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return candidate
    except Exception:
        return None


_ffmpeg_resolved = _ensure_ffmpeg_env()

try:
    from moviepy.editor import (
        ImageSequenceClip,
        AudioFileClip,
        concatenate_videoclips,
        CompositeAudioClip,  # kept for future use if you add multiple audios per element
    )
except Exception as e:
    raise RuntimeError(
        "MoviePy import failed.\n"
        "Fix by running:\n"
        "  pip install 'moviepy<2' imageio-ffmpeg\n"
        "Also ensure there is no local folder/file named 'moviepy' that shadows the package."
    ) from e

# Optional: validate ffmpeg availability early with a friendly hint
if not _ffmpeg_resolved:
    # We do NOT fail fast here—MoviePy + imageio may still download a binary at runtime.
    # But we log a clear warning so users know how to fix it.
    pass

logger = logging.getLogger("edu_video_pipeline")


# -----------------------------------------------------------------------------
# Errors
# -----------------------------------------------------------------------------
class VideoEncodingError(RuntimeError):
    """Raised for fatal errors during video encoding."""


# -----------------------------------------------------------------------------
# Encoder
# -----------------------------------------------------------------------------
@dataclass
class _OutputSettings:
    resolution: Tuple[int, int]
    fps: int
    fmt: str
    vcodec: str
    acodec: str
    abr: str
    vbr: str
    threads: int
    preset: str


class VideoEncoder:
    """
    Encoder for creating the final educational video.

    Expected composition structure (example):
    composition = {
        "elements": [
            {
                "duration": 5.2,  # optional; if absent, derived from frames/fps
                "animation": {
                    "frame_paths": [".../frame_0001.png", ".../frame_0002.png", ...]
                },
                "audio": {
                    "path": ".../narration_segment_01.wav"
                }
            },
            ...
        ],
        "meta": {...}  # optional, used by add_metadata (no-op by default)
    }
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: configuration mapping; expected keys (with example defaults):
                - OUTPUT_RESOLUTION: (1920, 1080)
                - OUTPUT_FPS: 30
                - OUTPUT_FORMAT: "mp4"
                - LOG_LEVEL, LOG_FILE, TEMP_DIR, etc. (handled elsewhere)
        """
        self.config = config
        self.output_resolution: Tuple[int, int] = tuple(self._coerce_res(config.get("OUTPUT_RESOLUTION", (1920, 1080))))
        self.fps: int = int(config.get("OUTPUT_FPS", 30))
        self.output_format: str = str(config.get("OUTPUT_FORMAT", "mp4"))

        # Optional tunables
        self._threads: int = int(config.get("ENCODER_THREADS", 4))
        self._preset: str = str(config.get("ENCODER_PRESET", "medium"))
        self._video_bitrate: str = str(config.get("VIDEO_BITRATE", "5000k"))
        self._audio_bitrate: str = str(config.get("AUDIO_BITRATE", "192k"))
        self._video_codec: str = str(config.get("VIDEO_CODEC", "libx264"))
        self._audio_codec: str = str(config.get("AUDIO_CODEC", "aac"))

        # Helpful log about FFmpeg
        if _ffmpeg_resolved:
            logger.info(f"FFmpeg resolved at: {_ffmpeg_resolved}")
        else:
            logger.warning(
                "FFmpeg not found on PATH and imageio-ffmpeg shim was not resolved. "
                "MoviePy may try to fetch a binary at runtime. "
                "If encoding fails, install FFmpeg:\n"
                "  sudo apt-get update && sudo apt-get install -y ffmpeg"
            )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def configure_output_settings(self, overrides: Optional[Dict[str, Any]] = None) -> _OutputSettings:
        """
        Compute encoder settings with optional overrides.

        Returns:
            _OutputSettings dataclass with all encoding params.
        """
        resolution = self.output_resolution
        fps = self.fps
        fmt = self.output_format
        vcodec = self._video_codec
        acodec = self._audio_codec
        abr = self._audio_bitrate
        vbr = self._video_bitrate
        threads = self._threads
        preset = self._preset

        if overrides:
            resolution = tuple(self._coerce_res(overrides.get("resolution", resolution)))  # type: ignore
            fps = int(overrides.get("fps", fps))
            fmt = str(overrides.get("format", fmt))
            vcodec = str(overrides.get("codec", vcodec))
            acodec = str(overrides.get("audio_codec", acodec))
            abr = str(overrides.get("audio_bitrate", abr))
            vbr = str(overrides.get("video_bitrate", vbr))
            threads = int(overrides.get("threads", threads))
            preset = str(overrides.get("preset", preset))

        settings = _OutputSettings(
            resolution=resolution,
            fps=fps,
            fmt=fmt,
            vcodec=vcodec,
            acodec=acodec,
            abr=abr,
            vbr=vbr,
            threads=threads,
            preset=preset,
        )

        logger.info(
            "Output settings -> "
            f"res={settings.resolution}, fps={settings.fps}, fmt={settings.fmt}, "
            f"vcodec={settings.vcodec}, acodec={settings.acodec}, "
            f"vbr={settings.vbr}, abr={settings.abr}, threads={settings.threads}, preset={settings.preset}"
        )
        return settings

    def encode_video(self, composition: Dict[str, Any], output_path: str) -> str:
        """
        Build and encode the final video from a composition.

        Steps:
        1) Validate composition & collect element clips
        2) Resize every clip to the target resolution
        3) Concatenate with method='compose' to avoid size/audio mismatches
        4) Write final file with desired codecs/bitrates
        5) Add (optional) metadata

        Returns:
            The output_path on success.

        Raises:
            VideoEncodingError if anything fatal occurs.
        """
        # Defensive checks
        if not isinstance(composition, dict):
            raise VideoEncodingError("composition must be a dict.")

        elements = composition.get("elements", [])
        if not isinstance(elements, list) or not elements:
            raise VideoEncodingError("composition['elements'] must be a non-empty list.")

        try:
            settings = self.configure_output_settings()

            # Build clips
            clips: List[Any] = []
            for idx, element in enumerate(elements):
                clip = self._create_clip_from_element(element, settings)
                if clip is None:
                    logger.warning(f"Element {idx}: no clip produced (skipping).")
                    continue
                # Normalize resolution to avoid concat failures
                clip = clip.resize(newsize=settings.resolution)
                clips.append(clip)

            if not clips:
                raise VideoEncodingError("No usable video clips were created from the composition.")

            # Concatenate (compose is safer when sizes/audios differ)
            logger.info(f"Concatenating {len(clips)} clip(s).")
            final_clip = concatenate_videoclips(clips, method="compose")

            # Ensure output dir exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            # Write video
            logger.info(f"Writing final video to: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec=settings.vcodec,
                audio_codec=settings.acodec,
                bitrate=settings.vbr,
                audio_bitrate=settings.abr,
                fps=settings.fps,
                threads=settings.threads,
                preset=settings.preset,
                logger=None,  # silence MoviePy's own logger; we use our logger
            )

            # Cleanup MoviePy resources
            try:
                final_clip.close()
            except Exception:
                pass
            for c in clips:
                try:
                    c.close()
                except Exception:
                    pass

            # Optional metadata hook (no-op by default)
            self.add_metadata(output_path, composition)

            logger.info(f"Encoded video saved to: {output_path}")
            return output_path

        except VideoEncodingError:
            raise
        except Exception as e:
            logger.exception(f"Fatal error during encoding: {e}")
            raise VideoEncodingError(str(e)) from e

    def export_final_video(
        self,
        video_path: str,
        output_path: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Export/copy the final video with specific settings.

        Note:
            This is currently a simple file copy. You can replace this with an
            ffmpeg invocation to remux or transcode (e.g., change container/bitrate).

        Returns:
            output_path
        """
        try:
            if settings:
                self.configure_output_settings(settings)  # Validate/log
            if os.path.abspath(video_path) != os.path.abspath(output_path):
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(video_path, "rb") as src, open(output_path, "wb") as dst:
                    dst.write(src.read())
            logger.info(f"Exported final video to: {output_path}")
            return output_path
        except Exception as e:
            logger.exception(f"Error exporting final video: {e}")
            raise VideoEncodingError(str(e)) from e

    # -------------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------------
    def _create_clip_from_element(self, element: Dict[str, Any], settings: _OutputSettings):
        """
        Convert a single composition element to a MoviePy clip.

        Rules:
        - If element['duration'] is missing/zero, derive from frame_count / fps.
        - Audio, if present, is trimmed/padded to match the video clip duration.
        - Invalid/missing frames -> returns None.

        Returns:
            A MoviePy VideoClip (with audio set if available), or None if not possible.
        """
        try:
            anim = element.get("animation", {}) or {}
            audio_meta = element.get("audio", {}) or {}

            # Collect frame paths and filter to existing files
            raw_frames: Iterable[str] = anim.get("frame_paths", []) or []
            frame_paths: List[str] = [p for p in raw_frames if isinstance(p, str) and os.path.exists(p)]

            if not frame_paths:
                logger.warning("Element has no valid frames on disk; skipping.")
                return None

            # Create video from frames
            video_clip = ImageSequenceClip(frame_paths, fps=settings.fps)

            # Duration handling: explicit or derived
            duration: float = float(element.get("duration") or 0.0)
            if duration <= 0:
                # Derive from frame count
                duration = len(frame_paths) / float(settings.fps)
            # Time-stretch frames if explicit duration differs
            video_clip = video_clip.set_duration(duration)

            # Optional audio
            audio_path = audio_meta.get("path")
            if isinstance(audio_path, str) and os.path.exists(audio_path):
                try:
                    aclip = AudioFileClip(audio_path)
                except Exception as e:
                    logger.warning(f"Failed to load audio '{audio_path}': {e}")
                    aclip = None

                if aclip is not None:
                    # Match durations (trim or pad with silence)
                    if aclip.duration < duration:
                        aclip = aclip.set_duration(duration)
                    elif aclip.duration > duration:
                        aclip = aclip.subclip(0, duration)
                    video_clip = video_clip.set_audio(aclip)

            return video_clip

        except Exception as e:
            logger.error(f"Error creating clip from element: {e}")
            return None

    def add_metadata(self, video_path: str, composition: Dict[str, Any]) -> None:
        """
        Hook to add container metadata via ffmpeg if desired.

        Currently a no-op. To implement:
        - Create a temp output file
        - Run ffmpeg with -metadata ... -c copy
        - Replace original if successful
        """
        try:
            # Example (disabled):
            # meta = composition.get("meta", {})
            # if not meta: return
            # with tempfile.NamedTemporaryFile(suffix=f".{self.output_format}", delete=False) as tmp:
            #     tmp_out = tmp.name
            # cmd = [
            #     _ffmpeg_resolved or "ffmpeg", "-y",
            #     "-i", video_path,
            #     "-c", "copy",
            #     "-map_metadata", "0",
            #     "-metadata", f"title={meta.get('title','')}",
            #     tmp_out
            # ]
            # subprocess.run(cmd, check=True)
            # os.replace(tmp_out, video_path)
            logger.info(f"(metadata) No-op; video left unchanged: {video_path}")
        except Exception as e:
            logger.warning(f"Metadata step failed (ignored): {e}")

    # -------------------------------------------------------------------------
    # Utils
    # -------------------------------------------------------------------------
    @staticmethod
    def _coerce_res(value: Any) -> Tuple[int, int]:
        """
        Coerce resolution-like values into a (w, h) tuple of ints.
        Accepts:
            (1920,1080), ["1920","1080"], "1920x1080", "1920,1080"
        """
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return int(value[0]), int(value[1])
        if isinstance(value, str):
            for sep in ("x", "X", ",", " "):
                if sep in value:
                    w, h = value.split(sep)[:2]
                    return int(w.strip()), int(h.strip())
        # Fallback default
        return 1920, 1080

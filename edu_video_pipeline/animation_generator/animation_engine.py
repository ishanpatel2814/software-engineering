"""
Animation engine for creating animations for the educational video.
"""
from __future__ import annotations

import os
import logging
from typing import Dict, List, Any, Tuple

from PIL import Image

from animation_generator.transition_effects import TransitionEffects
from animation_generator.animation_styles import get_animation_preset
from utils.file_utils import create_temp_directory

logger = logging.getLogger("edu_video_pipeline")


class AnimationEngine:
    """Engine for creating animations for the educational video."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the animation engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.animation_style = config.get("DEFAULT_ANIMATION_STYLE", "standard")
        self.animation_complexity = config.get("ANIMATION_COMPLEXITY", "medium")
        self.output_resolution: Tuple[int, int] = tuple(config.get("OUTPUT_RESOLUTION", (1920, 1080)))
        self.fps = int(config.get("OUTPUT_FPS", 30))

        # Initialize transition effects and style preset
        self.transitions = TransitionEffects(config)
        self.animation_preset = get_animation_preset(self.animation_style)

        # Create temp directory
        self.temp_dir = create_temp_directory(config.get("TEMP_DIR"))

        # Performance: cache loaded and letterboxed images
        self._loaded_cache: Dict[str, Image.Image] = {}              # path -> PIL.Image
        self._fitted_cache: Dict[Tuple[str, int, int], Image.Image] = {}  # (path, w, h) -> fitted canvas

        # Pillow resampling (Pillow>=10 uses Image.Resampling)
        self._RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

        # Optional speed knob
        self.fast_mode = bool(self.config.get("ANIMATION_FAST_MODE", True))

    def create_animations(
        self,
        visuals: Dict[str, Any],
        content_structure: Dict[str, Any],
        audio_segments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create animations for the educational video.

        Args:
            visuals: Visual content data
            content_structure: Content structure data
            audio_segments: Audio segments data

        Returns:
            Dictionary containing animation data
        """
        logger.info("Creating animations for educational video")

        sections = content_structure.get("sections", []) or []
        audio_section_segments = audio_segments.get("sections", []) or []

        style_params = self.apply_animation_style()

        animation_segments = []
        for section_idx, section in enumerate(sections):
            logger.debug(f"Creating animation for section {section_idx + 1}/{len(sections)}")

            audio_segment = next((seg for seg in audio_section_segments if seg.get("section_idx") == section_idx), None)
            if not audio_segment:
                logger.warning(f"No audio segment found for section {section_idx + 1}")
                continue

            # Preload and fit once per section (key optimization)
            visual_content = self._get_section_visuals(section, section_idx, visuals)
            fitted_base = None
            if visual_content:
                path = visual_content[0].get("path")
                if path and os.path.exists(path):
                    try:
                        fitted_base = self._get_fitted_canvas(path, self.output_resolution)
                    except Exception as e:
                        logger.error(f"Failed to prepare base image for section {section_idx + 1}: {e}")

            section_animation = self._create_section_animation(
                section, section_idx, visual_content, audio_segment, style_params, fitted_base=fitted_base
            )
            animation_segments.append(section_animation)

        # Create transitions between sections
        transition_segments = []
        for section_idx in range(len(animation_segments) - 1):
            logger.debug(f"Creating transition animation {section_idx + 1}/{len(animation_segments) - 1}")
            transition_animation = self._create_transition_animation(
                animation_segments[section_idx],
                animation_segments[section_idx + 1],
                style_params,
            )
            transition_segments.append(transition_animation)

        animation_data = {
            "sections": animation_segments,
            "transitions": transition_segments,
            "style": self.animation_style,
            "metadata": {
                "total_duration": sum(segment["duration"] for segment in animation_segments),
                "section_count": len(animation_segments),
                "resolution": self.output_resolution,
                "fps": self.fps,
            },
        }

        logger.info(
            f"Created {len(animation_segments)} animation segments, "
            f"{animation_data['metadata']['total_duration']:.2f} seconds total"
        )
        return animation_data

    def apply_animation_style(self) -> Dict[str, Any]:
        """
        Apply the selected animation style.

        Returns:
            Dictionary containing style parameters
        """
        style_params = self.animation_preset.copy()
        if self.config.get("ANIMATION_COMPLEXITY"):
            style_params["complexity"] = self.config.get("ANIMATION_COMPLEXITY")
        logger.info(f"Applied animation style: {self.animation_style}, complexity: {style_params['complexity']}")
        return style_params

    def _create_section_animation(
        self,
        section: Dict[str, Any],
        section_idx: int,
        visuals: List[Dict[str, Any]],
        audio_segment: Dict[str, Any],
        style_params: Dict[str, Any],
        fitted_base: Image.Image | None = None,
    ) -> Dict[str, Any]:
        """
        Create animation for a section.
        """
        try:
            frames_dir = os.path.join(self.temp_dir, f"section_{section_idx + 1}_frames")
            os.makedirs(frames_dir, exist_ok=True)

            frames = self._generate_section_frames(
                visuals, audio_segment, style_params, frames_dir, fitted_base=fitted_base
            )

            animation_segment = {
                "section_idx": section_idx,
                "frames_dir": frames_dir,
                "frame_count": len(frames),
                "frame_paths": frames,
                "duration": float(audio_segment.get("duration", 0.0)),
                "fps": self.fps,
                "style": self.animation_style,
            }
            return animation_segment

        except Exception as e:
            logger.error(f"Error creating section animation: {e}")
            raise

    def _get_section_visuals(
        self,
        section: Dict[str, Any],
        section_idx: int,
        visuals: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Get visual content for a section.
        """
        if "slides" in visuals:
            slide_idx = section_idx
            if 0 <= slide_idx < len(visuals["slides"]):
                return [visuals["slides"][slide_idx]]
            logger.warning(f"No slide found for section {section_idx + 1}")
            return []
        if "pages" in visuals:
            page_idx = section_idx
            if 0 <= page_idx < len(visuals["pages"]):
                return [visuals["pages"][page_idx]]
            logger.warning(f"No page found for section {section_idx + 1}")
            return []
        logger.warning(f"No visual content found for section {section_idx + 1}")
        return []

    def _generate_section_frames(
        self,
        visual_content: List[Dict[str, Any]],
        audio_segment: Dict[str, Any],
        style_params: Dict[str, Any],
        output_dir: str,
        fitted_base: Image.Image | None = None,
    ) -> List[str]:
        """
        Generate frames for a section animation.
        """
        duration = float(audio_segment.get("duration", 0.0))
        frame_count = max(1, int(round(duration * self.fps)))

        frame_paths: List[str] = []
        for frame_idx in range(frame_count):
            time_pos = frame_idx / (frame_count - 1) if frame_count > 1 else 0.0
            frame_path = self._generate_frame(
                visual_content, time_pos, style_params, output_dir, frame_idx, fitted_base=fitted_base
            )
            frame_paths.append(frame_path)
        return frame_paths

    def _generate_frame(
        self,
        visual_content: List[Dict[str, Any]],
        time_pos: float,
        style_params: Dict[str, Any],
        output_dir: str,
        frame_idx: int,
        fitted_base: Image.Image | None = None,
    ) -> str:
        """
        Generate a single frame for the animation.
        """
        frame_path = os.path.join(output_dir, f"frame_{frame_idx:05d}.png")

        # Start with a white frame
        frame = Image.new("RGB", self.output_resolution, color="white")

        if visual_content:
            visual = visual_content[0]
            path = visual.get("path")

            try:
                # Use pre-fitted base if provided; otherwise compute & cache
                if fitted_base is not None:
                    base = fitted_base.copy()
                else:
                    base = self._get_fitted_canvas(path, self.output_resolution)

                # Apply time-based effects on a copy
                img = base.copy()
                img = self._apply_animation_effects(img, time_pos, style_params)

                if img.size == self.output_resolution:
                    # If RGBA, composite over white; else assign directly
                    if img.mode == "RGBA":
                        bg = Image.new("RGB", self.output_resolution, "white")
                        bg.paste(img, (0, 0), mask=img.split()[-1])
                        frame = bg
                    else:
                        frame = img
                else:
                    pos = self._center_image(img.size, self.output_resolution)
                    if img.mode == "RGBA":
                        frame.paste(img, pos, mask=img.split()[-1])
                    else:
                        frame.paste(img, pos)

            except Exception as e:
                logger.error(f"Error processing visual content: {e}")

        frame.save(frame_path, "PNG")
        return frame_path

    # ---------------------- Image caching & fitting ----------------------

    def _load_image(self, path: str) -> Image.Image:
        """
        Load an image from disk with caching.
        """
        if path in self._loaded_cache:
            return self._loaded_cache[path]
        img = Image.open(path)
        # Force load now so we don't keep an open file handle
        img.load()
        self._loaded_cache[path] = img
        return img

    def _get_fitted_canvas(self, path: str, target_size: Tuple[int, int]) -> Image.Image:
        """
        Return a letterboxed canvas of size target_size with the slide/page centered.
        Cached per (path, target_size).
        """
        key = (path, target_size[0], target_size[1])
        cached = self._fitted_cache.get(key)
        if cached is not None:
            return cached.copy()

        src = self._load_image(path)
        fitted = self._resize_image_to_fit(src, target_size)  # returns the letterboxed result
        self._fitted_cache[key] = fitted
        return fitted.copy()

    def _resize_image_to_fit(self, img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize an image to fit within target_size while maintaining aspect ratio
        and return a full-size canvas (letterboxed) ready to paste as a frame.
        """
        sw, sh = img.size
        tw, th = target_size
        if sw <= 0 or sh <= 0 or tw <= 0 or th <= 0:
            raise ValueError(f"Invalid sizes: src={img.size}, target={target_size}")

        scale = min(tw / sw, th / sh)
        nw = max(1, int(round(sw * scale)))
        nh = max(1, int(round(sh * scale)))

        # High-quality resize only once
        if (nw, nh) == (sw, sh):
            resized = img.copy()
        else:
            resized = img.resize((nw, nh), resample=self._RESAMPLE)

        # Letterbox on a white RGB canvas at final resolution
        canvas = Image.new("RGB", (tw, th), (255, 255, 255))
        px = (tw - nw) // 2
        py = (th - nh) // 2
        if resized.mode == "RGBA":
            canvas.paste(resized, (px, py), mask=resized.split()[-1])
        else:
            canvas.paste(resized, (px, py))
        return canvas

    def _center_image(self, img_size: Tuple[int, int], target_size: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calculate the position to center an image within a target size.
        """
        iw, ih = img_size
        tw, th = target_size
        return (tw - iw) // 2, (th - ih) // 2

    # ---------------------- Effects ----------------------

    def _apply_animation_effects(self, img: Image.Image, time_pos: float, style_params: Dict[str, Any]) -> Image.Image:
        """
        Apply animation effects to an image based on time position.
        """
        complexity = style_params.get("complexity", "medium")

        if complexity == "low":
            # Simple fade-in at the start
            if time_pos < 0.1:
                alpha = int(255 * (time_pos / 0.1))
                img = self._apply_alpha(img, alpha)

        elif complexity == "medium":
            # Fade-in + subtle zoom
            if time_pos < 0.2:
                alpha = int(255 * (time_pos / 0.2))
                img = self._apply_alpha(img, alpha)
                zoom_factor = 0.95 + (time_pos / 0.2) * 0.05
                img = self._apply_zoom(img, zoom_factor)

        elif complexity == "high":
            # Longer fade + zoom + slight motion
            if time_pos < 0.3:
                alpha = int(255 * (time_pos / 0.3))
                img = self._apply_alpha(img, alpha)
                zoom_factor = 0.90 + (time_pos / 0.3) * 0.10
                img = self._apply_zoom(img, zoom_factor)
                offset_x = int(10 * (1.0 - time_pos / 0.3))
                offset_y = int(5 * (1.0 - time_pos / 0.3))
                img = self._apply_offset(img, (offset_x, offset_y))

        return img

    def _apply_alpha(self, img: Image.Image, alpha: int) -> Image.Image:
        """
        Apply a global alpha value to an image (for fade-in).
        """
        alpha = max(0, min(255, alpha))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        r, g, b, a = img.split()
        a = a.point(lambda _i: alpha)
        return Image.merge("RGBA", (r, g, b, a))

    def _apply_zoom(self, img: Image.Image, zoom_factor: float) -> Image.Image:
        """
        Apply a zoom effect, keeping output size unchanged.
        """
        w, h = img.size
        nw = max(1, int(round(w * zoom_factor)))
        nh = max(1, int(round(h * zoom_factor)))

        resized = img.resize((nw, nh), resample=self._RESAMPLE)

        # Preserve transparency if present
        bg_color = (255, 255, 255, 0) if resized.mode == "RGBA" else (255, 255, 255)
        result = Image.new(resized.mode, (w, h), bg_color)
        px = (w - nw) // 2
        py = (h - nh) // 2
        if resized.mode == "RGBA":
            result.paste(resized, (px, py), mask=resized.split()[-1])
        else:
            result.paste(resized, (px, py))
        return result

    def _apply_offset(self, img: Image.Image, offset: Tuple[int, int]) -> Image.Image:
        """
        Apply a positional offset, keeping output size unchanged.
        """
        w, h = img.size
        bg_color = (255, 255, 255, 0) if img.mode == "RGBA" else (255, 255, 255)
        result = Image.new(img.mode, (w, h), bg_color)
        ox, oy = offset
        if img.mode == "RGBA":
            result.paste(img, (ox, oy), mask=img.split()[-1])
        else:
            result.paste(img, (ox, oy))
        return result

    # ---------------------- Transitions & rendering ----------------------

    def _create_transition_animation(
        self,
        from_segment: Dict[str, Any],
        to_segment: Dict[str, Any],
        style_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a transition animation between two segments.
        """
        try:
            transition_duration = float(style_params.get("transition_duration", 1.0))
            transition_dir = os.path.join(
                self.temp_dir,
                f"transition_{from_segment['section_idx']}_to_{to_segment['section_idx']}_frames",
            )
            os.makedirs(transition_dir, exist_ok=True)

            ttype = style_params.get("transition_type", "fade")
            if ttype == "fade":
                frames = self.transitions.fade_transition(
                    from_segment, to_segment, transition_duration, self.fps, transition_dir
                )
            elif ttype == "slide":
                frames = self.transitions.slide_transition(
                    from_segment, to_segment, transition_duration, self.fps, transition_dir
                )
            else:
                frames = self.transitions.fade_transition(
                    from_segment, to_segment, transition_duration, self.fps, transition_dir
                )

            return {
                "from_section_idx": from_segment["section_idx"],
                "to_section_idx": to_segment["section_idx"],
                "frames_dir": transition_dir,
                "frame_count": len(frames),
                "frame_paths": frames,
                "duration": transition_duration,
                "fps": self.fps,
                "transition_type": ttype,
            }

        except Exception as e:
            logger.error(f"Error creating transition animation: {e}")
            raise

    def generate_slide_transitions(self, animations: List[Dict[str, Any]], style_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate transitions between slides.
        """
        transitions = []
        for i in range(len(animations) - 1):
            transitions.append(self._create_transition_animation(animations[i], animations[i + 1], style_params))
        return transitions

    def render_animations(self, animations: List[Dict[str, Any]], transitions: List[Dict[str, Any]], output_dir: str) -> List[str]:
        """
        Placeholder: return frame directories; actual encoding is handled elsewhere.
        """
        video_paths = [a["frames_dir"] for a in animations] + [t["frames_dir"] for t in transitions]
        return video_paths

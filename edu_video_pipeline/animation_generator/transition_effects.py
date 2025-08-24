"""
Transition effects for the educational video pipeline.
"""
import os
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Any, Tuple

logger = logging.getLogger("edu_video_pipeline")


class TransitionEffects:
    """Library of transition effects for animations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the transition effects library.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.output_resolution = config.get("OUTPUT_RESOLUTION", (1920, 1080))
    
    def fade_transition(self, 
                       from_segment: Dict[str, Any], 
                       to_segment: Dict[str, Any],
                       duration: float,
                       fps: int,
                       output_dir: str) -> List[str]:
        """
        Create a fade transition between two segments.
        
        Args:
            from_segment: Source animation segment
            to_segment: Target animation segment
            duration: Transition duration in seconds
            fps: Frames per second
            output_dir: Output directory for frames
        
        Returns:
            List of frame paths
        """
        try:
            # Calculate number of frames
            frame_count = int(duration * fps)
            
            # Get last frame from source segment
            if from_segment["frame_paths"]:
                from_img = Image.open(from_segment["frame_paths"][-1])
            else:
                # If no source frames, create a blank image
                from_img = Image.new("RGB", self.output_resolution, color="white")
            
            # Get first frame from target segment
            if to_segment["frame_paths"]:
                to_img = Image.open(to_segment["frame_paths"][0])
            else:
                # If no target frames, create a blank image
                to_img = Image.new("RGB", self.output_resolution, color="white")
            
            # Generate transition frames
            frame_paths = []
            for frame_idx in range(frame_count):
                # Calculate blend factor (0.0 to 1.0)
                alpha = frame_idx / (frame_count - 1) if frame_count > 1 else 1.0
                
                # Create blended frame
                blended_frame = Image.blend(from_img, to_img, alpha)
                
                # Save frame
                frame_path = os.path.join(output_dir, f"frame_{frame_idx:05d}.png")
                blended_frame.save(frame_path, "PNG")
                
                frame_paths.append(frame_path)
            
            logger.debug(f"Created fade transition with {frame_count} frames")
            
            return frame_paths
            
        except Exception as e:
            logger.error(f"Error creating fade transition: {str(e)}")
            raise
    
    def slide_transition(self, 
                        from_segment: Dict[str, Any], 
                        to_segment: Dict[str, Any],
                        duration: float,
                        fps: int,
                        output_dir: str) -> List[str]:
        """
        Create a slide transition between two segments.
        
        Args:
            from_segment: Source animation segment
            to_segment: Target animation segment
            duration: Transition duration in seconds
            fps: Frames per second
            output_dir: Output directory for frames
        
        Returns:
            List of frame paths
        """
        try:
            # Calculate number of frames
            frame_count = int(duration * fps)
            
            # Get last frame from source segment
            if from_segment["frame_paths"]:
                from_img = Image.open(from_segment["frame_paths"][-1])
            else:
                # If no source frames, create a blank image
                from_img = Image.new("RGB", self.output_resolution, color="white")
            
            # Get first frame from target segment
            if to_segment["frame_paths"]:
                to_img = Image.open(to_segment["frame_paths"][0])
            else:
                # If no target frames, create a blank image
                to_img = Image.new("RGB", self.output_resolution, color="white")
            
            # Get dimensions
            width, height = self.output_resolution
            
            # Generate transition frames
            frame_paths = []
            for frame_idx in range(frame_count):
                # Calculate slide position (0.0 to 1.0)
                slide_pos = frame_idx / (frame_count - 1) if frame_count > 1 else 1.0
                
                # Create a blank frame
                frame = Image.new("RGB", (width, height), color="white")
                
                # Calculate positions for sliding effect (slide from right to left)
                from_x = int(-width * slide_pos)
                to_x = int(width * (1.0 - slide_pos))
                
                # Paste the images
                frame.paste(from_img, (from_x, 0))
                frame.paste(to_img, (to_x, 0))
                
                # Save frame
                frame_path = os.path.join(output_dir, f"frame_{frame_idx:05d}.png")
                frame.save(frame_path, "PNG")
                
                frame_paths.append(frame_path)
            
            logger.debug(f"Created slide transition with {frame_count} frames")
            
            return frame_paths
            
        except Exception as e:
            logger.error(f"Error creating slide transition: {str(e)}")
            raise
    
    def zoom_effect(self, 
                   img: Image.Image,
                   zoom_factor: float) -> Image.Image:
        """
        Apply a zoom effect to an image.
        
        Args:
            img: Input image
            zoom_factor: Zoom factor (1.0 = original size)
        
        Returns:
            Zoomed image
        """
        # Get image dimensions
        width, height = img.size
        
        # Calculate new dimensions
        new_width = int(width * zoom_factor)
        new_height = int(height * zoom_factor)
        
        # Calculate crop box (center of the image)
        left = (width - new_width) // 2
        top = (height - new_height) // 2
        right = left + new_width
        bottom = top + new_height
        
        # Crop and resize
        cropped = img.crop((left, top, right, bottom))
        zoomed = cropped.resize((width, height), Image.LANCZOS)
        
        return zoomed
    
    def highlight_effect(self, 
                        img: Image.Image,
                        region: Tuple[int, int, int, int],
                        color: Tuple[int, int, int] = (255, 255, 0),
                        alpha: int = 128) -> Image.Image:
        """
        Apply a highlight effect to a region of an image.
        
        Args:
            img: Input image
            region: Region to highlight (left, top, right, bottom)
            color: Highlight color (R, G, B)
            alpha: Highlight opacity (0-255)
        
        Returns:
            Image with highlight effect
        """
        # Create a copy of the image
        result = img.copy()
        
        # Create a transparent overlay
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw highlight rectangle
        draw.rectangle(region, fill=(*color, alpha))
        
        # Composite the overlay onto the result
        if result.mode != "RGBA":
            result = result.convert("RGBA")
        
        result = Image.alpha_composite(result, overlay)
        
        return result
    
    def create_transition_frames(self, 
                               from_img: Image.Image,
                               to_img: Image.Image,
                               transition_type: str,
                               frame_count: int,
                               output_dir: str) -> List[str]:
        """
        Create transition frames between two images.
        
        Args:
            from_img: Source image
            to_img: Target image
            transition_type: Type of transition ("fade", "slide", "zoom")
            frame_count: Number of frames to generate
            output_dir: Output directory for frames
        
        Returns:
            List of frame paths
        """
        frame_paths = []
        
        if transition_type == "fade":
            # Generate fade transition frames
            for frame_idx in range(frame_count):
                # Calculate blend factor (0.0 to 1.0)
                alpha = frame_idx / (frame_count - 1) if frame_count > 1 else 1.0
                
                # Create blended frame
                blended_frame = Image.blend(from_img, to_img, alpha)
                
                # Save frame
                frame_path = os.path.join(output_dir, f"frame_{frame_idx:05d}.png")
                blended_frame.save(frame_path, "PNG")
                
                frame_paths.append(frame_path)
        
        elif transition_type == "slide":
            # Get dimensions
            width, height = from_img.size
            
            # Generate slide transition frames
            for frame_idx in range(frame_count):
                # Calculate slide position (0.0 to 1.0)
                slide_pos = frame_idx / (frame_count - 1) if frame_count > 1 else 1.0
                
                # Create a blank frame
                frame = Image.new("RGB", (width, height), color="white")
                
                # Calculate positions for sliding effect (slide from right to left)
                from_x = int(-width * slide_pos)
                to_x = int(width * (1.0 - slide_pos))
                
                # Paste the images
                frame.paste(from_img, (from_x, 0))
                frame.paste(to_img, (to_x, 0))
                
                # Save frame
                frame_path = os.path.join(output_dir, f"frame_{frame_idx:05d}.png")
                frame.save(frame_path, "PNG")
                
                frame_paths.append(frame_path)
        
        elif transition_type == "zoom":
            # Generate zoom transition frames
            for frame_idx in range(frame_count):
                # Calculate zoom position (0.0 to 1.0)
                zoom_pos = frame_idx / (frame_count - 1) if frame_count > 1 else 1.0
                
                if zoom_pos < 0.5:
                    # First half: zoom out from source image
                    zoom_factor = 1.0 - (zoom_pos * 0.5)
                    frame = self.zoom_effect(from_img, zoom_factor)
                    
                    # Apply fade out
                    opacity = 255 - int(zoom_pos * 2 * 255)
                    frame = self._apply_opacity(frame, opacity)
                else:
                    # Second half: zoom in to target image
                    zoom_factor = 0.5 + ((zoom_pos - 0.5) * 1.0)
                    frame = self.zoom_effect(to_img, zoom_factor)
                    
                    # Apply fade in
                    opacity = int((zoom_pos - 0.5) * 2 * 255)
                    frame = self._apply_opacity(frame, opacity)
                
                # Save frame
                frame_path = os.path.join(output_dir, f"frame_{frame_idx:05d}.png")
                frame.save(frame_path, "PNG")
                
                frame_paths.append(frame_path)
        
        else:
            # Default to fade transition
            logger.warning(f"Unknown transition type: {transition_type}, using fade instead")
            return self.create_transition_frames(from_img, to_img, "fade", frame_count, output_dir)
        
        return frame_paths
    
    def _apply_opacity(self, img: Image.Image, opacity: int) -> Image.Image:
        """
        Apply opacity to an image.
        
        Args:
            img: Input image
            opacity: Opacity value (0-255)
        
        Returns:
            Image with opacity applied
        """
        # Ensure opacity is in valid range
        opacity = max(0, min(255, opacity))
        
        # Create an alpha channel
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        # Get alpha channel
        r, g, b, a = img.split()
        
        # Apply opacity to alpha channel
        a = a.point(lambda i: i * opacity // 255)
        
        # Merge channels
        result = Image.merge("RGBA", (r, g, b, a))
        
        return result
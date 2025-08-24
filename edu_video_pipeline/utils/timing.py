"""
Timing utilities for the PDF/PPT to Educational Video Pipeline.
"""
import re
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger("edu_video_pipeline")


def calculate_speaking_rate(text: str, words_per_minute: int = 150) -> float:
    """
    Calculate the duration needed to speak the given text.
    
    Args:
        text: Text to be spoken
        words_per_minute: Average speaking rate
    
    Returns:
        Duration in seconds
    """
    # Count words (split by whitespace)
    word_count = len(re.findall(r'\S+', text))
    
    # Calculate duration in seconds
    duration_seconds = (word_count / words_per_minute) * 60
    
    return duration_seconds


def estimate_slide_duration(
    slide_content: Dict[str, Any], 
    words_per_minute: int = 150,
    min_duration: float = 5.0
) -> float:
    """
    Estimate the duration needed for a slide based on its content.
    
    Args:
        slide_content: Slide content data
        words_per_minute: Average speaking rate
        min_duration: Minimum duration for any slide
    
    Returns:
        Estimated duration in seconds
    """
    # Get text content
    text = slide_content.get("text", "")
    
    # Calculate base duration from text
    base_duration = calculate_speaking_rate(text, words_per_minute)
    
    # Add time for visual elements
    visual_count = len(slide_content.get("visuals", []))
    visual_duration = visual_count * 2.0  # Add 2 seconds per visual element
    
    # Calculate total duration
    total_duration = max(base_duration + visual_duration, min_duration)
    
    logger.debug(f"Estimated slide duration: {total_duration:.2f}s " 
                f"(text: {base_duration:.2f}s, visuals: {visual_duration:.2f}s)")
    
    return total_duration


def adjust_timing(
    durations: List[float], 
    multiplier: float = 1.0
) -> List[float]:
    """
    Adjust timing durations by a multiplier.
    
    Args:
        durations: List of durations in seconds
        multiplier: Timing multiplier (>1 makes slower, <1 makes faster)
    
    Returns:
        Adjusted durations
    """
    return [duration * multiplier for duration in durations]
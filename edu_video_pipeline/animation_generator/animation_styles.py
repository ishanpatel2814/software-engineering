"""
Animation style presets for the educational video pipeline.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger("edu_video_pipeline")

# Define animation presets
ANIMATION_PRESETS = {
    # Standard animation style (moderate effects)
    "standard": {
        "complexity": "medium",
        "transition_type": "fade",
        "transition_duration": 1.0,
        "zoom_effect": True,
        "zoom_factor": 0.05,
        "fade_effect": True,
        "highlight_effect": True,
        "motion_effect": False,
        "color_scheme": {
            "background": (255, 255, 255),
            "text": (0, 0, 0),
            "accent": (41, 128, 185)
        }
    },
    
    # Minimal animation style (subtle effects)
    "minimal": {
        "complexity": "low",
        "transition_type": "fade",
        "transition_duration": 0.8,
        "zoom_effect": False,
        "fade_effect": True,
        "highlight_effect": False,
        "motion_effect": False,
        "color_scheme": {
            "background": (255, 255, 255),
            "text": (0, 0, 0),
            "accent": (52, 73, 94)
        }
    },
    
    # Dynamic animation style (rich effects)
    "dynamic": {
        "complexity": "high",
        "transition_type": "slide",
        "transition_duration": 1.2,
        "zoom_effect": True,
        "zoom_factor": 0.1,
        "fade_effect": True,
        "highlight_effect": True,
        "motion_effect": True,
        "color_scheme": {
            "background": (255, 255, 255),
            "text": (0, 0, 0),
            "accent": (192, 57, 43)
        }
    },
    
    # Professional animation style (clean transitions)
    "professional": {
        "complexity": "medium",
        "transition_type": "fade",
        "transition_duration": 0.9,
        "zoom_effect": True,
        "zoom_factor": 0.03,
        "fade_effect": True,
        "highlight_effect": True,
        "motion_effect": False,
        "color_scheme": {
            "background": (250, 250, 250),
            "text": (44, 62, 80),
            "accent": (52, 152, 219)
        }
    },
    
    # Academic animation style (clear focus on content)
    "academic": {
        "complexity": "low",
        "transition_type": "fade",
        "transition_duration": 0.7,
        "zoom_effect": False,
        "fade_effect": True,
        "highlight_effect": True,
        "motion_effect": False,
        "color_scheme": {
            "background": (253, 254, 254),
            "text": (40, 40, 40),
            "accent": (41, 128, 185)
        }
    },
    
    # Energetic animation style (lively transitions)
    "energetic": {
        "complexity": "high",
        "transition_type": "slide",
        "transition_duration": 1.5,
        "zoom_effect": True,
        "zoom_factor": 0.15,
        "fade_effect": True,
        "highlight_effect": True,
        "motion_effect": True,
        "color_scheme": {
            "background": (255, 255, 255),
            "text": (0, 0, 0),
            "accent": (230, 126, 34)
        }
    }
}


def get_animation_preset(style_name: str) -> Dict[str, Any]:
    """
    Get animation preset parameters for a specified style.
    
    Args:
        style_name: Name of the animation style
    
    Returns:
        Dictionary containing animation preset parameters
    """
    # If style exists, return it
    if style_name in ANIMATION_PRESETS:
        logger.info(f"Using animation style preset: {style_name}")
        return ANIMATION_PRESETS[style_name].copy()
    
    # If style doesn't exist, use standard and log a warning
    logger.warning(f"Unknown animation style: {style_name}, using 'standard' instead")
    return ANIMATION_PRESETS["standard"].copy()


def list_available_styles() -> Dict[str, Dict[str, str]]:
    """
    List all available animation styles with descriptions.
    
    Returns:
        Dictionary containing style names and descriptions
    """
    # Define descriptions for each style
    style_descriptions = {
        "standard": "Balanced effects with moderate transitions",
        "minimal": "Subtle, clean animations with minimal distraction",
        "dynamic": "Rich, engaging animations with noticeable effects",
        "professional": "Clean, corporate-style transitions and effects",
        "academic": "Clear focus on content with understated animations",
        "energetic": "Lively, attention-grabbing animations and transitions"
    }
    
    # Create result with available styles and descriptions
    available_styles = {}
    for style in ANIMATION_PRESETS.keys():
        available_styles[style] = {
            "description": style_descriptions.get(style, "No description available"),
            "complexity": ANIMATION_PRESETS[style]["complexity"]
        }
    
    return available_styles
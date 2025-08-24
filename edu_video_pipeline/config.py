"""
Configuration settings for the PDF/PPT to Educational Video Pipeline.
"""
import os
import argparse
from typing import Dict, Tuple, Any

class Config:
    """Configuration class for the educational video pipeline."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        # API Keys (to be set via constructor or args)
       "OPENAI_API_KEY": "",
        "ELEVENLABS_API_KEY": "",
        
        # OpenAI settings
        "OPENAI_MODEL": "gpt-4",
        "OPENAI_MAX_TOKENS": 2000,
        "OPENAI_TEMPERATURE": 0.7,
        
        # ElevenLabs settings
        "ELEVENLABS_VOICE_ID": "21m00Tcm4TlvDq8ikWAM",  # Default voice ID
        "ELEVENLABS_STABILITY": 0.5,
        "ELEVENLABS_SIMILARITY_BOOST": 0.75,
        
        # Video settings
        "OUTPUT_RESOLUTION": (1920, 1080),
        "OUTPUT_FPS": 30,
        "OUTPUT_FORMAT": "mp4",
        
        # Animation settings
        "DEFAULT_ANIMATION_STYLE": "standard",
        "ANIMATION_COMPLEXITY": "medium",
        
        # Timing settings
        "WORDS_PER_MINUTE": 150,  # Average speaking rate
        "MIN_SLIDE_DURATION": 5,  # Minimum seconds per slide
        "DURATION_MULTIPLIER": 1.0,  # Adjust overall timing
        
        # File paths
        "TEMP_DIR": "temp",
        "DEFAULT_OUTPUT_DIR": "output",
        
        # Logging
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "pipeline.log",
    }
    
    def __init__(self, args=None):
        """
        Initialize configuration with default values and override with args.
        
        Args:
            args: Optional ArgumentParser args to override config values
        """
        # Start with default config
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Override with args if provided
        if args:
            self._update_from_args(args)
        
        # Create necessary directories
        os.makedirs(self.config["TEMP_DIR"], exist_ok=True)
        os.makedirs(self.config["DEFAULT_OUTPUT_DIR"], exist_ok=True)
    
    def _update_from_args(self, args):
        """Update config from command line arguments."""
        # Convert args to dictionary
        args_dict = vars(args)
        
        # Update API keys if provided
        if args_dict.get("openai_key"):
            self.config["OPENAI_API_KEY"] = args_dict["openai_key"]
        
        if args_dict.get("elevenlabs_key"):
            self.config["ELEVENLABS_API_KEY"] = args_dict["elevenlabs_key"]
        
        # Update other settings if provided
        if args_dict.get("output"):
            output_dir = os.path.dirname(args_dict["output"])
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
        
        if args_dict.get("duration"):
            self.config["DURATION_MULTIPLIER"] = args_dict["duration"]
        
        if args_dict.get("animation_style"):
            self.config["DEFAULT_ANIMATION_STYLE"] = args_dict["animation_style"]
        
        if args_dict.get("voice"):
            self.config["ELEVENLABS_VOICE_ID"] = args_dict["voice"]
    
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value
    
    def validate(self):
        """Validate the configuration."""
        # Check that API keys are set
        if not self.config["OPENAI_API_KEY"]:
            raise ValueError("OpenAI API key is not set")
        
        if not self.config["ELEVENLABS_API_KEY"]:
            raise ValueError("ElevenLabs API key is not set")
        
        return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Convert PDF/PPT to educational video')
    
    # Required arguments
    parser.add_argument('--input', '-i', required=True, 
                        help='Input PDF or PPT file path')
    
    # Optional arguments
    parser.add_argument('--output', '-o', 
                        help='Output video file path')
    parser.add_argument('--duration', '-d', type=float, 
                        help='Duration multiplier for timing')
    parser.add_argument('--animation-style', '-a', 
                        help='Animation style preset')
    parser.add_argument('--voice', '-v', 
                        help='ElevenLabs voice ID')
    
    # API keys
    parser.add_argument('--openai-key', 
                        help='OpenAI API key')
    parser.add_argument('--elevenlabs-key', 
                        help='ElevenLabs API key')
    
    return parser.parse_args()
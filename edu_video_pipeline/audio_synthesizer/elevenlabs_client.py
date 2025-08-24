"""
ElevenLabs API client for synthesizing speech from script text.
"""
import os
import logging
import requests
import json
from typing import Dict, List, Any, Optional, BinaryIO

logger = logging.getLogger("edu_video_pipeline")


class ElevenLabsClient:
    """Client for the ElevenLabs API to synthesize speech."""
    
    # ElevenLabs API endpoints
    API_BASE_URL = "https://api.elevenlabs.io/v1"
    VOICES_ENDPOINT = "/voices"
    TEXT_TO_SPEECH_ENDPOINT = "/text-to-speech/{voice_id}"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ElevenLabs client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.api_key = config.get("ELEVENLABS_API_KEY")
        self.voice_id = config.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.stability = config.get("ELEVENLABS_STABILITY", 0.5)
        self.similarity_boost = config.get("ELEVENLABS_SIMILARITY_BOOST", 0.75)
        
        # Initialize client
        self.initialize_client()
    
    def initialize_client(self) -> None:
        """Initialize the ElevenLabs client with API key."""
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
        
        # Set up headers for API requests
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        
        logger.info(f"Initialized ElevenLabs client with voice ID: {self.voice_id}")
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get available voices from the ElevenLabs API.
        
        Returns:
            List of available voices
        """
        try:
            # Make API request
            url = f"{self.API_BASE_URL}{self.VOICES_ENDPOINT}"
            response = requests.get(url, headers=self.headers)
            
            # Check response
            if response.status_code != 200:
                raise ValueError(f"Error getting voices: {response.status_code}, {response.text}")
            
            # Parse response
            data = response.json()
            voices = data.get("voices", [])
            
            logger.info(f"Retrieved {len(voices)} voices from ElevenLabs API")
            
            return voices
            
        except Exception as e:
            logger.error(f"Error getting voices from ElevenLabs API: {str(e)}")
            raise
    
    def synthesize_speech(self, text: str, output_path: str) -> str:
        """
        Synthesize speech from text using the ElevenLabs API.
        
        Args:
            text: Text to synthesize
            output_path: Path to save the audio file
        
        Returns:
            Path to the saved audio file
        """
        try:
            # Make API request
            url = f"{self.API_BASE_URL}{self.TEXT_TO_SPEECH_ENDPOINT.format(voice_id=self.voice_id)}"
            
            # Prepare request data
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost
                }
            }
            
            # Send request
            response = requests.post(url, json=data, headers=self.headers)
            
            # Check response
            if response.status_code != 200:
                raise ValueError(f"Error synthesizing speech: {response.status_code}, {response.text}")
            
            # Save audio to file
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Synthesized speech saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error synthesizing speech with ElevenLabs API: {str(e)}")
            raise
    
    def handle_response(self, response: requests.Response) -> bytes:
        """
        Handle the response from the ElevenLabs API.
        
        Args:
            response: API response
        
        Returns:
            Audio data
        """
        try:
            # Check response
            if response.status_code != 200:
                raise ValueError(f"Error from ElevenLabs API: {response.status_code}, {response.text}")
            
            # Return audio data
            return response.content
            
        except Exception as e:
            logger.error(f"Error handling response from ElevenLabs API: {str(e)}")
            raise
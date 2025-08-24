"""
Audio processor for generating and processing audio narration.
"""
import os
import logging
import re
from typing import Dict, List, Any, Tuple
from pydub import AudioSegment

from audio_synthesizer.elevenlabs_client import ElevenLabsClient
from utils.file_utils import create_temp_directory

logger = logging.getLogger("edu_video_pipeline")


class AudioProcessor:
    """Processor for generating and processing audio narration."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the audio processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.elevenlabs_client = ElevenLabsClient(config)
        self.temp_dir = create_temp_directory(config.get("TEMP_DIR"))
    
    def process_audio(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a script into audio segments.
        
        Args:
            script: Script data
        
        Returns:
            Dictionary containing audio segments
        """
        logger.info("Processing script into audio segments")
        
        # Extract sections
        sections = script.get("sections", [])
        
        # Generate audio for each section
        audio_segments = []
        for section_idx, section in enumerate(sections):
            logger.debug(f"Generating audio for section {section_idx+1}/{len(sections)}")
            
            # Generate audio for this section
            section_audio = self._generate_section_audio(section, section_idx)
            
            # Add to audio segments
            audio_segments.append(section_audio)
        
        # Generate transitions if available
        transition_segments = []
        for section_idx, section in enumerate(sections[:-1]):
            if "transition" in section and section["transition"]:
                logger.debug(f"Generating audio for transition {section_idx+1}")
                
                # Generate audio for this transition
                transition_audio = self._generate_transition_audio(
                    section["transition"], section_idx
                )
                
                # Add to transition segments
                transition_segments.append(transition_audio)
        
        # Assemble final audio data
        audio_data = {
            "sections": audio_segments,
            "transitions": transition_segments,
            "metadata": {
                "total_duration": sum(segment["duration"] for segment in audio_segments),
                "section_count": len(audio_segments)
            }
        }
        
        logger.info(f"Generated {len(audio_segments)} audio segments, " 
                   f"{audio_data['metadata']['total_duration']:.2f} seconds total")
        
        return audio_data
    
    def _generate_section_audio(self, section: Dict[str, Any], section_idx: int) -> Dict[str, Any]:
        """
        Generate audio for a script section.
        
        Args:
            section: Section data
            section_idx: Section index
        
        Returns:
            Dictionary containing section audio data
        """
        try:
            # Extract text
            text = section.get("text", "")
            
            # Create output path
            output_filename = f"section_{section_idx+1}.mp3"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # Generate audio
            self.elevenlabs_client.synthesize_speech(text, output_path)
            
            # Calculate audio duration
            duration = self._get_audio_duration(output_path)
            
            # Create audio segment data
            audio_segment = {
                "section_idx": section_idx,
                "path": output_path,
                "duration": duration,
                "text": text
            }
            
            return audio_segment
            
        except Exception as e:
            logger.error(f"Error generating section audio: {str(e)}")
            raise
    
    def _generate_transition_audio(self, transition_text: str, section_idx: int) -> Dict[str, Any]:
        """
        Generate audio for a transition.
        
        Args:
            transition_text: Transition text
            section_idx: Section index
        
        Returns:
            Dictionary containing transition audio data
        """
        try:
            # Create output path
            output_filename = f"transition_{section_idx+1}.mp3"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # Generate audio
            self.elevenlabs_client.synthesize_speech(transition_text, output_path)
            
            # Calculate audio duration
            duration = self._get_audio_duration(output_path)
            
            # Create audio segment data
            audio_segment = {
                "section_idx": section_idx,
                "path": output_path,
                "duration": duration,
                "text": transition_text
            }
            
            return audio_segment
            
        except Exception as e:
            logger.error(f"Error generating transition audio: {str(e)}")
            raise
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """
        Get the duration of an audio file.
        
        Args:
            audio_path: Path to the audio file
        
        Returns:
            Duration in seconds
        """
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Get duration in seconds
            duration = len(audio) / 1000.0
            
            return duration
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            # Return estimated duration if actual duration can't be determined
            return 0.0
    
    def calculate_timing(self, audio_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate timing information for audio segments.
        
        Args:
            audio_segments: List of audio segments
        
        Returns:
            Dictionary containing timing information
        """
        # Calculate start and end times for each segment
        current_time = 0.0
        for segment in audio_segments:
            segment["start_time"] = current_time
            segment["end_time"] = current_time + segment["duration"]
            current_time = segment["end_time"]
        
        # Create timing data
        timing_data = {
            "total_duration": current_time,
            "segments": audio_segments
        }
        
        return timing_data
    
    def segment_audio(self, audio_path: str, segments: List[Tuple[float, float]]) -> List[str]:
        """
        Segment an audio file into smaller parts.
        
        Args:
            audio_path: Path to the audio file
            segments: List of (start_time, end_time) tuples in seconds
        
        Returns:
            List of paths to the segmented audio files
        """
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Create segments
            segment_paths = []
            for idx, (start_time, end_time) in enumerate(segments):
                # Convert times to milliseconds
                start_ms = int(start_time * 1000)
                end_ms = int(end_time * 1000)
                
                # Extract segment
                segment = audio[start_ms:end_ms]
                
                # Save segment
                segment_filename = f"{os.path.splitext(os.path.basename(audio_path))[0]}_segment_{idx+1}.mp3"
                segment_path = os.path.join(self.temp_dir, segment_filename)
                segment.export(segment_path, format="mp3")
                
                segment_paths.append(segment_path)
            
            return segment_paths
            
        except Exception as e:
            logger.error(f"Error segmenting audio: {str(e)}")
            raise
    
    def export_audio(self, audio_segments: List[Dict[str, Any]], output_path: str) -> str:
        """
        Export audio segments to a single file.
        
        Args:
            audio_segments: List of audio segments
            output_path: Path to save the combined audio file
        
        Returns:
            Path to the combined audio file
        """
        try:
            # Create combined audio
            combined = AudioSegment.empty()
            
            # Add each segment
            for segment in audio_segments:
                # Load segment
                audio = AudioSegment.from_file(segment["path"])
                
                # Add to combined audio
                combined += audio
            
            # Export combined audio
            combined.export(output_path, format="mp3")
            
            logger.info(f"Exported combined audio to: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting audio: {str(e)}")
            raise
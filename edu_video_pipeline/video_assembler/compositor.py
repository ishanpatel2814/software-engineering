"""
Video compositor for synchronizing audio with visuals.
"""
import os
import logging
import shutil
from typing import Dict, List, Any, Tuple
import tempfile

from utils.file_utils import create_temp_directory

logger = logging.getLogger("edu_video_pipeline")


class VideoCompositor:
    """Compositor for synchronizing audio with visuals."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the video compositor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.output_resolution = config.get("OUTPUT_RESOLUTION", (1920, 1080))
        self.fps = config.get("OUTPUT_FPS", 30)
        self.temp_dir = create_temp_directory(config.get("TEMP_DIR"))
    
    def sync_audio_with_visuals(self, 
                              animations: Dict[str, Any], 
                              audio_segments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronize audio with visual animations.
        
        Args:
            animations: Animation data
            audio_segments: Audio segments data
        
        Returns:
            Dictionary containing synchronized composition data
        """
        logger.info("Synchronizing audio with visuals")
        
        # Create a composition directory
        composition_dir = os.path.join(self.temp_dir, "composition")
        os.makedirs(composition_dir, exist_ok=True)
        
        # Extract sections
        animation_sections = animations.get("sections", [])
        animation_transitions = animations.get("transitions", [])
        audio_sections = audio_segments.get("sections", [])
        audio_transitions = audio_segments.get("transitions", [])
        
        # Create segment compositions
        segment_compositions = []
        for section_idx, anim_section in enumerate(animation_sections):
            logger.debug(f"Synchronizing section {section_idx+1}/{len(animation_sections)}")
            
            # Find corresponding audio section
            audio_section = next(
                (a for a in audio_sections if a["section_idx"] == anim_section["section_idx"]), 
                None
            )
            
            if not audio_section:
                logger.warning(f"No audio found for section {section_idx+1}")
                continue
            
            # Create composition for this section
            segment_comp = self._create_segment_composition(
                anim_section, audio_section, section_idx, composition_dir
            )
            
            segment_compositions.append(segment_comp)
        
        # Create transition compositions
        transition_compositions = []
        for trans_idx, anim_trans in enumerate(animation_transitions):
            logger.debug(f"Synchronizing transition {trans_idx+1}/{len(animation_transitions)}")
            
            # Find corresponding audio transition
            audio_trans = next(
                (a for a in audio_transitions if a["section_idx"] == anim_trans["from_section_idx"]), 
                None
            )
            
            # Create composition for this transition
            trans_comp = self._create_transition_composition(
                anim_trans, audio_trans, trans_idx, composition_dir
            )
            
            transition_compositions.append(trans_comp)
        
        # Assemble final composition
        composition = self.assemble_video_segments(
            segment_compositions, transition_compositions, composition_dir
        )
        
        logger.info(f"Created video composition with {len(segment_compositions)} segments, " 
                   f"{len(transition_compositions)} transitions")
        
        return composition
    
    def _create_segment_composition(self, 
                                  animation: Dict[str, Any], 
                                  audio: Dict[str, Any],
                                  section_idx: int,
                                  output_dir: str) -> Dict[str, Any]:
        """
        Create a composition for a segment.
        
        Args:
            animation: Animation segment data
            audio: Audio segment data
            section_idx: Section index
            output_dir: Output directory
        
        Returns:
            Dictionary containing segment composition data
        """
        try:
            # Create segment directory
            segment_dir = os.path.join(output_dir, f"segment_{section_idx+1}")
            os.makedirs(segment_dir, exist_ok=True)
            
            # Create composition file with audio and visual info
            composition_file = os.path.join(segment_dir, "composition.json")
            
            # Create segment composition data
            segment_comp = {
                "section_idx": section_idx,
                "animation": animation,
                "audio": audio,
                "composition_file": composition_file,
                "composition_dir": segment_dir,
                "duration": max(animation["duration"], audio["duration"]),
                "frame_count": animation["frame_count"],
                "fps": self.fps
            }
            
            return segment_comp
            
        except Exception as e:
            logger.error(f"Error creating segment composition: {str(e)}")
            raise
    
    def _create_transition_composition(self, 
                                     animation: Dict[str, Any], 
                                     audio: Dict[str, Any],
                                     transition_idx: int,
                                     output_dir: str) -> Dict[str, Any]:
        """
        Create a composition for a transition.
        
        Args:
            animation: Animation transition data
            audio: Audio transition data (optional)
            transition_idx: Transition index
            output_dir: Output directory
        
        Returns:
            Dictionary containing transition composition data
        """
        try:
            # Create transition directory
            transition_dir = os.path.join(output_dir, f"transition_{transition_idx+1}")
            os.makedirs(transition_dir, exist_ok=True)
            
            # Create composition file with audio and visual info
            composition_file = os.path.join(transition_dir, "composition.json")
            
            # Calculate duration based on available audio
            duration = animation["duration"]
            if audio:
                duration = max(animation["duration"], audio["duration"])
            
            # Create transition composition data
            transition_comp = {
                "transition_idx": transition_idx,
                "from_section_idx": animation["from_section_idx"],
                "to_section_idx": animation["to_section_idx"],
                "animation": animation,
                "audio": audio,  # May be None
                "composition_file": composition_file,
                "composition_dir": transition_dir,
                "duration": duration,
                "frame_count": animation["frame_count"],
                "fps": self.fps
            }
            
            return transition_comp
            
        except Exception as e:
            logger.error(f"Error creating transition composition: {str(e)}")
            raise
    
    def assemble_video_segments(self, 
                              segments: List[Dict[str, Any]], 
                              transitions: List[Dict[str, Any]],
                              output_dir: str) -> Dict[str, Any]:
        """
        Assemble video segments and transitions into a final composition.
        
        Args:
            segments: List of segment compositions
            transitions: List of transition compositions
            output_dir: Output directory
        
        Returns:
            Dictionary containing final composition data
        """
        try:
            # Create final composition directory
            final_dir = os.path.join(output_dir, "final")
            os.makedirs(final_dir, exist_ok=True)
            
            # Sort segments and transitions by index
            segments = sorted(segments, key=lambda x: x["section_idx"])
            transitions = sorted(transitions, key=lambda x: x["transition_idx"])
            
            # Interleave segments and transitions
            composition_elements = []
            
            # Add first segment
            if segments:
                composition_elements.append(segments[0])
            
            # Add alternating transitions and segments
            for i in range(len(transitions)):
                # Add transition
                composition_elements.append(transitions[i])
                
                # Add next segment if available
                if i + 1 < len(segments):
                    composition_elements.append(segments[i + 1])
            
            # Calculate total duration and frame count
            total_duration = sum(element["duration"] for element in composition_elements)
            total_frame_count = sum(element["frame_count"] for element in composition_elements)
            
            # Create final composition data
            final_composition = {
                "elements": composition_elements,
                "segment_count": len(segments),
                "transition_count": len(transitions),
                "total_duration": total_duration,
                "total_frame_count": total_frame_count,
                "composition_dir": final_dir,
                "fps": self.fps,
                "resolution": self.output_resolution
            }
            
            logger.info(f"Assembled final composition: {total_duration:.2f} seconds, " 
                       f"{total_frame_count} frames")
            
            return final_composition
            
        except Exception as e:
            logger.error(f"Error assembling video segments: {str(e)}")
            raise
    
    def add_transitions(self, 
                      segments: List[Dict[str, Any]], 
                      transition_type: str = "fade",
                      transition_duration: float = 1.0) -> List[Dict[str, Any]]:
        """
        Add transitions between video segments.
        
        Args:
            segments: List of video segments
            transition_type: Type of transition
            transition_duration: Duration of transition in seconds
        
        Returns:
            Updated list of video segments with transitions
        """
        # This method would add transition metadata between segments
        # For now, we'll return the original segments since transitions are
        # already handled in the animation generator
        
        return segments
    
    def create_final_composition(self, 
                               composition: Dict[str, Any], 
                               output_path: str) -> str:
        """
        Create the final video composition.
        
        Args:
            composition: Composition data
            output_path: Output path for the composition file
        
        Returns:
            Path to the final composition file
        """
        try:
            # In a real implementation, this would create a file describing the
            # composition for the video encoder to use
            
            # For now, just create a simple text file with composition info
            with open(output_path, "w") as f:
                f.write(f"Educational Video Composition\n")
                f.write(f"Resolution: {composition['resolution'][0]}x{composition['resolution'][1]}\n")
                f.write(f"FPS: {composition['fps']}\n")
                f.write(f"Duration: {composition['total_duration']:.2f} seconds\n")
                f.write(f"Segments: {composition['segment_count']}\n")
                f.write(f"Transitions: {composition['transition_count']}\n")
                f.write(f"Total Frames: {composition['total_frame_count']}\n")
                
                # Write segment info
                f.write("\nSegments:\n")
                for i, element in enumerate(composition['elements']):
                    if "section_idx" in element:
                        f.write(f"  Segment {element['section_idx']+1}: {element['duration']:.2f}s, " 
                               f"{element['frame_count']} frames\n")
                    elif "transition_idx" in element:
                        f.write(f"  Transition {element['transition_idx']+1}: {element['duration']:.2f}s, " 
                               f"{element['frame_count']} frames\n")
            
            logger.info(f"Created final composition file: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating final composition: {str(e)}")
            raise
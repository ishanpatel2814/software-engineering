#!/usr/bin/env python3
"""
Main entry point for the PDF/PPT to Educational Video Pipeline.
"""
import os
import sys
import time
from typing import Dict, Any

# Import configuration and utils
from config import Config, parse_arguments
from utils.logger import setup_logger, log_pipeline_progress
from utils.file_utils import validate_output_path, clean_temp_files

# Import pipeline modules
from input_processor.file_handler import FileHandler
from content_analyzer.text_analyzer import TextAnalyzer
from content_analyzer.visual_analyzer import VisualAnalyzer
from content_analyzer.content_organizer import ContentOrganizer
from script_generator.script_processor import ScriptGenerator
from audio_synthesizer.audio_processor import AudioProcessor
from animation_generator.animation_engine import AnimationEngine
from video_assembler.compositor import VideoCompositor
from video_assembler.encoder import VideoEncoder


def main():
    """Main pipeline function."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize configuration
    config = Config(args)
    
    # Setup logger
    logger = setup_logger(config.get("LOG_LEVEL"), config.get("LOG_FILE"))
    logger.info("Starting PDF/PPT to Educational Video Pipeline")
    
    try:
        # Validate API keys
        if not config.get("OPENAI_API_KEY"):
            logger.error("OpenAI API key is required")
            print("Error: OpenAI API key is required. Use --openai-key option.")
            return 1
        
        if not config.get("ELEVENLABS_API_KEY"):
            logger.error("ElevenLabs API key is required")
            print("Error: ElevenLabs API key is required. Use --elevenlabs-key option.")
            return 1
        
        # Validate input file
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            print(f"Error: Input file not found: {args.input}")
            return 1
        
        # Set output path if not provided
        if not args.output:
            input_name = os.path.splitext(os.path.basename(args.input))[0]
            args.output = os.path.join(
                config.get("DEFAULT_OUTPUT_DIR"), 
                f"{input_name}_video.{config.get('OUTPUT_FORMAT')}"
            )
        
        # Validate output path
        if not validate_output_path(args.output):
            logger.error(f"Invalid output path: {args.output}")
            print(f"Error: Invalid output path: {args.output}")
            return 1
        
        # Start pipeline execution
        logger.info(f"Processing input file: {args.input}")
        logger.info(f"Output will be saved to: {args.output}")
        
        # Initialize pipeline components
        file_handler = FileHandler(config)
        text_analyzer = TextAnalyzer(config)
        visual_analyzer = VisualAnalyzer(config)
        content_organizer = ContentOrganizer(config)
        script_generator = ScriptGenerator(config)
        audio_processor = AudioProcessor(config)
        animation_engine = AnimationEngine(config)
        video_compositor = VideoCompositor(config)
        video_encoder = VideoEncoder(config)
        
        # Execute pipeline
        
        # Step 1: Process input file
        log_pipeline_progress(logger, "Processing input file", 1, 8)
        content_data = file_handler.process_file(args.input)
        
        # Step 2: Analyze content
        log_pipeline_progress(logger, "Analyzing content", 2, 8)
        text_analysis = text_analyzer.analyze_content(content_data["text"])
        visual_analysis = visual_analyzer.analyze_content(content_data["visuals"])
        
        # Step 3: Organize content
        log_pipeline_progress(logger, "Organizing content structure", 3, 8)
        content_structure = content_organizer.create_content_flow(
            text_analysis, visual_analysis
        )
        
        # Step 4: Generate script
        log_pipeline_progress(logger, "Generating educational script", 4, 8)
        script = script_generator.generate_script(content_structure)
        
        # Step 5: Generate audio
        log_pipeline_progress(logger, "Synthesizing audio narration", 5, 8)
        audio_segments = audio_processor.process_audio(script)
        
        # Step 6: Generate animations
        log_pipeline_progress(logger, "Creating animations", 6, 8)
        animations = animation_engine.create_animations(
            content_data["visuals"], 
            content_structure,
            audio_segments
        )
        
        # Step 7: Compose video
        log_pipeline_progress(logger, "Composing video", 7, 8)
        video_composition = video_compositor.sync_audio_with_visuals(
            animations, audio_segments
        )
        
        # Step 8: Encode final video
        log_pipeline_progress(logger, "Encoding final video", 8, 8)
        video_encoder.encode_video(video_composition, args.output)
        
        # Cleanup
        log_pipeline_progress(logger, "Cleaning up temporary files", 8, 8)
        clean_temp_files(config.get("TEMP_DIR"))
        
        logger.info(f"Video successfully created: {args.output}")
        print(f"\nVideo successfully created: {args.output}")
        return 0
        
    except Exception as e:
        logger.exception(f"Error in pipeline execution: {str(e)}")
        print(f"\nError: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
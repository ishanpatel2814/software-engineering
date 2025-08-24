"""
File handler for processing input files in the PDF/PPT to Educational Video Pipeline.
"""
import os
import logging
from typing import Dict, Any, Optional

from utils.file_utils import get_file_extension
from input_processor.pdf_processor import PDFProcessor
from input_processor.ppt_processor import PPTProcessor

logger = logging.getLogger("edu_video_pipeline")


class FileHandler:
    """Handler for processing input files (PDF, PPT)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the file handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.pdf_processor = PDFProcessor(config)
        self.ppt_processor = PPTProcessor(config)
    
    def detect_file_type(self, file_path: str) -> str:
        """
        Detect the type of the input file.
        
        Args:
            file_path: Path to the input file
        
        Returns:
            File type ("pdf", "ppt", "pptx", or "unknown")
        """
        ext = get_file_extension(file_path)
        
        if ext == "pdf":
            return "pdf"
        elif ext in ["ppt", "pptx"]:
            return "ppt"
        else:
            return "unknown"
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file exists and is a supported type.
        
        Args:
            file_path: Path to the input file
        
        Returns:
            True if the file is valid, False otherwise
        """
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                pass
        except IOError:
            logger.error(f"Cannot read file: {file_path}")
            return False
        
        # Check file type
        file_type = self.detect_file_type(file_path)
        if file_type == "unknown":
            logger.error(f"Unsupported file type: {file_path}")
            return False
        
        return True
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process the input file and extract content.
        
        Args:
            file_path: Path to the input file
        
        Returns:
            Dictionary containing extracted content
        """
        # Validate file
        if not self.validate_file(file_path):
            raise ValueError(f"Invalid input file: {file_path}")
        
        # Detect file type
        file_type = self.detect_file_type(file_path)
        logger.info(f"Processing {file_type.upper()} file: {file_path}")
        
        # Process file based on type
        if file_type == "pdf":
            content = self._process_pdf(file_path)
        elif file_type == "ppt":
            content = self._process_ppt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        return content
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Process a PDF file.
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            Dictionary containing extracted content
        """
        # Extract text content
        text_content = self.pdf_processor.extract_text(file_path)
        
        # Extract images
        images = self.pdf_processor.extract_images(file_path)
        
        # Extract pages as images
        pages = self.pdf_processor.extract_pages(file_path)
        
        # Get metadata
        metadata = self.pdf_processor.get_metadata(file_path)
        
        # Combine content
        content = {
            "type": "pdf",
            "path": file_path,
            "metadata": metadata,
            "text": text_content,
            "visuals": {
                "pages": pages,
                "images": images
            }
        }
        
        return content
    
    def _process_ppt(self, file_path: str) -> Dict[str, Any]:
        """
        Process a PowerPoint file.
        
        Args:
            file_path: Path to the PowerPoint file
        
        Returns:
            Dictionary containing extracted content
        """
        # Extract text content
        text_content = self.ppt_processor.extract_text(file_path)
        
        # Extract slides as images
        slides = self.ppt_processor.extract_slides(file_path)
        
        # Extract notes
        notes = self.ppt_processor.extract_notes(file_path)
        
        # Get metadata
        metadata = self.ppt_processor.get_metadata(file_path)
        
        # Combine content
        content = {
            "type": "ppt",
            "path": file_path,
            "metadata": metadata,
            "text": text_content,
            "notes": notes,
            "visuals": {
                "slides": slides
            }
        }
        
        return content
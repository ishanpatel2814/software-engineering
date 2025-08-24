"""
File system utilities for the PDF/PPT to Educational Video Pipeline.
"""
import os
import shutil
import tempfile
import logging
from typing import Optional

logger = logging.getLogger("edu_video_pipeline")


def create_temp_directory(base_dir: str = "temp") -> str:
    """
    Create a temporary directory for processing files.
    
    Args:
        base_dir: Base directory for temporary files
    
    Returns:
        Path to the created temporary directory
    """
    os.makedirs(base_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp(dir=base_dir)
    logger.debug(f"Created temporary directory: {temp_dir}")
    return temp_dir


def clean_temp_files(directory: str) -> None:
    """
    Clean up temporary files from a directory.
    
    Args:
        directory: Directory to clean
    """
    if os.path.exists(directory) and os.path.isdir(directory):
        # Don't delete the base directory, just its contents
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.unlink(item_path)
                logger.debug(f"Removed temporary item: {item_path}")
            except Exception as e:
                logger.warning(f"Error removing temporary item {item_path}: {str(e)}")


def validate_output_path(output_path: str) -> bool:
    """
    Validate that the output path is valid and writable.
    
    Args:
        output_path: Output file path
    
    Returns:
        True if the output path is valid, False otherwise
    """
    try:
        # Check if directory exists or can be created
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Check if file can be written
        with open(output_path, 'a') as f:
            pass
        
        # If we got here, the path is valid
        return True
    except (IOError, OSError):
        return False


def get_file_extension(file_path: str) -> str:
    """
    Get the file extension from a file path.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File extension in lowercase without the dot
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower()[1:] if ext else ""
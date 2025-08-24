"""
PDF processor for extracting content from PDF files.
"""
import os
import logging
import fitz  # PyMuPDF
from PIL import Image
import io
import tempfile
from typing import Dict, List, Any, Tuple

from utils.file_utils import create_temp_directory

logger = logging.getLogger("edu_video_pipeline")


class PDFProcessor:
    """Processor for extracting content from PDF files."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the PDF processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.temp_dir = create_temp_directory(config.get("TEMP_DIR"))
    
    def extract_text(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            List of dictionaries containing text content per page
        """
        text_content = []
        
        try:
            # Open the PDF file
            doc = fitz.open(pdf_path)
            
            # Extract text from each page
            for page_num, page in enumerate(doc):
                # Extract text
                text = page.get_text()
                
                # Create a dictionary for this page's text content
                page_content = {
                    "page_num": page_num + 1,
                    "text": text,
                    "blocks": self._extract_text_blocks(page)
                }
                
                text_content.append(page_content)
            
            logger.info(f"Extracted text from {len(doc)} pages in PDF: {pdf_path}")
            
            # Close the document
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            raise
        
        return text_content
    
    def _extract_text_blocks(self, page) -> List[Dict[str, Any]]:
        """
        Extract text blocks from a PDF page.
        
        Args:
            page: PyMuPDF Page object
        
        Returns:
            List of dictionaries containing text block information
        """
        blocks = []
        
        # Extract text blocks
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                    block_text += "\n"
                
                # Create a dictionary for this text block
                block_dict = {
                    "text": block_text.strip(),
                    "bbox": block["bbox"],  # (x0, y0, x1, y1)
                    "type": "text"
                }
                
                blocks.append(block_dict)
        
        return blocks
    
    def extract_images(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            List of dictionaries containing image information
        """
        images = []
        
        try:
            # Open the PDF file
            doc = fitz.open(pdf_path)
            
            # Extract images from each page
            for page_num, page in enumerate(doc):
                # Get images
                img_list = page.get_images(full=True)
                
                for img_idx, img_info in enumerate(img_list):
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Create a temp file for the image
                    img_filename = f"page_{page_num+1}_img_{img_idx+1}.{base_image['ext']}"
                    img_path = os.path.join(self.temp_dir, img_filename)
                    
                    with open(img_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # Create a dictionary for this image
                    img_dict = {
                        "page_num": page_num + 1,
                        "img_idx": img_idx + 1,
                        "path": img_path,
                        "extension": base_image["ext"],
                        "width": base_image.get("width", 0),
                        "height": base_image.get("height", 0)
                    }
                    
                    images.append(img_dict)
            
            logger.info(f"Extracted {len(images)} images from PDF: {pdf_path}")
            
            # Close the document
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF {pdf_path}: {str(e)}")
            raise
        
        return images
    
    def extract_pages(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract pages as images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            List of dictionaries containing page image information
        """
        pages = []
        
        try:
            # Open the PDF file
            doc = fitz.open(pdf_path)
            
            # Convert each page to an image
            for page_num, page in enumerate(doc):
                # Render page to an image (higher resolution for better quality)
                zoom = 2.0  # Zoom factor for higher resolution
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Create a temp file for the page image
                page_filename = f"page_{page_num+1}.png"
                page_path = os.path.join(self.temp_dir, page_filename)
                
                # Save the image
                pix.save(page_path)
                
                # Create a dictionary for this page
                page_dict = {
                    "page_num": page_num + 1,
                    "path": page_path,
                    "width": pix.width,
                    "height": pix.height
                }
                
                pages.append(page_dict)
            
            logger.info(f"Extracted {len(pages)} page images from PDF: {pdf_path}")
            
            # Close the document
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting pages from PDF {pdf_path}: {str(e)}")
            raise
        
        return pages
    
    def get_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get metadata from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Dictionary containing PDF metadata
        """
        metadata = {}
        
        try:
            # Open the PDF file
            doc = fitz.open(pdf_path)
            
            # Get document metadata
            meta = doc.metadata
            
            # Convert to a regular dictionary
            metadata = {
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "subject": meta.get("subject", ""),
                "keywords": meta.get("keywords", ""),
                "creator": meta.get("creator", ""),
                "producer": meta.get("producer", ""),
                "page_count": len(doc),
                "file_size": os.path.getsize(pdf_path)
            }
            
            # Close the document
            doc.close()
            
        except Exception as e:
            logger.error(f"Error getting metadata from PDF {pdf_path}: {str(e)}")
            raise
        
        return metadata
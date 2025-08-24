"""
Content organizer for organizing content flow in the educational video.
"""
import os
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger("edu_video_pipeline")


class ContentOrganizer:
    """Organizer for creating a logical content flow for the educational video."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the content organizer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
    
    def create_content_flow(self, 
                           text_analysis: Dict[str, Any], 
                           visual_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a logical content flow from text and visual analyses.
        
        Args:
            text_analysis: Text analysis data
            visual_analysis: Visual analysis data
        
        Returns:
            Dictionary containing the content structure
        """
        logger.info("Creating content flow structure")
        
        # Extract sections from text analysis
        text_sections = text_analysis.get("sections", [])
        
        # Extract visual items from visual analysis
        visual_items = visual_analysis.get("items", [])
        
        # Map text sections to visual items
        content_mapping = self._map_sections_to_visuals(text_sections, visual_items)
        
        # Build relationships between sections
        relationships = self.map_relationships(content_mapping)
        
        # Create content structure
        content_structure = self.build_content_structure(content_mapping, relationships)
        
        logger.info(f"Created content flow with {len(content_structure['sections'])} sections")
        
        return content_structure
    
    def _map_sections_to_visuals(self, 
                               text_sections: List[Dict[str, Any]],
                               visual_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map text sections to visual items.
        
        Args:
            text_sections: List of text sections
            visual_items: List of visual items
        
        Returns:
            List of dictionaries containing mapped content
        """
        content_mapping = []
        
        # Determine the number of sections to create
        section_count = max(len(text_sections), len(visual_items))
        
        for idx in range(section_count):
            # Get text section if available
            text_section = text_sections[idx] if idx < len(text_sections) else None
            
            # Get visual item if available
            visual_item = visual_items[idx] if idx < len(visual_items) else None
            
            # Create section mapping
            section_mapping = {
                "index": idx,
                "text_section": text_section,
                "visual_item": visual_item
            }
            
            content_mapping.append(section_mapping)
        
        return content_mapping
    
    def map_relationships(self, content_mapping: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map relationships between content sections.
        
        Args:
            content_mapping: List of mapped content sections
        
        Returns:
            Dictionary containing relationship mappings
        """
        relationships = {
            "sequential": [],
            "prerequisite": [],
            "related": []
        }
        
        # If we have at least two sections, create sequential relationships
        for i in range(len(content_mapping) - 1):
            relationships["sequential"].append({
                "from_index": i,
                "to_index": i + 1,
                "type": "sequential"
            })
        
        # In a real implementation, this would use NLP techniques to identify
        # more complex relationships between sections
        # For now, return the sequential relationships
        
        return relationships
    
    def build_content_structure(self, 
                              content_mapping: List[Dict[str, Any]],
                              relationships: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the final content structure.
        
        Args:
            content_mapping: List of mapped content sections
            relationships: Relationship mappings
        
        Returns:
            Dictionary containing the content structure
        """
        # Create sections
        sections = []
        for mapping in content_mapping:
            # Get section data
            index = mapping["index"]
            text_section = mapping["text_section"]
            visual_item = mapping["visual_item"]
            
            # Skip if no text or visual content
            if not text_section and not visual_item:
                continue
            
            # Create section
            section = {
                "index": index,
                "title": self._get_section_title(text_section, visual_item),
                "text": self._get_section_text(text_section),
                "key_points": self._get_section_key_points(text_section),
                "visuals": self._get_section_visuals(visual_item)
            }
            
            sections.append(section)
        
        # Create content structure
        structure = {
            "title": self._get_content_title(sections),
            "sections": sections,
            "relationships": relationships
        }
        
        return structure
    
    def _get_section_title(self, 
                         text_section: Dict[str, Any], 
                         visual_item: Dict[str, Any]) -> str:
        """
        Get a title for a section.
        
        Args:
            text_section: Text section data
            visual_item: Visual item data
        
        Returns:
            Section title
        """
        # If text section has a title, use it
        if text_section and "title" in text_section:
            return text_section["title"]
        
        # If visual item has a title, use it
        if visual_item and "item" in visual_item:
            item = visual_item["item"]
            if "slide_num" in item:
                return f"Slide {item['slide_num']}"
            elif "page_num" in item:
                return f"Page {item['page_num']}"
        
        # Default title
        return "Untitled Section"
    
    def _get_section_text(self, text_section: Dict[str, Any]) -> str:
        """
        Get text content for a section.
        
        Args:
            text_section: Text section data
        
        Returns:
            Section text
        """
        if text_section and "text" in text_section:
            return text_section["text"]
        
        return ""
    
    def _get_section_key_points(self, text_section: Dict[str, Any]) -> List[str]:
        """
        Get key points for a section.
        
        Args:
            text_section: Text section data
        
        Returns:
            List of key points
        """
        if text_section and "key_points" in text_section:
            return text_section["key_points"]
        
        return []
    
    def _get_section_visuals(self, visual_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get visual content for a section.
        
        Args:
            visual_item: Visual item data
        
        Returns:
            Dictionary containing visual content
        """
        if not visual_item:
            return {}
        
        # Extract item and assets
        item = visual_item.get("item", {})
        assets = visual_item.get("assets", [])
        focus_areas = visual_item.get("focus_areas", [])
        
        # Create visuals dictionary
        visuals = {
            "path": item.get("path", ""),
            "assets": assets,
            "focus_areas": focus_areas
        }
        
        return visuals
    
    def _get_content_title(self, sections: List[Dict[str, Any]]) -> str:
        """
        Get a title for the overall content.
        
        Args:
            sections: List of content sections
        
        Returns:
            Content title
        """
        # If we have at least one section, use its title as a base
        if sections:
            first_section_title = sections[0]["title"]
            
            # If it's a slide or page title, use a more generic title
            if first_section_title.startswith("Slide ") or first_section_title.startswith("Page "):
                return "Educational Content"
            
            return first_section_title
        
        # Default title
        return "Educational Content"
"""
Text analyzer for analyzing content from PDF/PPT files.
"""
import os
import logging
import re
from typing import Dict, List, Any, Tuple

logger = logging.getLogger("edu_video_pipeline")


class TextAnalyzer:
    """Analyzer for text content from PDF/PPT files."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the text analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
    
    def analyze_content(self, text_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze text content from a document.
        
        Args:
            text_content: List of dictionaries containing text content
        
        Returns:
            Dictionary containing analysis results
        """
        logger.info("Analyzing text content")
        
        # Check if content is empty
        if not text_content:
            logger.warning("No text content to analyze")
            return {"sections": []}
        
        # Extract topics from content
        topics = self.identify_topics(text_content)
        
        # Extract key concepts
        key_concepts = self.extract_key_concepts(text_content)
        
        # Analyze structure
        structure = self.analyze_structure(text_content)
        
        # Calculate complexity
        complexity = self.calculate_complexity(text_content)
        
        # Combine results
        analysis = {
            "topics": topics,
            "key_concepts": key_concepts,
            "structure": structure,
            "complexity": complexity,
            "sections": []
        }
        
        # Create sections from content
        for idx, content in enumerate(text_content):
            section = {
                "index": idx,
                "title": self._extract_title(content),
                "text": content.get("text", ""),
                "key_points": self._extract_key_points(content),
                "complexity": self._calculate_section_complexity(content)
            }
            
            analysis["sections"].append(section)
        
        logger.info(f"Analyzed {len(text_content)} content items, " 
                   f"identified {len(topics)} topics and {len(key_concepts)} key concepts")
        
        return analysis
    
    def identify_topics(self, text_content: List[Dict[str, Any]]) -> List[str]:
        """
        Identify topics in the text content.
        
        Args:
            text_content: List of dictionaries containing text content
        
        Returns:
            List of identified topics
        """
        topics = set()
        
        # Extract text from each content item
        for content in text_content:
            text = content.get("text", "")
            
            # In a real implementation, this would use NLP techniques to identify topics
            # For now, use a simple heuristic approach
            
            # Split text into paragraphs
            paragraphs = text.split("\n\n")
            
            for paragraph in paragraphs:
                # Skip short paragraphs
                if len(paragraph) < 10:
                    continue
                
                # Extract potential topics (capitalized phrases)
                potential_topics = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', paragraph)
                
                for topic in potential_topics:
                    # Filter out common words and short topics
                    if len(topic) > 3 and topic not in ["The", "This", "That", "These", "Those"]:
                        topics.add(topic)
        
        return list(topics)
    
    def extract_key_concepts(self, text_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract key concepts from text content.
        
        Args:
            text_content: List of dictionaries containing text content
        
        Returns:
            List of dictionaries containing key concepts
        """
        key_concepts = []
        concept_set = set()
        
        # Extract text from each content item
        for idx, content in enumerate(text_content):
            text = content.get("text", "")
            
            # In a real implementation, this would use NLP techniques to extract key concepts
            # For now, use a simple heuristic approach
            
            # Look for patterns that suggest definitions or key concepts
            # For example: "X is defined as", "X refers to", "X is a"
            definition_patterns = [
                r'([A-Z][a-z]+(?:\s+[a-z]+)*) is defined as (.+?)\.',
                r'([A-Z][a-z]+(?:\s+[a-z]+)*) refers to (.+?)\.',
                r'([A-Z][a-z]+(?:\s+[a-z]+)*) is a (.+?)\.'
            ]
            
            for pattern in definition_patterns:
                matches = re.findall(pattern, text)
                
                for match in matches:
                    concept = match[0].strip()
                    definition = match[1].strip()
                    
                    # Skip if already added
                    if concept in concept_set:
                        continue
                    
                    # Add to key concepts
                    key_concepts.append({
                        "concept": concept,
                        "definition": definition,
                        "source_idx": idx
                    })
                    
                    concept_set.add(concept)
        
        return key_concepts
    
    def analyze_structure(self, text_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the structure of the text content.
        
        Args:
            text_content: List of dictionaries containing text content
        
        Returns:
            Dictionary containing structure analysis
        """
        # Analyze structure of content
        headings = []
        sections = []
        
        # Extract headings and sections
        for idx, content in enumerate(text_content):
            text = content.get("text", "")
            
            # Extract potential headings (lines that end with newline and don't end with period)
            lines = text.split("\n")
            
            for line_idx, line in enumerate(lines):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Check if line is a potential heading
                if (line_idx == 0 or not lines[line_idx - 1].strip()) and \
                   not line.endswith(".") and len(line) < 100:
                    headings.append({
                        "text": line,
                        "content_idx": idx,
                        "line_idx": line_idx
                    })
            
            # Extract sections (paragraphs)
            paragraphs = text.split("\n\n")
            
            for para_idx, paragraph in enumerate(paragraphs):
                paragraph = paragraph.strip()
                
                # Skip empty paragraphs
                if not paragraph:
                    continue
                
                sections.append({
                    "text": paragraph,
                    "content_idx": idx,
                    "paragraph_idx": para_idx
                })
        
        # Create structure analysis
        structure = {
            "headings": headings,
            "sections": sections,
            "heading_count": len(headings),
            "section_count": len(sections)
        }
        
        return structure
    
    def calculate_complexity(self, text_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate complexity metrics for the text content.
        
        Args:
            text_content: List of dictionaries containing text content
        
        Returns:
            Dictionary containing complexity metrics
        """
        # Extract all text
        all_text = ""
        for content in text_content:
            all_text += content.get("text", "") + "\n\n"
        
        # Calculate metrics
        word_count = len(re.findall(r'\w+', all_text))
        sentence_count = len(re.findall(r'[.!?]+', all_text))
        
        # Calculate average words per sentence
        words_per_sentence = word_count / max(1, sentence_count)
        
        # Calculate average word length
        total_word_length = sum(len(word) for word in re.findall(r'\w+', all_text))
        avg_word_length = total_word_length / max(1, word_count)
        
        # Calculate complexity level
        complexity_level = self._determine_complexity_level(words_per_sentence, avg_word_length)
        
        # Create complexity metrics
        complexity = {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "words_per_sentence": words_per_sentence,
            "avg_word_length": avg_word_length,
            "complexity_level": complexity_level
        }
        
        return complexity
    
    def _determine_complexity_level(self, words_per_sentence: float, avg_word_length: float) -> str:
        """
        Determine the complexity level based on metrics.
        
        Args:
            words_per_sentence: Average words per sentence
            avg_word_length: Average word length
        
        Returns:
            Complexity level ("low", "medium", "high")
        """
        # Simple heuristic for complexity level
        if words_per_sentence < 15 and avg_word_length < 4.5:
            return "low"
        elif words_per_sentence > 25 or avg_word_length > 5.5:
            return "high"
        else:
            return "medium"
    
    def _extract_title(self, content: Dict[str, Any]) -> str:
        """
        Extract a title from content.
        
        Args:
            content: Content dictionary
        
        Returns:
            Extracted title
        """
        text = content.get("text", "")
        
        # Try to find the first line that looks like a title
        lines = text.strip().split('\n')
        if lines:
            # Return the first non-empty line
            for line in lines:
                if line.strip():
                    # Limit title length
                    title = line.strip()
                    if len(title) > 50:
                        title = title[:47] + "..."
                    return title
        
        # Default title if none found
        if "page_num" in content:
            return f"Page {content['page_num']}"
        elif "slide_num" in content:
            return f"Slide {content['slide_num']}"
        else:
            return "Untitled Section"
    
    def _extract_key_points(self, content: Dict[str, Any]) -> List[str]:
        """
        Extract key points from content.
        
        Args:
            content: Content dictionary
        
        Returns:
            List of key points
        """
        text = content.get("text", "")
        key_points = []
        
        # Look for bullet points
        bullet_patterns = [
            r'•\s*(.*?)(?=\n|$)',
            r'-\s*(.*?)(?=\n|$)',
            r'(\d+\.)\s*(.*?)(?=\n|$)',
            r'(\*)\s*(.*?)(?=\n|$)'
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text)
            
            for match in matches:
                if isinstance(match, tuple):
                    # For patterns with capturing groups
                    point = match[-1].strip()
                else:
                    point = match.strip()
                
                if point and point not in key_points:
                    key_points.append(point)
        
        # If no bullet points found, try to extract short sentences
        if not key_points:
            sentences = re.split(r'[.!?]+', text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                # Skip empty or long sentences
                if not sentence or len(sentence) > 100:
                    continue
                
                # Skip sentences that are already part of a key point
                if any(sentence in point for point in key_points):
                    continue
                
                # Add as key point
                key_points.append(sentence)
                
                # Limit to 5 key points
                if len(key_points) >= 5:
                    break
        
        return key_points
    
    def _calculate_section_complexity(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate complexity metrics for a section.
        
        Args:
            content: Content dictionary
        
        Returns:
            Dictionary containing complexity metrics
        """
        text = content.get("text", "")
        
        # Calculate metrics
        word_count = len(re.findall(r'\w+', text))
        sentence_count = len(re.findall(r'[.!?]+', text))
        
        # Calculate average words per sentence
        words_per_sentence = word_count / max(1, sentence_count)
        
        # Calculate average word length
        total_word_length = sum(len(word) for word in re.findall(r'\w+', text))
        avg_word_length = total_word_length / max(1, word_count)
        
        # Calculate complexity level
        complexity_level = self._determine_complexity_level(words_per_sentence, avg_word_length)
        
        # Create complexity metrics
        complexity = {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "words_per_sentence": words_per_sentence,
            "avg_word_length": avg_word_length,
            "complexity_level": complexity_level
        }
        
        return complexity
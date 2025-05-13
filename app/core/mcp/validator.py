"""
Validator module for Multi-Component Prompting (MCP) framework.

This module defines tools for validating and analyzing prompt templates,
providing suggestions and improvements for better prompt engineering.
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Set, Optional
import nltk
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)

# Download required NLTK data (will only download if not already present)
try:
    nltk.download('punkt', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK data: {e}")


class PromptValidator:
    """Validator for prompt templates.
    
    Provides tools for validating, analyzing, and suggesting improvements
    for prompt templates in the MCP framework.
    """
    
    def __init__(self):
        """Initialize the prompt validator."""
        # Common patterns to look for in prompts
        self.role_patterns = [
            r"you are (?:a|an) (.+)",
            r"act as (?:a|an) (.+)",
            r"assume the role of (?:a|an) (.+)"
        ]
        
        self.instruction_patterns = [
            r"your task is to (.+)",
            r"you (need|have) to (.+)",
            r"please (.+)",
            r"(\w+) the following"
        ]
        
        self.output_format_patterns = [
            r"(format|respond|output|return)(.{0,30})(json|list|table|bullet)",
            r"use the (following|this) format",
            r"format[^\n]+(:|as follows)",
            r"respond (with|using|in)"
        ]
        
        # Common issues to check for
        self.problematic_phrases = [
            "as an AI", "as an assistant", "as an AI assistant", "as an AI language model",
            "I don't have personal", "I don't have the ability", "I cannot", "I don't have access",
            "I'm not able to", "I cannot browse", "I cannot access",
            "my training", "my knowledge", "my training data", "my training cutoff"
        ]
        
        # Template quality metrics
        self.min_template_length = 50
        self.max_template_length = 2000
        self.ideal_role_context_ratio = 0.2
        self.ideal_instruction_clarity_score = 0.7
        
    def validate_template(self, template: str) -> Tuple[bool, List[str], List[str]]:
        """Validate a prompt template and provide basic feedback.
        
        Args:
            template: The template text to validate.
            
        Returns:
            A tuple containing (is_valid, errors, warnings).
        """
        errors = []
        warnings = []
        
        # Check for empty template
        if not template or not template.strip():
            errors.append("Template cannot be empty")
            return False, errors, warnings
        
        # Check for minimum length
        if len(template.strip()) < self.min_template_length:
            warnings.append(f"Template is very short ({len(template.strip())} chars). Consider providing more context and instruction.")
        
        # Check for maximum length
        if len(template.strip()) > self.max_template_length:
            warnings.append(f"Template is very long ({len(template.strip())} chars). Consider breaking it into smaller components.")
        
        # Extract placeholders
        placeholder_pattern = r'\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}'
        placeholders = re.findall(placeholder_pattern, template)
        
        if not placeholders:
            warnings.append("Template contains no placeholders. Consider parameterizing for reusability.")
        
        # Check for unclosed braces
        open_count = template.count("{")
        close_count = template.count("}")
        if open_count != close_count:
            errors.append(f"Mismatched braces: {open_count} opening and {close_count} closing braces")
        
        # Check for invalid placeholder syntax
        invalid_placeholders = re.findall(r'\{([^a-zA-Z0-9_:{}].*?)\}', template)
        if invalid_placeholders:
            for invalid in invalid_placeholders:
                errors.append(f"Invalid placeholder syntax: {{{invalid}}}")
        
        # Check for potentially problematic whitespace
        whitespace_placeholders = re.findall(r'\{\s+([a-zA-Z0-9_]+)\s*\}', template)
        if whitespace_placeholders:
            for placeholder in whitespace_placeholders:
                warnings.append(f"Placeholder '{placeholder}' contains extra whitespace which may cause issues")
        
        # Check for duplicate placeholders with inconsistent formatting
        placeholder_set = set()
        for match in placeholders:
            var_name = match[0]
            is_optional = match[1] == 'optional'
            
            placeholder_key = f"{var_name}:{is_optional}"
            if placeholder_key in placeholder_set:
                continue
            
            opposite_key = f"{var_name}:{not is_optional}"
            if opposite_key in placeholder_set:
                warnings.append(f"Placeholder '{var_name}' is marked as both required and optional in different places")
                continue
            
            placeholder_set.add(placeholder_key)
        
        # Check for problematic phrases
        for phrase in self.problematic_phrases:
            if phrase.lower() in template.lower():
                warnings.append(f"Contains language about AI limitations ('{phrase}'). Consider rephrasing to focus on the task.")
        
        # Validation is successful if there are no errors
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def analyze_template(self, template: str) -> Dict[str, Any]:
        """Analyze a prompt template for quality and provide detailed feedback.
        
        Args:
            template: The template text to analyze.
            
        Returns:
            A dictionary containing analysis results and suggestions.
        """
        # Initial validation
        is_valid, errors, warnings = self.validate_template(template)
        
        # Initialize results
        results = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": [],
            "structure_analysis": {},
            "metrics": {},
            "improvement_areas": []
        }
        
        # If template is not valid, return early with just errors
        if not is_valid:
            return results
        
        # Structure analysis
        structure = self._analyze_structure(template)
        results["structure_analysis"] = structure
        
        # Check for missing components and provide suggestions
        if not structure.get("has_role_definition", False):
            results["suggestions"].append("Consider adding a clear role definition (e.g., 'You are a [ROLE]')")
            results["improvement_areas"].append("role_definition")
        
        if not structure.get("has_task_specification", False):
            results["suggestions"].append("Add a specific task description (e.g., 'Your task is to [TASK]')")
            results["improvement_areas"].append("task_specification")
        
        if not structure.get("has_output_format", False):
            results["suggestions"].append("Specify the expected output format for more consistent results")
            results["improvement_areas"].append("output_format")
        
        # Analyze complexity
        complexity = self._analyze_complexity(template)
        results["metrics"]["complexity"] = complexity
        
        if complexity["readability_score"] < 40:
            results["suggestions"].append("Simplify language for better clarity (current readability is low)")
            results["improvement_areas"].append("readability")
        
        if complexity["avg_sentence_length"] > 25:
            results["suggestions"].append("Consider breaking down long sentences for clarity")
            results["improvement_areas"].append("sentence_length")
        
        # Analyze tone and style
        tone = self._analyze_tone(template)
        results["metrics"]["tone"] = tone
        
        if tone["directive_score"] < 0.3:
            results["suggestions"].append("Use more directive language for clearer instructions")
            results["improvement_areas"].append("directiveness")
        
        # Check specific structural elements
        if not self._has_section_breaks(template):
            results["suggestions"].append("Add clear section breaks (e.g., using '---', headers, or numbered sections)")
            results["improvement_areas"].append("section_breaks")
        
        # Overall quality assessment
        quality_score = self._calculate_quality_score(structure, complexity, tone)
        results["metrics"]["overall_quality"] = quality_score
        
        if quality_score < 0.5:
            results["suggestions"].append("This template needs significant improvement in structure and clarity")
        elif quality_score < 0.7:
            results["suggestions"].append("This template could benefit from better structure and clearer instructions")
        elif quality_score < 0.9:
            results["suggestions"].append("This is a good template that could be improved with minor adjustments")
        else:
            results["suggestions"].append("This is an excellent, well-structured template")
        
        return results
    
    def _analyze_structure(self, template: str) -> Dict[str, Any]:
        """Analyze the structural components of a template.
        
        Args:
            template: The template text to analyze.
            
        Returns:
            A dictionary containing structural analysis results.
        """
        result = {
            "has_role_definition": False,
            "has_task_specification": False,
            "has_context_section": False,
            "has_output_format": False,
            "has_examples": False,
            "identified_sections": [],
            "placeholder_count": 0
        }
        
        # Check for role definition
        for pattern in self.role_patterns:
            if re.search(pattern, template, re.IGNORECASE):
                result["has_role_definition"] = True
                result["identified_sections"].append("role_definition")
                break
        
        # Check for task specification
        for pattern in self.instruction_patterns:
            if re.search(pattern, template, re.IGNORECASE):
                result["has_task_specification"] = True
                result["identified_sections"].append("task_specification")
                break
        
        # Check for context section
        if re.search(r"(context|background|information):", template, re.IGNORECASE):
            result["has_context_section"] = True
            result["identified_sections"].append("context_section")
        
        # Check for output format specification
        for pattern in self.output_format_patterns:
            if re.search(pattern, template, re.IGNORECASE):
                result["has_output_format"] = True
                result["identified_sections"].append("output_format")
                break
        
        # Check for examples
        if re.search(r"(example|for instance|e\.g\.)", template, re.IGNORECASE):
            result["has_examples"] = True
            result["identified_sections"].append("examples")
        
        # Count placeholders
        placeholder_pattern = r'\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}'
        placeholders = re.findall(placeholder_pattern, template)
        result["placeholder_count"] = len(placeholders)
        
        # Identify other common sections
        if re.search(r"(instruction|steps|procedure)s?:", template, re.IGNORECASE):
            result["identified_sections"].append("instructions")
        
        if re.search(r"(requirement|constraint)s?:", template, re.IGNORECASE):
            result["identified_sections"].append("requirements")
        
        if re.search(r"(guideline|rule)s?:", template, re.IGNORECASE):
            result["identified_sections"].append("guidelines")
        
        return result
    
    def _analyze_complexity(self, template: str) -> Dict[str, Any]:
        """Analyze the complexity of a template.
        
        Args:
            template: The template text to analyze.
            
        Returns:
            A dictionary containing complexity metrics.
        """
        # Remove placeholders to avoid skewing metrics
        clean_template = re.sub(r'\{[^}]*\}', '[PLACEHOLDER]', template)
        
        # Basic tokenization
        try:
            sentences = nltk.sent_tokenize(clean_template)
            words = nltk.word_tokenize(clean_template)
        except:
            # Fallback if NLTK fails
            sentences = clean_template.split('. ')
            words = clean_template.split()
        
        # Calculate metrics
        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(1, sentence_count)
        
        # Simple readability score (approximation of Flesch Reading Ease)
        long_words = sum(1 for word in words if len(word) > 6)
        long_word_percentage = long_words / max(1, word_count)
        
        # Higher is better (0-100 scale)
        readability_score = 100 - (avg_sentence_length * 0.85 + long_word_percentage * 70)
        readability_score = max(0, min(100, readability_score))
        
        # Repetition analysis
        word_counts = Counter(w.lower() for w in words if len(w) > 3)
        repeated_words = {word: count for word, count in word_counts.items() if count > 3}
        
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length,
            "readability_score": readability_score,
            "repeated_words": repeated_words
        }
    
    def _analyze_tone(self, template: str) -> Dict[str, Any]:
        """Analyze the tone and style of a template.
        
        Args:
            template: The template text to analyze.
            
        Returns:
            A dictionary containing tone analysis results.
        """
        # Remove placeholders to avoid skewing metrics
        clean_template = re.sub(r'\{[^}]*\}', '[PLACEHOLDER]', template)
        
        # Directive words (instructions, commands)
        directive_words = ["must", "should", "need to", "have to", "required", 
                           "ensure", "create", "analyze", "generate", "provide",
                           "list", "describe", "explain", "summarize", "identify"]
        
        directive_count = sum(clean_template.lower().count(word) for word in directive_words)
        
        # Question analysis
        questions = len(re.findall(r'\?', clean_template))
        
        # Passive voice approximation
        passive_indicators = ["is provided", "are provided", "was provided", "were provided",
                             "is shown", "are shown", "was shown", "were shown",
                             "is done", "are done", "was done", "were done"]
        
        passive_count = sum(clean_template.lower().count(phrase) for phrase in passive_indicators)
        
        # Calculate tone scores (0-1 scale)
        word_count = len(clean_template.split())
        directive_score = min(1.0, directive_count / max(10, word_count / 10))
        question_ratio = min(1.0, questions / max(5, word_count / 20))
        passive_ratio = min(1.0, passive_count / max(5, word_count / 20))
        
        # Overall clarity score
        clarity_score = 0.6 * directive_score + 0.2 * (1 - passive_ratio) + 0.2 * min(0.5, question_ratio)
        
        return {
            "directive_score": directive_score,
            "question_ratio": question_ratio,
            "passive_ratio": passive_ratio,
            "clarity_score": clarity_score
        }
    
    def _has_section_breaks(self, template: str) -> bool:
        """Check if the template has clear section breaks.
        
        Args:
            template: The template text to analyze.
            
        Returns:
            True if the template has section breaks, False otherwise.
        """
        # Check for markdown-style headers
        if re.search(r'^#+\s+\w+', template, re.MULTILINE):
            return True
        
        # Check for section delimiters
        if re.search(r'^-{3,}$|^={3,}$', template, re.MULTILINE):
            return True
        
        # Check for numbered sections
        if re.search(r'^\d+\.\s+\w+', template, re.MULTILINE):
            return True
        
        # Check for labeled sections
        if re.search(r'^[A-Za-z\s]+:$', template, re.MULTILINE):
            return True
        
        return False
    
    def _calculate_quality_score(self, structure: Dict[str, Any], 
                               complexity: Dict[str, Any],
                               tone: Dict[str, Any]) -> float:
        """Calculate an overall quality score for the template.
        
        Args:
            structure: Structure analysis results.
            complexity: Complexity analysis results.
            tone: Tone analysis results.
            
        Returns:
            Quality score between 0 and 1.
        """
        # Structure components weight
        structure_score = (
            (0.25 if structure["has_role_definition"] else 0) +
            (0.25 if structure["has_task_specification"] else 0) +
            (0.2 if structure["has_output_format"] else 0) +
            (0.15 if structure["has_context_section"] else 0) +
            (0.15 if structure["has_examples"] else 0)
        )
        
        # Normalize readability score to 0-1
        readability_score = complexity["readability_score"] / 100
        
        # Calculate final quality score with weights
        quality_score = (
            0.4 * structure_score +
            0.3 * readability_score +
            0.3 * tone["clarity_score"]
        )
        
        return quality_score
    
    def suggest_improvements(self, template: str) -> List[str]:
        """Suggest improvements for a prompt template.
        
        Args:
            template: The template text to improve.
            
        Returns:
            A list of improvement suggestions.
        """
        analysis = self.analyze_template(template)
        return analysis["suggestions"]
    
    def get_template_examples(self, task_type: Optional[str] = None) -> Dict[str, str]:
        """Get examples of well-structured templates for different tasks.
        
        Args:
            task_type: Optional task type to get specific examples for.
            
        Returns:
            A dictionary mapping task types to example templates.
        """
        examples = {
            "summarization": """You are a summarization expert. Your task is to create a concise summary of the following content.

Content to summarize:
{text}

Length: {length:optional}

Summary:
""",
            "analysis": """You are a content analyst specializing in {domain:optional}. Analyze the following content and extract key insights, patterns, and implications.

Content to analyze:
{text}

Analysis points to cover:
- Main themes and key concepts
- Supporting evidence and examples
- Implications and significance
- Areas for further exploration

Detailed analysis:
""",
            "classification": """You are a classification expert. Categorize the following content into the most appropriate category from this list: {categories}.

Content to classify:
{text}

For your classification, provide:
1. The selected category
2. A brief explanation of why this category is most appropriate
3. Confidence level (high/medium/low)

Classification:
""",
            "extraction": """Extract all relevant entities from the provided text. Focus on these entity types:
- People (names of individuals)
- Organizations (companies, institutions, agencies)
- Locations (places, addresses, regions)
- Dates and times
- Key concepts or terms

Text for extraction:
{text}

Format each entity type as a list with the entity and its position or context.

Extracted entities:
"""
        }
        
        if task_type and task_type in examples:
            return {task_type: examples[task_type]}
        
        return examples
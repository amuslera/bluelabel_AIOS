"""
Service provider for MCP components and related services.

This module provides a central location for accessing MCP components
and related services.
"""

import os
from typing import Dict, Any

from app.core.mcp import ComponentRegistry, ComponentEditor, ComponentTester
from app.core.model_router import ModelRouter

# Singleton instances
_component_registry = None
_component_editor = None
_component_tester = None
_model_router = None

def get_component_registry() -> ComponentRegistry:
    """Get the component registry singleton.
    
    Returns:
        The component registry instance.
    """
    global _component_registry
    
    if _component_registry is None:
        # Get storage directory from config or use default
        from app.core.config import get_config
        config = get_config()
        
        storage_dir = config.get("mcp", {}).get("storage_dir")
        
        # Initialize registry
        _component_registry = ComponentRegistry(storage_dir)
    
    return _component_registry

def get_component_editor() -> ComponentEditor:
    """Get the component editor singleton.
    
    Returns:
        The component editor instance.
    """
    global _component_editor
    
    if _component_editor is None:
        registry = get_component_registry()
        _component_editor = ComponentEditor(registry)
    
    return _component_editor

def get_model_router() -> ModelRouter:
    """Get the model router singleton.
    
    Returns:
        The model router instance.
    """
    global _model_router
    
    if _model_router is None:
        from app.core.model_router.router import ModelRouter
        
        # Initialize router
        _model_router = ModelRouter()
    
    return _model_router

def get_component_tester() -> ComponentTester:
    """Get the component tester singleton.
    
    Returns:
        The component tester instance.
    """
    global _component_tester
    
    if _component_tester is None:
        registry = get_component_registry()
        model_router = get_model_router()
        _component_tester = ComponentTester(registry, model_router)
    
    return _component_tester

def initialize_mcp_system(config: Dict[str, Any] = None) -> None:
    """Initialize the MCP system.
    
    This function initializes all MCP components and services.
    
    Args:
        config: Optional configuration dictionary.
    """
    # Force initialization of singletons
    get_component_registry()
    get_component_editor()
    get_model_router()
    get_component_tester()
    
    # Always load system components that the model router depends on
    _load_system_components()
    
    # Always load agent components
    _load_agent_components()

    # Load example components if needed
    if config and config.get("mcp", {}).get("load_examples", False):
        _load_example_components()

def _load_example_components() -> None:
    """Load example components into the registry."""
    registry = get_component_registry()
    editor = get_component_editor()
    
    # URL Content Summarization
    editor.create_component(
        name="URL Content Summarization",
        description="Summarizes content from a web article",
        template="You are summarizing a web article. Create a concise summary that captures the key points.\n\nArticle content:\n{text}\n\nSummary:",
        tags=["summarization", "content", "web", "example"],
        metadata={
            "example": True,
            "expected_inputs": {
                "text": "The article content to summarize"
            }
        }
    )
    
    # Entity Extraction
    editor.create_component(
        name="Entity Extraction",
        description="Extracts key entities from content",
        template="Extract key entities from the following content. Focus on people, organizations, products, concepts, and technologies.\nReturn the entities as a JSON object with categories as keys and arrays of entities as values.\n\nContent:\n{text}\n\nEntities (in JSON format):",
        tags=["extraction", "entities", "content", "example"],
        metadata={
            "example": True,
            "expected_inputs": {
                "text": "The content to extract entities from"
            },
            "output_format": "JSON"
        }
    )

def _load_system_components() -> None:
    """Load system components used by the ModelRouter."""
    editor = get_component_editor()
    
    # System prompt components
    editor.create_component(
        name="Summarization System Prompt",
        description="System prompt for summarization tasks",
        template="You are a precise summarization assistant. Your task is to create concise, accurate summaries of content that capture the key points and main message. Focus on the most important information and maintain the original meaning. Be clear, factual, and objective.",
        tags=["system", "summarization"],
        metadata={
            "system": True,
        },
        # Use a fixed ID for system components
        id="system_prompt_summarize"
    )
    
    editor.create_component(
        name="Entity Extraction System Prompt",
        description="System prompt for entity extraction tasks",
        template="You are an entity extraction assistant. Your task is to identify and categorize key entities mentioned in the content. Focus on people, organizations, products, concepts, and technologies. Format your output as a valid JSON object with categories as keys and arrays of entities as values. Do not include any explanatory text - only output the JSON object.",
        tags=["system", "entity-extraction"],
        metadata={
            "system": True,
        },
        id="system_prompt_extract_entities"
    )
    
    editor.create_component(
        name="Content Tagging System Prompt",
        description="System prompt for content tagging tasks",
        template="You are a content tagging assistant. Your task is to generate relevant tags for content that accurately represent the topics, themes, and subjects covered. Create 5-10 tags that would help categorize and discover this content. Return only a comma-separated list of tags without any explanations or additional text.",
        tags=["system", "tagging"],
        metadata={
            "system": True,
        },
        id="system_prompt_tag_content"
    )
    
    # Task prompt components
    editor.create_component(
        name="Summarization Task",
        description="Task prompt for summarization",
        template="Summarize the following content in a concise way that captures the key points:\n\n{text}\n\nSummary:",
        tags=["task", "summarization"],
        metadata={
            "system": True,
            "expected_inputs": {
                "text": "The content to summarize"
            }
        },
        id="task_summarize"
    )
    
    editor.create_component(
        name="Entity Extraction Task",
        description="Task prompt for entity extraction",
        template="Extract the key entities from the following content. Focus on people, organizations, products, concepts, and technologies.\nFormat the output as a JSON object with categories as keys and arrays of entities as values.\n\n{text}\n\nEntities (in JSON format):",
        tags=["task", "entity-extraction"],
        metadata={
            "system": True,
            "expected_inputs": {
                "text": "The content to extract entities from"
            },
            "output_format": "JSON"
        },
        id="task_extract_entities"
    )
    
    editor.create_component(
        name="Content Tagging Task",
        description="Task prompt for content tagging",
        template="Generate appropriate tags for the following content. Tags should be relevant keywords that categorize the content.\nReturn a comma-separated list of 5-10 tags.\n\n{text}\n\nTags:",
        tags=["task", "tagging"],
        metadata={
            "system": True,
            "expected_inputs": {
                "text": "The content to tag"
            }
        },
        id="task_tag_content"
    )

def _load_agent_components() -> None:
    """Load components used by agents."""
    editor = get_component_editor()
    
    # ContentMind components
    _load_contentmind_components(editor)

def _load_contentmind_components(editor: ComponentEditor) -> None:
    """Load components used by the ContentMind agent."""
    # ContentMind summarization component
    editor.create_component(
        name="ContentMind Summarization",
        description="Summarizes content for the ContentMind agent",
        template="You are the ContentMind agent, tasked with summarizing content to extract key information.\n\nPlease provide a concise summary that captures the main points, key facts, and core message of the content. Focus on extracting the most valuable information that would be useful to the user.\n\nContent to summarize:\n{text}\n\nSummary:",
        tags=["agent", "contentmind", "summarization"],
        metadata={
            "agent": "contentmind",
            "task": "summarize_content"
        },
        id="agent_contentmind_summarize"
    )
    
    # ContentMind entity extraction component
    editor.create_component(
        name="ContentMind Entity Extraction",
        description="Extracts entities for the ContentMind agent",
        template="You are the ContentMind agent, tasked with extracting entities from content.\n\nIdentify and categorize key entities mentioned in this content. Focus on people, organizations, products, concepts, locations, and technologies. Format your output as a valid JSON object with categories as keys and arrays of entities as values.\n\nContent for entity extraction:\n{text}\n\nEntities (in JSON format):",
        tags=["agent", "contentmind", "entity-extraction"],
        metadata={
            "agent": "contentmind",
            "task": "extract_entities",
            "output_format": "JSON"
        },
        id="agent_contentmind_extract_entities"
    )
    
    # ContentMind content tagging component
    editor.create_component(
        name="ContentMind Content Tagging",
        description="Tags content for the ContentMind agent",
        template="You are the ContentMind agent, tasked with generating relevant tags for content.\n\nCreate 5-10 tags that accurately represent the topics, themes, and subjects covered in this content. These tags will be used for organization, categorization, and discovery of this content in the knowledge repository.\n\nContent to tag:\n{text}\n\nTags (comma-separated):",
        tags=["agent", "contentmind", "tagging"],
        metadata={
            "agent": "contentmind",
            "task": "tag_content"
        },
        id="agent_contentmind_tag_content"
    )
    
    # ContentMind URL processing component
    editor.create_component(
        name="ContentMind URL Processing",
        description="Processes URLs for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing content from a URL.\n\nExtract the key information from this web content, focusing on the main text while ignoring navigation, advertisements, and other non-essential elements.\n\nURL content:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "url-processing"],
        metadata={
            "agent": "contentmind",
            "task": "process_url"
        },
        id="agent_contentmind_process_url"
    )
    
    # ContentMind PDF processing component
    editor.create_component(
        name="ContentMind PDF Processing",
        description="Processes PDFs for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing content from a PDF document.\n\nExtract the key information from this PDF content, organizing it in a way that preserves the document's structure while highlighting the most important information.\n\nPDF content:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "pdf-processing"],
        metadata={
            "agent": "contentmind",
            "task": "process_pdf"
        },
        id="agent_contentmind_process_pdf"
    )
    
    # ContentMind audio processing component
    editor.create_component(
        name="ContentMind Audio Processing",
        description="Processes audio transcriptions for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing content from an audio transcription.\n\nExamine this transcription and organize the content in a structured format. Identify speakers if possible, and focus on extracting the key points and main message.\n\nTranscription:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "audio-processing"],
        metadata={
            "agent": "contentmind",
            "task": "process_audio"
        },
        id="agent_contentmind_process_audio"
    )
    
    # ContentMind text processing component
    editor.create_component(
        name="ContentMind Text Processing",
        description="Processes text for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing raw text content.\n\nOrganize and structure this text to extract the core information and present it in a clear, concise format.\n\nRaw text:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "text-processing"],
        metadata={
            "agent": "contentmind",
            "task": "process_text"
        },
        id="agent_contentmind_process_text"
    )
    
    # ContentMind social media processing component
    editor.create_component(
        name="ContentMind Social Media Processing",
        description="Processes social media content for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing content from social media.\n\nAnalyze this social media content and extract the key information, including the main message, topic, sentiment, and any relevant context. For threads, maintain the conversation flow while highlighting the most important points.\n\nSocial media content:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "social-media-processing"],
        metadata={
            "agent": "contentmind",
            "task": "process_social"
        },
        id="agent_contentmind_process_social"
    )
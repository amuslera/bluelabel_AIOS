"""
Service provider for MCP components and related services.

This module provides a central location for accessing MCP components
and related services.
"""

import os
from typing import Dict, Any

from app.core.mcp import ComponentRegistry, ComponentEditor, ComponentTester

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

def get_model_router():
    """Get the model router singleton.

    Returns:
        The model router instance.
    """
    global _model_router

    if _model_router is None:
        from app.core.model_router.router import ModelRouter
        from app.core.config import get_config
        config = get_config()
        _model_router = ModelRouter(config.get("llm", {}))

    return _model_router

def get_component_tester() -> ComponentTester:
    """Get the component tester singleton.

    Returns:
        The component tester instance.
    """
    global _component_tester

    if _component_tester is None:
        registry = get_component_registry()
        # Import here to avoid circular imports
        router = get_model_router()
        _component_tester = ComponentTester(registry, router)

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
    registry = get_component_registry()

    def upsert_component(id, **kwargs):
        if registry.get_component(id) is not None:
            editor.update_component(
                component_id=id,
                name=kwargs.get("name"),
                description=kwargs.get("description"),
                template=kwargs.get("template"),
                tags=kwargs.get("tags"),
                metadata=kwargs.get("metadata"),
                increment_version=False
            )
        else:
            editor.create_component(id=id, **kwargs)

    # System prompt components
    upsert_component(
        id="system_prompt_summarize",
        name="Summarization System Prompt",
        description="System prompt for summarization tasks",
        template="You are a precise summarization assistant. Your task is to create concise, accurate summaries of content that capture the key points and main message. Focus on the most important information and maintain the original meaning. Be clear, factual, and objective.",
        tags=["system", "summarization"],
        metadata={"system": True}
    )
    upsert_component(
        id="system_prompt_extract_entities",
        name="Entity Extraction System Prompt",
        description="System prompt for entity extraction tasks",
        template="You are an entity extraction assistant. Your task is to identify and categorize key entities mentioned in the content. Focus on people, organizations, products, concepts, and technologies. Format your output as a valid JSON object with categories as keys and arrays of entities as values. Do not include any explanatory text - only output the JSON object.",
        tags=["system", "entity-extraction"],
        metadata={"system": True}
    )
    upsert_component(
        id="system_prompt_tag_content",
        name="Content Tagging System Prompt",
        description="System prompt for content tagging tasks",
        template="You are a content tagging assistant. Your task is to generate relevant tags for content that accurately represent the topics, themes, and subjects covered. Create 5-10 tags that would help categorize and discover this content. Return only a comma-separated list of tags without any explanations or additional text.",
        tags=["system", "tagging"],
        metadata={"system": True}
    )
    # Task prompt components
    upsert_component(
        id="task_summarize",
        name="Summarization Task",
        description="Task prompt for summarization",
        template="Summarize the following content in a concise way that captures the key points:\n\n{text}\n\nSummary:",
        tags=["task", "summarization"],
        metadata={"system": True, "expected_inputs": {"text": "The content to summarize"}}
    )
    upsert_component(
        id="task_extract_entities",
        name="Entity Extraction Task",
        description="Task prompt for entity extraction",
        template="Extract the key entities from the following content. Focus on people, organizations, products, concepts, and technologies.\nFormat the output as a JSON object with categories as keys and arrays of entities as values.\n\n{text}\n\nEntities (in JSON format):",
        tags=["task", "entity-extraction"],
        metadata={"system": True, "expected_inputs": {"text": "The content to extract entities from"}, "output_format": "JSON"}
    )
    upsert_component(
        id="task_tag_content",
        name="Content Tagging Task",
        description="Task prompt for content tagging",
        template="Generate appropriate tags for the following content. Tags should be relevant keywords that categorize the content.\nReturn a comma-separated list of 5-10 tags.\n\n{text}\n\nTags:",
        tags=["task", "tagging"],
        metadata={"system": True, "expected_inputs": {"text": "The content to tag"}}
    )

def _load_agent_components() -> None:
    """Load components used by agents."""
    editor = get_component_editor()
    
    # ContentMind components
    _load_contentmind_components(editor)

    # Researcher components
    _load_researcher_components(editor)
    
    # Gateway components
    _load_gateway_components(editor)

def _load_gateway_components(editor: ComponentEditor) -> None:
    """Load components used by the Gateway agent."""
    registry = get_component_registry()
    
    def upsert_component(id, **kwargs):
        if registry.get_component(id) is not None:
            editor.update_component(
                component_id=id,
                name=kwargs.get("name"),
                description=kwargs.get("description"),
                template=kwargs.get("template"),
                tags=kwargs.get("tags"),
                metadata=kwargs.get("metadata"),
                increment_version=False
            )
        else:
            editor.create_component(id=id, **kwargs)
    
    upsert_component(
        id="gateway_classify_content",
        name="Content Classification",
        description="Classifies content from various sources",
        template="""
        You are the Gateway agent responsible for classifying content from various sources.
        
        Examine the content below and determine:
        1. The content type (text, url, pdf, audio, image, etc.)
        2. Whether this appears to be a research query or content to be processed
        3. Which agent would be best to handle this content (contentmind or researcher)
        
        Content to classify:
        {content}
        
        Provide your classification in the following format:
        Content Type: [content type]
        Is Research Query: [yes/no]
        Recommended Agent: [contentmind/researcher]
        Reasoning: [brief explanation]
        """,
        tags=["agent", "gateway", "classification"],
        metadata={"agent": "gateway", "task": "classify_content"}
    )
    
    upsert_component(
        id="gateway_route_content",
        name="Content Routing",
        description="Routes content to appropriate agents",
        template="""
        You are the Gateway agent responsible for routing content to appropriate processing agents.
        
        Based on the content and its metadata, determine:
        1. Which agent should process this content (contentmind or researcher)
        2. Any special processing instructions for that agent
        
        Content metadata:
        {metadata}
        
        Content preview:
        {content_preview}
        
        Provide your routing decision in the following format:
        Target Agent: [contentmind/researcher]
        Processing Type: [content/query/research]
        Priority: [high/medium/low]
        Special Instructions: [any special processing instructions]
        Reasoning: [brief explanation of your decision]
        """,
        tags=["agent", "gateway", "routing"],
        metadata={"agent": "gateway", "task": "route_content"}
    )

def _load_researcher_components(editor: ComponentEditor) -> None:
    """Load components used by the Researcher agent."""
    registry = get_component_registry()

    def upsert_component(id, **kwargs):
        if registry.get_component(id) is not None:
            editor.update_component(
                component_id=id,
                name=kwargs.get("name"),
                description=kwargs.get("description"),
                template=kwargs.get("template"),
                tags=kwargs.get("tags"),
                metadata=kwargs.get("metadata"),
                increment_version=False
            )
        else:
            editor.create_component(id=id, **kwargs)

    upsert_component(
        id="research_query",
        name="Research Query",
        description="Guides the search for information on a topic",
        template="""
        You are a research assistant tasked with finding information about: {query}

        Please provide information from multiple sources about this topic. For each source,
        format your response as follows:

        Source: [Source Name]
        [Content from this source]

        Source: [Another Source Name]
        [Content from this source]

        Provide information from at least 3 different sources if possible.
        Be factual, accurate, and comprehensive.
        """,
        tags=["agent", "researcher", "search"],
        metadata={"agent": "researcher", "task": "research"}
    )

    upsert_component(
        id="research_synthesize",
        name="Research Synthesis",
        description="Synthesizes information from multiple sources",
        template="""
        You are a research synthesis expert tasked with creating a comprehensive summary
        based on the following query and search results:

        QUERY: {query}

        SEARCH RESULTS:
        {search_results}

        Please synthesize the information into a cohesive summary that addresses the query.
        Your synthesis should be well-structured and include:

        1. A comprehensive summary of the key information
        2. Important entities mentioned in the sources, categorized by type (people, organizations, locations, concepts, etc.)
        3. Relevant tags for this research

        Format your response as follows:

        [Summary of findings]

        Entities:
        People: [List people]
        Organizations: [List organizations]
        Locations: [List locations]
        Concepts: [List concepts]
        [Any other relevant entity categories]

        Tags: [comma-separated list of relevant tags]

        Be objective, accurate, and focused on the query.
        """,
        tags=["agent", "researcher", "synthesis"],
        metadata={"agent": "researcher", "task": "synthesize"}
    )

def _load_contentmind_components(editor: ComponentEditor) -> None:
    """Load components used by the ContentMind agent."""
    registry = get_component_registry()
    def upsert_component(id, **kwargs):
        if registry.get_component(id) is not None:
            editor.update_component(
                component_id=id,
                name=kwargs.get("name"),
                description=kwargs.get("description"),
                template=kwargs.get("template"),
                tags=kwargs.get("tags"),
                metadata=kwargs.get("metadata"),
                increment_version=False
            )
        else:
            editor.create_component(id=id, **kwargs)

    upsert_component(
        id="agent_contentmind_summarize",
        name="ContentMind Summarization",
        description="Summarizes content for the ContentMind agent",
        template="You are the ContentMind agent, tasked with summarizing content to extract key information.\n\nPlease provide a concise summary that captures the main points, key facts, and core message of the content. Focus on extracting the most valuable information that would be useful to the user.\n\nContent to summarize:\n{text}\n\nSummary:",
        tags=["agent", "contentmind", "summarization"],
        metadata={"agent": "contentmind", "task": "summarize_content"}
    )
    upsert_component(
        id="agent_contentmind_extract_entities",
        name="ContentMind Entity Extraction",
        description="Extracts entities for the ContentMind agent",
        template="You are the ContentMind agent, tasked with extracting entities from content.\n\nIdentify and categorize key entities mentioned in this content. Focus on people, organizations, products, concepts, locations, and technologies. Format your output as a valid JSON object with categories as keys and arrays of entities as values.\n\nContent for entity extraction:\n{text}\n\nEntities (in JSON format):",
        tags=["agent", "contentmind", "entity-extraction"],
        metadata={"agent": "contentmind", "task": "extract_entities", "output_format": "JSON"}
    )
    upsert_component(
        id="agent_contentmind_tag_content",
        name="ContentMind Content Tagging",
        description="Tags content for the ContentMind agent",
        template="You are the ContentMind agent, tasked with generating relevant tags for content.\n\nCreate 5-10 tags that accurately represent the topics, themes, and subjects covered in this content. These tags will be used for organization, categorization, and discovery of this content in the knowledge repository.\n\nContent to tag:\n{text}\n\nTags (comma-separated):",
        tags=["agent", "contentmind", "tagging"],
        metadata={"agent": "contentmind", "task": "tag_content"}
    )
    upsert_component(
        id="agent_contentmind_process_url",
        name="ContentMind URL Processing",
        description="Processes URLs for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing content from a URL.\n\nExtract the key information from this web content, focusing on the main text while ignoring navigation, advertisements, and other non-essential elements.\n\nURL content:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "url-processing"],
        metadata={"agent": "contentmind", "task": "process_url"}
    )
    upsert_component(
        id="agent_contentmind_process_pdf",
        name="ContentMind PDF Processing",
        description="Processes PDFs for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing content from a PDF document.\n\nExtract the key information from this PDF content, organizing it in a way that preserves the document's structure while highlighting the most important information.\n\nPDF content:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "pdf-processing"],
        metadata={"agent", "contentmind", "task": "process_pdf"}
    )
    upsert_component(
        id="agent_contentmind_process_audio",
        name="ContentMind Audio Processing",
        description="Processes audio transcriptions for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing content from an audio transcription.\n\nExamine this transcription and organize the content in a structured format. Identify speakers if possible, and focus on extracting the key points and main message.\n\nTranscription:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "audio-processing"],
        metadata={"agent": "contentmind", "task": "process_audio"}
    )
    upsert_component(
        id="agent_contentmind_process_text",
        name="ContentMind Text Processing",
        description="Processes text for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing raw text content.\n\nOrganize and structure this text to extract the core information and present it in a clear, concise format.\n\nRaw text:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "text-processing"],
        metadata={"agent": "contentmind", "task": "process_text"}
    )
    upsert_component(
        id="agent_contentmind_process_social",
        name="ContentMind Social Media Processing",
        description="Processes social media content for the ContentMind agent",
        template="You are the ContentMind agent, tasked with processing content from social media.\n\nAnalyze this social media content and extract the key information, including the main message, topic, sentiment, and any relevant context. For threads, maintain the conversation flow while highlighting the most important points.\n\nSocial media content:\n{text}\n\nProcessed content:",
        tags=["agent", "contentmind", "social-media-processing"],
        metadata={"agent": "contentmind", "task": "process_social"}
    )
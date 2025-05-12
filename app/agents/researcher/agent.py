# app/agents/researcher/agent.py
from typing import Dict, Any, List, Optional
import logging
import json
from app.agents.base.agent import BluelabelAgent, AgentTool
from app.core.model_router.router import ModelRouter

# Configure logging
logger = logging.getLogger(__name__)

class SearchTool(AgentTool):
    """Tool for searching information"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="searcher",
            description="Searches for information on a given topic"
        )
        self.model_router = model_router

    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Search for information based on a query"""
        logger.info(f"Searching for: {query}")
        
        # This is a mock implementation. In a real system, this would connect
        # to a search API or other information source.
        
        # Instead, we'll use the model router to generate a "search result"
        content = {"query": query}
        requirements = {
            "max_tokens": 500,
            "temperature": 0.2,
            "model": kwargs.get("model", None),
            "provider": kwargs.get("provider", None)
        }
        
        try:
            # Simulate search using an LLM
            result = await self.model_router.route_request("research", content, requirements)
            logger.info(f"Search completed with provider: {result.get('provider')}")
            return result
        except Exception as e:
            logger.error(f"Error in SearchTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error searching for information: {str(e)}"
            }

class SynthesisTool(AgentTool):
    """Tool for synthesizing information"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="synthesizer",
            description="Synthesizes information from multiple sources"
        )
        self.model_router = model_router

    async def execute(self, query: str, search_results: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Synthesize information from search results"""
        logger.info(f"Synthesizing information for: {query}")
        
        # Format search results for the model
        formatted_results = "\n\n".join([
            f"Source: {result.get('source', 'Unknown')}\n{result.get('content', '')}"
            for result in search_results
        ])
        
        # Prepare content for model router
        content = {
            "query": query,
            "search_results": formatted_results
        }
        
        requirements = {
            "max_tokens": 800,
            "temperature": 0.2,
            "model": kwargs.get("model", None),
            "provider": kwargs.get("provider", None)
        }
        
        try:
            # Use model router to synthesize information
            result = await self.model_router.route_request("synthesize", content, requirements)
            logger.info(f"Synthesis completed with provider: {result.get('provider')}")
            return result
        except Exception as e:
            logger.error(f"Error in SynthesisTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error synthesizing information: {str(e)}"
            }

class ResearcherAgent(BluelabelAgent):
    """Agent for conducting research and synthesizing information"""

    def __init__(self, config: Dict[str, Any], model_router: ModelRouter):
        self.model_router = model_router
        super().__init__(config)

    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent"""
        return [
            SearchTool(self.model_router),
            SynthesisTool(self.model_router)
        ]

    def _register_components(self) -> Dict[str, str]:
        """Register MCP components for Researcher agent tasks"""
        return {
            "research": "research_query",
            "synthesize": "research_synthesize"
        }
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a research request"""
        # Extract query from request
        query = request.get("query")
        if not query:
            return {
                "status": "error",
                "message": "Missing 'query' in request"
            }
        
        # Get provider preferences
        provider_preferences = request.get("provider_preferences", {})
        research_provider = provider_preferences.get("research", None)
        synthesis_provider = provider_preferences.get("synthesis", None)
        
        logger.info(f"Research query: {query}")
        logger.info(f"Provider preferences: {provider_preferences}")
        
        # Step 1: Search for information
        search_tool = next((t for t in self.tools if t.name == "searcher"), None)
        if not search_tool:
            return {"status": "error", "message": "Search tool not available"}
        
        search_result = await search_tool.execute(
            query=query,
            provider=research_provider
        )
        
        if search_result.get("status") != "success":
            return search_result
        
        # Mock search results (in a real system, these would come from external sources)
        # For demo purposes, we'll parse the LLM's response as if it contains multiple sources
        search_text = search_result.get("result", "")
        search_items = []
        
        # Split by source markers if present
        if "Source:" in search_text:
            parts = search_text.split("Source:")
            for part in parts[1:]:  # Skip the first empty part
                source, *content_parts = part.split("\n", 1)
                content = content_parts[0] if content_parts else ""
                search_items.append({
                    "source": source.strip(),
                    "content": content.strip()
                })
        else:
            # Just use the whole result as one source
            search_items = [{
                "source": "AI-generated",
                "content": search_text
            }]
        
        # Step 2: Synthesize information
        synthesis_tool = next((t for t in self.tools if t.name == "synthesizer"), None)
        if not synthesis_tool:
            return {"status": "error", "message": "Synthesis tool not available"}
        
        synthesis_result = await synthesis_tool.execute(
            query=query,
            search_results=search_items,
            provider=synthesis_provider
        )
        
        if synthesis_result.get("status") != "success":
            return synthesis_result
        
        # Prepare the final response
        # Extract entity and tag information if the synthesis includes them
        synthesis_text = synthesis_result.get("result", "")
        
        # Default empty structures
        entities = {}
        tags = []
        
        # Try to extract entities and tags from the synthesis
        # This is a simplified approach - in a real system, you'd use
        # more sophisticated entity extraction
        
        # Check if there's a section for entities
        if "Entities:" in synthesis_text:
            entity_section = synthesis_text.split("Entities:")[1].split("Tags:")[0].strip()
            entity_lines = entity_section.split("\n")
            current_category = "general"
            
            for line in entity_lines:
                line = line.strip()
                if not line:
                    continue
                
                if ":" in line and not line.startswith("- "):
                    # This is a category
                    current_category = line.rstrip(":").strip()
                    entities[current_category] = []
                elif line.startswith("- "):
                    # This is an entity
                    entity = line[2:].strip()
                    if current_category in entities:
                        entities[current_category].append(entity)
                    else:
                        entities[current_category] = [entity]
        
        # Check if there's a section for tags
        if "Tags:" in synthesis_text:
            tag_section = synthesis_text.split("Tags:")[1].strip()
            tag_text = tag_section.split("\n")[0].strip()
            tags = [tag.strip() for tag in tag_text.split(",")]
        
        # Extract summary - first part before any section headers
        summary = synthesis_text
        if "Entities:" in summary:
            summary = summary.split("Entities:")[0].strip()
        
        # Construct the response
        return {
            "status": "success",
            "content_type": "research",
            "original_content": query,
            "processed_content": {
                "title": f"Research: {query}",
                "summary": summary,
                "sources": search_items,
                "entities": entities,
                "tags": tags,
                "query": query
            },
            "providers_used": {
                "research": search_result.get("provider"),
                "synthesis": synthesis_result.get("provider")
            }
        }
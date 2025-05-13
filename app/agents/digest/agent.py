# app/agents/digest/agent.py
from typing import Dict, Any, List, Optional, Set, Tuple, Union
import logging
import json
import asyncio
from datetime import datetime, timedelta
import re

from app.agents.base.agent import BluelabelAgent, AgentTool
from app.core.model_router.router import ModelRouter

# Configure logging
logger = logging.getLogger(__name__)

class ContentRetrievalTool(AgentTool):
    """Tool for retrieving content from the knowledge repository"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="content_retriever",
            description="Retrieves content from the knowledge repository based on filters"
        )
        self.model_router = model_router
    
    async def execute(self, time_period: str = "day", content_types: Optional[List[str]] = None, 
                     tags: Optional[List[str]] = None, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """Retrieve content items from the knowledge repository
        
        Args:
            time_period: Options are "day", "week", "month", or "custom:<days>" (e.g., "custom:3")
            content_types: Optional list of content types to filter by
            tags: Optional list of tags to filter by
            limit: Maximum number of items to retrieve
            
        Returns:
            Dictionary with status and retrieved content items
        """
        try:
            # Import here to avoid circular imports
            import aiohttp
            from datetime import datetime, timedelta
            
            # Calculate date range based on time period
            end_date = datetime.now()
            
            if time_period == "day":
                start_date = end_date - timedelta(days=1)
            elif time_period == "week":
                start_date = end_date - timedelta(days=7)
            elif time_period == "month":
                start_date = end_date - timedelta(days=30)
            elif time_period.startswith("custom:"):
                try:
                    days = int(time_period.split(":", 1)[1])
                    start_date = end_date - timedelta(days=days)
                except ValueError:
                    logger.error(f"Invalid custom time period: {time_period}")
                    start_date = end_date - timedelta(days=1)
            else:
                # Default to one day
                start_date = end_date - timedelta(days=1)
            
            # Format dates as ISO strings
            date_range = f"{start_date.isoformat()},{end_date.isoformat()}"
            
            # Prepare API parameters
            params = {
                "limit": limit,
                "date_range": date_range
            }
            
            if content_types:
                # The API expects a single content type, so we'll need to make multiple requests
                all_results = []
                for content_type in content_types:
                    # Build parameters for this content type
                    type_params = params.copy()
                    type_params["content_type"] = content_type
                    
                    if tags:
                        type_params["tags"] = ",".join(tags)
                    
                    # Make the request
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"http://localhost:8080/knowledge/list", params=type_params) as response:
                            result = await response.json()
                            
                            if result.get("status") == "success":
                                all_results.extend(result.get("results", []))
            else:
                # No content type filter, make a single request
                if tags:
                    params["tags"] = ",".join(tags)
                
                # Make the request
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://localhost:8080/knowledge/list", params=params) as response:
                        result = await response.json()
                        
                        if result.get("status") == "success":
                            all_results = result.get("results", [])
                        else:
                            return {
                                "status": "error",
                                "message": result.get("message", "Failed to retrieve content")
                            }
            
            # Sort results by date (newest first)
            all_results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Limit the number of results
            all_results = all_results[:limit]
            
            return {
                "status": "success",
                "content_items": all_results,
                "count": len(all_results),
                "time_period": time_period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error in ContentRetrievalTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error retrieving content: {str(e)}"
            }

class ContentAnalysisTool(AgentTool):
    """Tool for analyzing content items and identifying patterns and connections"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="content_analyzer",
            description="Analyzes content items to identify patterns, connections, and themes"
        )
        self.model_router = model_router
    
    async def execute(self, content_items: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Analyze content items to identify patterns and connections

        Args:
            content_items: List of content items to analyze

        Returns:
            Analysis results including themes, connections, and recommendations
        """
        try:
            if not content_items:
                return {
                    "status": "success",
                    "message": "No content items to analyze",
                    "themes": [],
                    "connections": [],
                    "key_insights": [],
                    "item_analyses": []
                }

            # Extract metadata for analysis
            content_data = []
            for item in content_items:
                content_data.append({
                    "id": item.get("id"),
                    "title": item.get("title", "Untitled"),
                    "summary": item.get("summary", ""),
                    "content_type": item.get("content_type", "unknown"),
                    "tags": item.get("tags", []),
                    "entities": item.get("entities", {}),
                    "created_at": item.get("created_at", "")
                })

            # Analyze themes across content items
            themes = await self._identify_themes(content_data)

            # Identify connections between content items
            connections = await self._identify_connections(content_data)

            # Extract key insights
            key_insights = await self._extract_key_insights(content_data)

            # Perform detailed analysis on individual content items
            item_analyses = []
            # Limit to 3 most recent items to avoid excessive LLM usage
            for item in content_data[:3]:
                item_analysis = await self._analyze_content_item(item)
                if item_analysis:
                    item_analyses.append({
                        "item_id": item["id"],
                        "title": item["title"],
                        "analysis": item_analysis
                    })

            # Perform cross-reference analysis if we have multiple items
            cross_reference = None
            if len(content_data) >= 2:
                cross_reference = await self._cross_reference_content(content_data[:5])  # Limit to 5 items

            return {
                "status": "success",
                "themes": themes,
                "connections": connections,
                "key_insights": key_insights,
                "item_analyses": item_analyses,
                "cross_reference": cross_reference,
                "content_types": self._count_content_types(content_data),
                "popular_tags": self._identify_popular_tags(content_data)
            }

        except Exception as e:
            logger.error(f"Error in ContentAnalysisTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error analyzing content: {str(e)}"
            }
    
    async def _identify_themes(self, content_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify common themes across content items using LLM"""
        try:
            # Prepare data for LLM
            content_summary = []
            for item in content_data:
                content_summary.append(f"Title: {item['title']}\nTags: {', '.join(item['tags'])}\nSummary: {item['summary']}")
            
            all_content = "\n\n---\n\n".join(content_summary)
            
            # Use model router to identify themes
            themes_prompt = {
                "content": all_content,
                "num_items": len(content_data)
            }
            
            themes_result = await self.model_router.route_request(
                "identify_themes", 
                themes_prompt,
                {
                    "max_tokens": 800,
                    "temperature": 0.1
                }
            )
            
            # Parse themes from LLM response
            raw_themes = themes_result.get("result", "")
            
            # Extract themes in the format "Theme: description"
            themes = []
            theme_pattern = r"(?:Theme|Topic)\s*\d*\s*:\s*([^\n]+)"
            for match in re.finditer(theme_pattern, raw_themes):
                theme_text = match.group(1).strip()
                if theme_text:
                    themes.append({"name": theme_text})
            
            # If we couldn't extract structured themes, use a simpler approach
            if not themes:
                # Split by lines and look for lines that seem like themes
                for line in raw_themes.split("\n"):
                    line = line.strip()
                    # Skip empty lines and lines that are too short
                    if line and len(line) > 5 and ":" in line:
                        theme_name = line.split(":", 1)[1].strip()
                        if theme_name:
                            themes.append({"name": theme_name})
            
            # If we still don't have themes, use a fallback method
            if not themes:
                # Use tag frequency as themes
                tag_counts = {}
                for item in content_data:
                    for tag in item.get("tags", []):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Convert top tags to themes
                for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    themes.append({"name": tag, "source": "tag_frequency", "count": count})
            
            return themes
        
        except Exception as e:
            logger.error(f"Error identifying themes: {str(e)}")
            return []
    
    async def _identify_connections(self, content_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify connections between content items"""
        try:
            connections = []
            
            # Quick return if fewer than 2 items
            if len(content_data) < 2:
                return connections
            
            # Use model router to identify connections
            # Prepare samples of content pairs for analysis
            pairs_to_analyze = min(10, len(content_data) * (len(content_data) - 1) // 2)
            
            # Generate sample pairs
            import random
            sampled_pairs = []
            items_used = set()
            
            # If fewer than 5 items, analyze all pairs
            if len(content_data) <= 5:
                for i in range(len(content_data)):
                    for j in range(i + 1, len(content_data)):
                        sampled_pairs.append((content_data[i], content_data[j]))
            else:
                # Sample random pairs
                attempts = 0
                while len(sampled_pairs) < pairs_to_analyze and attempts < 100:
                    attempts += 1
                    i, j = random.sample(range(len(content_data)), 2)
                    pair_key = (min(i, j), max(i, j))
                    if pair_key not in items_used:
                        items_used.add(pair_key)
                        sampled_pairs.append((content_data[i], content_data[j]))
            
            # Format pairs for LLM processing
            formatted_pairs = []
            for item1, item2 in sampled_pairs:
                pair_data = f"""Item 1:
Title: {item1['title']}
Tags: {', '.join(item1['tags'])}
Summary: {item1['summary']}

Item 2:
Title: {item2['title']}
Tags: {', '.join(item2['tags'])}
Summary: {item2['summary']}
"""
                formatted_pairs.append({
                    "items": pair_data,
                    "item1_id": item1['id'],
                    "item2_id": item2['id']
                })
            
            # Process each pair to identify connections
            for pair in formatted_pairs:
                connection_prompt = {
                    "items": pair["items"]
                }
                
                connection_result = await self.model_router.route_request(
                    "identify_connection", 
                    connection_prompt,
                    {
                        "max_tokens": 300,
                        "temperature": 0.1
                    }
                )
                
                connection_text = connection_result.get("result", "")
                if connection_text and not connection_text.lower().startswith(("no connection", "none", "not related")):
                    connections.append({
                        "item1_id": pair["item1_id"],
                        "item2_id": pair["item2_id"],
                        "relationship": connection_text
                    })
            
            return connections
        
        except Exception as e:
            logger.error(f"Error identifying connections: {str(e)}")
            return []
    
    async def _extract_key_insights(self, content_data: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from content items"""
        try:
            # Prepare content for LLM
            content_summary = []
            for item in content_data:
                content_summary.append(f"Title: {item['title']}\nSummary: {item['summary']}")
            
            all_content = "\n\n---\n\n".join(content_summary)
            
            # Use model router to extract insights
            insight_prompt = {
                "content": all_content,
                "num_items": len(content_data)
            }
            
            insight_result = await self.model_router.route_request(
                "extract_insights", 
                insight_prompt,
                {
                    "max_tokens": 500,
                    "temperature": 0.1
                }
            )
            
            # Parse insights from LLM response
            raw_insights = insight_result.get("result", "")
            
            # Extract insights in bulleted format
            insights = []
            insight_pattern = r"(?:•|-|[0-9]+\.)\s*([^\n]+)"
            for match in re.finditer(insight_pattern, raw_insights):
                insight_text = match.group(1).strip()
                if insight_text:
                    insights.append(insight_text)
            
            # If we couldn't extract structured insights, use sentences
            if not insights:
                # Split by sentences (crude method)
                sentences = re.split(r'(?<=[.!?])\s+', raw_insights)
                insights = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            return insights
        
        except Exception as e:
            logger.error(f"Error extracting key insights: {str(e)}")
            return []
    
    def _count_content_types(self, content_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count occurrences of each content type"""
        type_counts = {}
        for item in content_data:
            content_type = item.get("content_type", "unknown")
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
        return type_counts
    
    def _identify_popular_tags(self, content_data: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
        """Identify popular tags across content items"""
        tag_counts = {}
        for item in content_data:
            for tag in item.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort by count (descending)
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_tags[:10]  # Return top 10 tags

    async def _analyze_content_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform detailed analysis on a single content item using LLM"""
        try:
            # Skip if we don't have enough content to analyze
            if not item.get("summary"):
                return None

            # Prepare the content for analysis
            content = f"""Title: {item['title']}
Summary: {item['summary']}
Tags: {', '.join(item['tags'])}
"""

            # Add entity information if available
            if item.get("entities"):
                content += "\nEntities:\n"
                for entity_type, entities in item["entities"].items():
                    if isinstance(entities, list) and entities:
                        content += f"{entity_type}: {', '.join(entities)}\n"
                    elif isinstance(entities, str):
                        content += f"{entity_type}: {entities}\n"

            # Use model router to analyze content
            analysis_prompt = {
                "content": content
            }

            analysis_result = await self.model_router.route_request(
                "content_analysis",
                analysis_prompt,
                {
                    "max_tokens": 800,
                    "temperature": 0.1
                }
            )

            # Return the raw analysis result
            return analysis_result.get("result", "")

        except Exception as e:
            logger.error(f"Error analyzing content item: {str(e)}")
            return None

    async def _cross_reference_content(self, content_data: List[Dict[str, Any]]) -> Optional[str]:
        """Cross-reference multiple content items to find connections and relationships"""
        try:
            if len(content_data) < 2:
                return None

            # Prepare the content items for cross-reference
            formatted_items = []
            for item in content_data:
                formatted_items.append(f"""Title: {item['title']}
Summary: {item['summary']}
Tags: {', '.join(item['tags'])}
Content Type: {item['content_type']}
Created: {item['created_at']}
"""
                )

            # Join all content items with separators
            all_content = "\n\n--- ITEM SEPARATOR ---\n\n".join(formatted_items)

            # Use model router to cross-reference content
            cross_ref_prompt = {
                "content_items": all_content
            }

            cross_ref_result = await self.model_router.route_request(
                "cross_reference",
                cross_ref_prompt,
                {
                    "max_tokens": 1200,
                    "temperature": 0.1
                }
            )

            # Return the raw cross-reference result
            return cross_ref_result.get("result", "")

        except Exception as e:
            logger.error(f"Error cross-referencing content: {str(e)}")
            return None

class DigestGenerationTool(AgentTool):
    """Tool for generating digests from content analysis"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="digest_generator",
            description="Generates daily, weekly, or custom period digests"
        )
        self.model_router = model_router
    
    async def execute(self, content_items: List[Dict[str, Any]], analysis_results: Dict[str, Any], 
                     digest_type: str = "daily", **kwargs) -> Dict[str, Any]:
        """Generate a digest based on content items and analysis results
        
        Args:
            content_items: List of content items
            analysis_results: Results from content analysis
            digest_type: Type of digest to generate ("daily", "weekly", or "custom")
            
        Returns:
            Generated digest content
        """
        try:
            # Check if we have content to digest
            if not content_items:
                return {
                    "status": "success",
                    "message": "No content items for digest",
                    "digest_html": "<p>No new content was added during this period.</p>",
                    "digest_text": "No new content was added during this period.",
                    "digest_type": digest_type,
                    "item_count": 0
                }
            
            # Prepare digest data
            digest_data = {
                "content_items": [
                    {
                        "id": item.get("id"),
                        "title": item.get("title", "Untitled"),
                        "summary": item.get("summary", ""),
                        "content_type": item.get("content_type", "unknown"),
                        "tags": item.get("tags", []),
                        "created_at": item.get("created_at", "")
                    }
                    for item in content_items
                ],
                "themes": analysis_results.get("themes", []),
                "connections": analysis_results.get("connections", []),
                "key_insights": analysis_results.get("key_insights", []),
                "item_analyses": analysis_results.get("item_analyses", []),
                "cross_reference": analysis_results.get("cross_reference"),
                "content_types": analysis_results.get("content_types", {}),
                "popular_tags": analysis_results.get("popular_tags", []),
                "digest_type": digest_type,
                "item_count": len(content_items),
                "date": datetime.now().strftime("%B %d, %Y")
            }
            
            # Generate digest content using LLM
            digest_prompt = {
                "digest_data": json.dumps(digest_data)
            }
            
            digest_result = await self.model_router.route_request(
                "generate_digest", 
                digest_prompt,
                {
                    "max_tokens": 2000,
                    "temperature": 0.2
                }
            )
            
            # Parse digest response
            raw_digest = digest_result.get("result", "")
            
            # Split HTML and text versions if provided
            html_digest = raw_digest
            text_digest = self._html_to_text(html_digest)
            
            # If the result doesn't contain HTML tags, format it
            if "<html>" not in raw_digest and "<body>" not in raw_digest:
                html_digest = self._format_digest_html(raw_digest, digest_data)
                text_digest = self._format_digest_text(raw_digest, digest_data)
            
            return {
                "status": "success",
                "digest_html": html_digest,
                "digest_text": text_digest,
                "digest_type": digest_type,
                "date": digest_data["date"],
                "item_count": len(content_items)
            }
        
        except Exception as e:
            logger.error(f"Error in DigestGenerationTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating digest: {str(e)}"
            }
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text (simplified version)"""
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', '', html_content)
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Replace HTML entities
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        return text.strip()
    
    def _format_digest_html(self, content: str, digest_data: Dict[str, Any]) -> str:
        """Format digest content as HTML"""
        # Create a basic HTML structure
        html = f"""
        <html>
        <head>
            <title>{digest_data['digest_type'].capitalize()} Digest - {digest_data['date']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; margin-top: 20px; }}
                h3 {{ color: #2980b9; }}
                ul {{ padding-left: 20px; }}
                .item {{ margin-bottom: 20px; border-left: 3px solid #3498db; padding-left: 15px; }}
                .tags {{ color: #7f8c8d; font-size: 0.9em; }}
                .footer {{ margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; font-size: 0.8em; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <h1>{digest_data['digest_type'].capitalize()} Digest - {digest_data['date']}</h1>
            <p>This digest contains {digest_data['item_count']} items added to your knowledge repository.</p>
            
            <h2>Key Insights</h2>
            <ul>
        """
        
        # Add insights
        for insight in digest_data['key_insights']:
            html += f"<li>{insight}</li>\n"
        
        html += """
            </ul>
            
            <h2>Common Themes</h2>
            <ul>
        """
        
        # Add themes
        for theme in digest_data['themes']:
            html += f"<li>{theme['name']}</li>\n"
        
        html += """
            </ul>
            
            <h2>Content Summary</h2>
        """
        
        # Add content items
        for item in digest_data['content_items']:
            html += f"""
            <div class="item">
                <h3>{item['title']}</h3>
                <p>{item['summary']}</p>
                <p class="tags">Type: {item['content_type'].upper()} | Tags: {', '.join(item['tags'])}</p>
            </div>
            """
        
        # Add connections if any
        if digest_data['connections']:
            html += """
            <h2>Content Connections</h2>
            <ul>
            """
            
            # Add up to 5 connections
            connection_count = min(5, len(digest_data['connections']))
            for i in range(connection_count):
                connection = digest_data['connections'][i]
                # Find the titles for the connected items
                item1 = next((item for item in digest_data['content_items'] if item['id'] == connection['item1_id']), None)
                item2 = next((item for item in digest_data['content_items'] if item['id'] == connection['item2_id']), None)
                
                if item1 and item2:
                    html += f"<li><strong>{item1['title']}</strong> and <strong>{item2['title']}</strong>: {connection['relationship']}</li>\n"
            
            html += """
            </ul>
            """
        
        # Add item analyses if available
        if digest_data.get('item_analyses'):
            html += """
            <h2>Detailed Analysis</h2>
            """

            for analysis in digest_data['item_analyses'][:3]:  # Limit to 3 analyses
                html += f"""
                <div class="item-analysis">
                    <h3>{analysis['title']} - Analysis</h3>
                    <div class="analysis-content">
                        {analysis['analysis']}
                    </div>
                </div>
                """

        # Add cross-reference analysis if available
        if digest_data.get('cross_reference'):
            html += f"""
            <h2>Cross-Reference Analysis</h2>
            <div class="cross-reference">
                {digest_data['cross_reference']}
            </div>
            """

        # Close HTML
        html += """
            <div class="footer">
                <p>Generated by Bluelabel AIOS Digest Agent</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _format_digest_text(self, content: str, digest_data: Dict[str, Any]) -> str:
        """Format digest content as plain text"""
        text = f"""
{digest_data['digest_type'].upper()} DIGEST - {digest_data['date']}

This digest contains {digest_data['item_count']} items added to your knowledge repository.

KEY INSIGHTS
-----------
"""
        
        # Add insights
        for insight in digest_data['key_insights']:
            text += f"- {insight}\n"
        
        text += """
COMMON THEMES
------------
"""
        
        # Add themes
        for theme in digest_data['themes']:
            text += f"- {theme['name']}\n"
        
        text += """
CONTENT SUMMARY
-------------
"""
        
        # Add content items
        for item in digest_data['content_items']:
            text += f"""
{item['title']}
{'-' * len(item['title'])}
{item['summary']}
Type: {item['content_type'].upper()} | Tags: {', '.join(item['tags'])}

"""
        
        # Add connections if any
        if digest_data['connections']:
            text += """
CONTENT CONNECTIONS
-----------------
"""
            
            # Add up to 5 connections
            connection_count = min(5, len(digest_data['connections']))
            for i in range(connection_count):
                connection = digest_data['connections'][i]
                # Find the titles for the connected items
                item1 = next((item for item in digest_data['content_items'] if item['id'] == connection['item1_id']), None)
                item2 = next((item for item in digest_data['content_items'] if item['id'] == connection['item2_id']), None)
                
                if item1 and item2:
                    text += f"- {item1['title']} and {item2['title']}: {connection['relationship']}\n"
        
        # Add item analyses if available
        if digest_data.get('item_analyses'):
            text += """
DETAILED ANALYSIS
----------------
"""
            for analysis in digest_data['item_analyses'][:2]:  # Limit to 2 analyses for text version
                text += f"""
{analysis['title']} - Analysis
{'-' * (len(analysis['title']) + 11)}
{analysis['analysis']}

"""

        # Add cross-reference if available (simplified version)
        if digest_data.get('cross_reference'):
            text += """
CROSS-REFERENCE ANALYSIS
-----------------------
"""
            # Extract just the key points from the cross-reference
            cross_ref = digest_data['cross_reference']

            # Simple attempt to format/clean cross-reference text
            # Split by common section headers and keep only the first few bullet points from each
            sections = cross_ref.split('\n\n')
            for section in sections[:3]:  # Limit to first 3 sections
                text += f"{section.strip()}\n\n"

        # Footer
        text += """
Generated by Bluelabel AIOS Digest Agent
"""
        
        return text

class EmailDeliveryTool(AgentTool):
    """Tool for delivering digests via email"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="email_delivery",
            description="Delivers digests via email"
        )
        self.model_router = model_router

    async def execute(self, recipient: str, subject: str, html_content: str, text_content: str, **kwargs) -> Dict[str, Any]:
        """Send a digest email

        Args:
            recipient: Email address to send to
            subject: Email subject
            html_content: HTML version of the email body
            text_content: Plain text version of the email body

        Returns:
            Status of the email sending operation
        """
        try:
            # Import here to avoid circular imports
            from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
            from app.services.gateway.email_settings import email_settings
            
            # Set up email configuration
            mail_config = ConnectionConfig(
                MAIL_USERNAME=email_settings.SMTP_USERNAME,
                MAIL_PASSWORD=email_settings.SMTP_PASSWORD,
                MAIL_FROM=email_settings.MAIL_FROM,
                MAIL_PORT=email_settings.SMTP_PORT,
                MAIL_SERVER=email_settings.SMTP_SERVER,
                MAIL_FROM_NAME=email_settings.MAIL_FROM_NAME,
                MAIL_STARTTLS=email_settings.SMTP_USE_TLS,
                MAIL_SSL_TLS=email_settings.SMTP_USE_SSL,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True
            )
            
            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=[recipient],
                body=text_content,
                html=html_content,
                subtype="html"
            )
            
            # Send the email
            fm = FastMail(mail_config)
            await fm.send_message(message)
            
            return {
                "status": "success",
                "message": f"Digest email sent to {recipient}",
                "recipient": recipient,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error in EmailDeliveryTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error sending digest email: {str(e)}"
            }

class WhatsAppDeliveryTool(AgentTool):
    """Tool for delivering digests via WhatsApp"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="whatsapp_delivery",
            description="Delivers digests via WhatsApp"
        )
        self.model_router = model_router
    
    async def execute(self, recipient: str, digest_text: str, **kwargs) -> Dict[str, Any]:
        """Send a digest via WhatsApp
        
        Args:
            recipient: WhatsApp ID or phone number to send to
            digest_text: Plain text version of the digest
            
        Returns:
            Status of the WhatsApp sending operation
        """
        try:
            # Import here to avoid circular imports
            from app.services.gateway.whatsapp_processor import WhatsAppProcessor
            
            # Initialize WhatsApp processor
            whatsapp = WhatsAppProcessor()
            
            # Format the message for WhatsApp (simplified version of the digest)
            formatted_text = self._format_for_whatsapp(digest_text)
            
            # Send the message
            result = await whatsapp.send_message(recipient, formatted_text)
            
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "message": f"Digest sent to WhatsApp recipient {recipient}",
                    "recipient": recipient,
                    "message_id": result.get("message_id"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "Failed to send WhatsApp message")
                }
        
        except Exception as e:
            logger.error(f"Error in WhatsAppDeliveryTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error sending digest via WhatsApp: {str(e)}"
            }
    
    def _format_for_whatsapp(self, digest_text: str) -> str:
        """Format digest text for WhatsApp (simpler formatting, emojis)"""
        # Split the digest into sections
        sections = re.split(r'\n+([A-Z -]+)\n+[-]+\n+', digest_text)
        
        # The first element is the header, the rest are section titles and content alternating
        formatted = sections[0].strip() + "\n\n"
        
        # Process sections
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_title = sections[i]
                section_content = sections[i + 1]
                
                # Add emoji based on section title
                emoji = "📊"  # Default
                if "INSIGHT" in section_title:
                    emoji = "💡"
                elif "THEME" in section_title:
                    emoji = "🔍"
                elif "SUMMARY" in section_title:
                    emoji = "📝"
                elif "CONNECTION" in section_title:
                    emoji = "🔗"
                
                # Format section
                formatted += f"{emoji} *{section_title}*\n"
                
                # Format content items
                content_items = section_content.strip().split("\n\n")
                for item in content_items:
                    # Remove dashes used for underlining
                    item = re.sub(r'\n[-]+\n', "\n", item)
                    # Format bullet points
                    item = item.replace("- ", "• ")
                    formatted += item.strip() + "\n\n"
        
        # Add footer
        formatted += "🤖 Generated by Bluelabel AIOS"
        
        return formatted


class DigestAgent(BluelabelAgent):
    """Agent for generating digests from knowledge repository content"""

    def __init__(self, config: Dict[str, Any], model_router: ModelRouter):
        self.model_router = model_router
        super().__init__(config)
        logger.info("Digest Agent initialized")

    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent"""
        from app.agents.digest.scheduling_tool import SchedulingTool

        return [
            ContentRetrievalTool(self.model_router),
            ContentAnalysisTool(self.model_router),
            DigestGenerationTool(self.model_router),
            EmailDeliveryTool(self.model_router),
            WhatsAppDeliveryTool(self.model_router),
            SchedulingTool(self.model_router)
        ]

    def _register_components(self) -> Dict[str, str]:
        """Register MCP components for Digest agent tasks"""
        return {
            "identify_themes": "digest_identify_themes",
            "identify_connection": "digest_identify_connection",
            "extract_insights": "digest_extract_insights",
            "generate_digest": "digest_generate",
            "content_analysis": "digest_content_analysis",
            "cross_reference": "digest_cross_reference"
        }
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a digest request"""
        action = request.get("action", "generate")
        
        if action == "retrieve":
            # Retrieve content from knowledge repository
            return await self._retrieve_content(request)
        
        elif action == "analyze":
            # Analyze content for patterns and connections
            return await self._analyze_content(request)
        
        elif action == "generate":
            # Generate a digest from content
            return await self._generate_digest(request)
        
        elif action == "deliver":
            # Deliver a digest to recipient
            return await self._deliver_digest(request)
        
        elif action == "schedule":
            # Schedule a digest delivery
            return await self._schedule_digest(request)
        
        elif action == "generate_and_deliver":
            # Generate and deliver a digest in one step
            return await self._generate_and_deliver(request)
        
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }
    
    async def _retrieve_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve content from knowledge repository"""
        content_retriever = next((t for t in self.tools if t.name == "content_retriever"), None)
        if not content_retriever:
            return {"status": "error", "message": "Content retrieval tool not available"}
        
        return await content_retriever.execute(
            time_period=request.get("time_period", "day"),
            content_types=request.get("content_types"),
            tags=request.get("tags"),
            limit=request.get("limit", 20)
        )
    
    async def _analyze_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content for patterns and connections"""
        content_analyzer = next((t for t in self.tools if t.name == "content_analyzer"), None)
        if not content_analyzer:
            return {"status": "error", "message": "Content analysis tool not available"}
        
        content_items = request.get("content_items", [])
        if not content_items:
            # If no items provided, try to retrieve them
            retrieve_result = await self._retrieve_content(request)
            if retrieve_result.get("status") == "success":
                content_items = retrieve_result.get("content_items", [])
        
        return await content_analyzer.execute(content_items=content_items)
    
    async def _generate_digest(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a digest from content and analysis"""
        digest_generator = next((t for t in self.tools if t.name == "digest_generator"), None)
        if not digest_generator:
            return {"status": "error", "message": "Digest generation tool not available"}
        
        # Get content items
        content_items = request.get("content_items", [])
        if not content_items:
            # If no items provided, try to retrieve them
            retrieve_result = await self._retrieve_content(request)
            if retrieve_result.get("status") == "success":
                content_items = retrieve_result.get("content_items", [])
        
        # Get analysis results
        analysis_results = request.get("analysis_results", {})
        if not analysis_results:
            # If no analysis provided, try to analyze
            analyze_result = await self._analyze_content({"content_items": content_items})
            if analyze_result.get("status") == "success":
                analysis_results = analyze_result
        
        return await digest_generator.execute(
            content_items=content_items,
            analysis_results=analysis_results,
            digest_type=request.get("digest_type", "daily")
        )
    
    async def _deliver_digest(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver a digest to a recipient"""
        recipient = request.get("recipient")
        if not recipient:
            return {"status": "error", "message": "Recipient is required for delivery"}
        
        digest_html = request.get("digest_html", "")
        digest_text = request.get("digest_text", "")
        if not digest_html and not digest_text:
            return {"status": "error", "message": "Digest content is required for delivery"}
        
        # Determine delivery method
        delivery_method = request.get("delivery_method")
        if not delivery_method:
            # Auto-detect based on recipient format
            if "@" in recipient:
                delivery_method = "email"
            else:
                delivery_method = "whatsapp"
        
        if delivery_method == "email":
            # Deliver via email
            email_delivery = next((t for t in self.tools if t.name == "email_delivery"), None)
            if not email_delivery:
                return {"status": "error", "message": "Email delivery tool not available"}
            
            subject = request.get("subject", f"{request.get('digest_type', 'Daily').capitalize()} Digest - {datetime.now().strftime('%B %d, %Y')}")
            
            return await email_delivery.execute(
                recipient=recipient,
                subject=subject,
                html_content=digest_html,
                text_content=digest_text
            )
        
        elif delivery_method == "whatsapp":
            # Deliver via WhatsApp
            whatsapp_delivery = next((t for t in self.tools if t.name == "whatsapp_delivery"), None)
            if not whatsapp_delivery:
                return {"status": "error", "message": "WhatsApp delivery tool not available"}
            
            return await whatsapp_delivery.execute(
                recipient=recipient,
                digest_text=digest_text
            )
        
        else:
            return {
                "status": "error",
                "message": f"Unknown delivery method: {delivery_method}"
            }
    
    async def _schedule_digest(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a digest delivery"""
        scheduler = next((t for t in self.tools if t.name == "scheduler"), None)
        if not scheduler:
            return {"status": "error", "message": "Scheduling tool not available"}

        # Pass all relevant parameters to the scheduler tool
        return await scheduler.execute(
            action=request.get("schedule_action", "schedule"),
            schedule_type=request.get("schedule_type", "daily"),
            time=request.get("time", "09:00"),
            recipient=request.get("recipient"),
            digest_type=request.get("digest_type", "daily"),
            content_types=request.get("content_types"),
            tags=request.get("tags"),
            task_id=request.get("task_id"),
            active=request.get("active", True),
            delivery_method=request.get("delivery_method")
        )
    
    async def _generate_and_deliver(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and deliver a digest in one step"""
        # Generate the digest
        generate_result = await self._generate_digest(request)
        if generate_result.get("status") != "success":
            return generate_result
        
        # Deliver the digest
        delivery_request = {
            "recipient": request.get("recipient"),
            "digest_html": generate_result.get("digest_html", ""),
            "digest_text": generate_result.get("digest_text", ""),
            "digest_type": request.get("digest_type", "daily"),
            "delivery_method": request.get("delivery_method")
        }
        
        delivery_result = await self._deliver_digest(delivery_request)
        
        # Combine results
        combined_result = {
            "status": delivery_result.get("status"),
            "digest_generated": generate_result.get("status") == "success",
            "digest_delivered": delivery_result.get("status") == "success",
            "message": delivery_result.get("message"),
            "recipient": request.get("recipient"),
            "digest_type": request.get("digest_type", "daily"),
            "item_count": generate_result.get("item_count", 0),
            "date": generate_result.get("date", datetime.now().strftime("%B %d, %Y"))
        }
        
        return combined_result
import unittest
import asyncio
import os
import sys
import json
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.registry.agent_registry import AgentRegistry, get_agent_registry
from app.agents.base.agent import BluelabelAgent
from app.core.model_router.router import ModelRouter
from app.agents.gateway.agent import GatewayAgent
from app.agents.digest.agent import DigestAgent


class TestDigestWorkflow(unittest.TestCase):
    """Integration tests for the complete digest workflow"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for the entire test class"""
        # Create a mock router and KnowledgeService
        cls.model_router = MagicMock(spec=ModelRouter)
        
        # Configure model_router to return useful responses
        cls.model_router.route_request = AsyncMock()
        cls.model_router.route_request.return_value = {"result": "Mock analysis result"}
        
        # Mock aiohttp ClientSession for API calls
        cls.session_mock = MagicMock()
        cls.session_mock.__aenter__ = AsyncMock(return_value=cls.session_mock)
        cls.session_mock.__aexit__ = AsyncMock(return_value=None)
        
        # Mock response for content retrieval
        cls.response_mock = AsyncMock()
        cls.response_mock.json = AsyncMock(return_value={
            "status": "success",
            "results": [
                {
                    "id": "test-item-1",
                    "title": "Test Content 1",
                    "summary": "This is a test content item for the digest workflow test.",
                    "content_type": "text",
                    "tags": ["test", "integration"],
                    "created_at": datetime.now().isoformat()
                }
            ]
        })
        cls.session_mock.get = AsyncMock(return_value=cls.response_mock)

    def setUp(self):
        """Set up test environment for each test"""
        # Create a fresh registry for each test
        self.registry = AgentRegistry()
        
        # Clear class-level registries
        AgentRegistry._agent_classes = {}
        AgentRegistry._agent_configs = {}
        
        # Register agent classes
        AgentRegistry.register_class("gateway", GatewayAgent)
        AgentRegistry.register_class("digest", DigestAgent)
        
        # Register agent configs
        AgentRegistry.register_config("gateway", {
            "id": "gateway",
            "name": "Gateway Agent",
            "description": "Routes content from various sources"
        })
        
        AgentRegistry.register_config("digest", {
            "id": "digest",
            "name": "Digest Agent",
            "description": "Generates content digests"
        })
        
        # Create agent instances
        self.gateway_agent = self.registry.create_agent("gateway", self.model_router)
        self.digest_agent = self.registry.create_agent("digest", self.model_router)

    @patch('aiohttp.ClientSession')
    @patch('app.services.gateway.email_processor.EmailProcessor.process_incoming')
    @patch('app.agents.digest.agent.EmailDeliveryTool.execute')
    def test_email_to_digest_workflow(self, mock_email_delivery, mock_email_processor, mock_session):
        """Test the complete workflow from email submission to digest creation"""
        # Configure mocks
        mock_session.return_value = self.session_mock
        mock_email_processor.return_value = {"status": "success"}
        mock_email_delivery.return_value = AsyncMock(return_value={"status": "success"})
        
        # 1. Create a sample email
        sample_email = {
            "sender": "user@example.com",
            "subject": "Test content for digest",
            "plain_text": "This is a test content item for the digest.",
            "html_content": "<p>This is a test content item for the digest.</p>",
            "date": datetime.now().isoformat(),
            "message_id": "test-email-123"
        }
        
        # 2. Process the email through the Gateway agent
        gateway_result = asyncio.run(self.gateway_agent.process_email(sample_email))
        
        # 3. Verify the email was processed successfully
        self.assertEqual(gateway_result["status"], "success")
        self.assertEqual(gateway_result["processed_by"], "contentmind")
        self.assertEqual(gateway_result["content_type"], "text")
        
        # 4. Create an on-demand digest
        digest_request = {
            "action": "generate",
            "digest_type": "daily",
            "time_period": "day"
        }
        
        digest_result = asyncio.run(self.digest_agent.process(digest_request))
        
        # 5. Verify the digest was created successfully
        self.assertEqual(digest_result["status"], "success")
        self.assertIn("digest_html", digest_result)
        self.assertIn("digest_text", digest_result)
        
        # 6. Deliver the digest
        delivery_request = {
            "action": "deliver",
            "recipient": "user@example.com",
            "digest_html": digest_result["digest_html"],
            "digest_text": digest_result["digest_text"],
            "delivery_method": "email"
        }
        
        delivery_result = asyncio.run(self.digest_agent.process(delivery_request))
        
        # 7. Verify the digest was delivered successfully
        self.assertEqual(delivery_result["status"], "success")

    @patch('aiohttp.ClientSession')
    @patch('app.agents.digest.scheduling_tool.SchedulingTool._schedule_task')
    def test_scheduled_digest_creation(self, mock_schedule_task, mock_session):
        """Test scheduled digest creation"""
        # Configure mocks
        mock_session.return_value = self.session_mock
        mock_schedule_task.return_value = AsyncMock()
        
        # 1. Schedule a digest
        schedule_request = {
            "action": "schedule",
            "schedule_action": "schedule",
            "schedule_type": "daily",
            "time": "09:00",
            "recipient": "user@example.com",
            "digest_type": "daily"
        }
        
        schedule_result = asyncio.run(self.digest_agent.process(schedule_request))
        
        # 2. Verify the digest was scheduled successfully
        self.assertEqual(schedule_result["status"], "success")
        self.assertIn("task_id", schedule_result)
        
        # 3. Simulate the scheduled execution
        generate_request = {
            "action": "generate_and_deliver",
            "digest_type": "daily",
            "recipient": "user@example.com",
            "delivery_method": "email"
        }
        
        generate_result = asyncio.run(self.digest_agent.process(generate_request))
        
        # 4. Verify the digest was generated and delivered successfully
        self.assertEqual(generate_result["status"], "success")
        self.assertTrue(generate_result["digest_generated"])
        self.assertTrue(generate_result["digest_delivered"])

    @patch('aiohttp.ClientSession')
    @patch('app.services.gateway.whatsapp_processor.WhatsAppProcessor.process_incoming')
    @patch('app.agents.digest.agent.WhatsAppDeliveryTool.execute')
    def test_whatsapp_to_digest_workflow(self, mock_whatsapp_delivery, mock_whatsapp_processor, mock_session):
        """Test the workflow from WhatsApp submission to digest creation"""
        # Configure mocks
        mock_session.return_value = self.session_mock
        mock_whatsapp_processor.return_value = {"status": "success"}
        mock_whatsapp_delivery.return_value = AsyncMock(return_value={"status": "success"})
        
        # 1. Create a sample WhatsApp message
        sample_message = {
            "from": "1234567890",
            "text": "This is a test content item from WhatsApp for the digest workflow test.",
            "timestamp": datetime.now().isoformat(),
            "message_id": "test-whatsapp-123"
        }
        
        # 2. Process the message through the Gateway agent
        gateway_result = asyncio.run(self.gateway_agent.process_whatsapp(sample_message))
        
        # 3. Verify the message was processed successfully
        self.assertEqual(gateway_result["status"], "success")
        self.assertEqual(gateway_result["processed_by"], "contentmind")
        self.assertEqual(gateway_result["content_type"], "text")
        
        # 4. Create and deliver a digest via WhatsApp
        digest_request = {
            "action": "generate_and_deliver",
            "digest_type": "daily",
            "time_period": "day",
            "recipient": "1234567890",
            "delivery_method": "whatsapp"
        }
        
        digest_result = asyncio.run(self.digest_agent.process(digest_request))
        
        # 5. Verify the digest was created and delivered successfully
        self.assertEqual(digest_result["status"], "success")
        self.assertTrue(digest_result["digest_generated"])
        self.assertTrue(digest_result["digest_delivered"])

    def test_digest_content_analysis(self):
        """Test the content analysis functionality of the digest agent"""
        # 1. Create sample content items
        content_items = [
            {
                "id": "test-item-1",
                "title": "Test Content 1",
                "summary": "This is a test content item about AI.",
                "content_type": "text",
                "tags": ["ai", "technology"],
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "test-item-2",
                "title": "Test Content 2",
                "summary": "This is another test content item about machine learning.",
                "content_type": "text",
                "tags": ["ml", "ai", "technology"],
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # 2. Create an analysis request
        analysis_request = {
            "action": "analyze",
            "content_items": content_items
        }
        
        # 3. Analyze the content
        analysis_result = asyncio.run(self.digest_agent.process(analysis_request))
        
        # 4. Verify the analysis was created successfully
        self.assertEqual(analysis_result["status"], "success")
        self.assertIn("themes", analysis_result)
        self.assertIn("connections", analysis_result)
        self.assertIn("key_insights", analysis_result)


if __name__ == "__main__":
    unittest.main()
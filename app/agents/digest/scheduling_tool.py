# app/agents/digest/scheduling_tool.py
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.agents.base.agent import AgentTool
from app.core.model_router.router import ModelRouter
from app.services.scheduler.scheduler_service import scheduler_service

# Configure logging
logger = logging.getLogger(__name__)

class SchedulingTool(AgentTool):
    """Tool for scheduling digest generation and delivery"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="scheduler",
            description="Schedules digest generation and delivery"
        )
        self.model_router = model_router
    
    async def execute(self, action: str, schedule_type: str = "daily", time: str = "09:00", 
                     recipient: str = None, digest_type: str = "daily", 
                     content_types: Optional[List[str]] = None,
                     tags: Optional[List[str]] = None,
                     **kwargs) -> Dict[str, Any]:
        """Schedule or manage digest generation and delivery
        
        Args:
            action: Action to perform ("schedule", "list", "cancel", "update")
            schedule_type: Type of schedule ("daily", "weekly", "monthly")
            time: Time to deliver the digest (HH:MM format)
            recipient: Email or WhatsApp recipient for delivery
            digest_type: Type of digest to generate ("daily", "weekly", "monthly", "custom")
            content_types: Optional list of content types to filter by
            tags: Optional list of tags to filter by
            
        Returns:
            Status of the scheduling operation
        """
        try:
            if action == "list":
                # List all scheduled digests
                return await scheduler_service.get_scheduled_digests(
                    active_only=kwargs.get("active_only", False)
                )
            
            elif action == "cancel":
                # Cancel a scheduled digest
                task_id = kwargs.get("task_id")
                if not task_id:
                    return {
                        "status": "error",
                        "message": "Task ID is required for cancellation"
                    }
                
                return await scheduler_service.cancel_scheduled_digest(task_id)
            
            elif action == "update":
                # Update a scheduled digest
                task_id = kwargs.get("task_id")
                if not task_id:
                    return {
                        "status": "error",
                        "message": "Task ID is required for updating"
                    }
                
                # Create update data
                update_data = {}
                if schedule_type:
                    update_data["schedule_type"] = schedule_type
                if time:
                    update_data["time"] = time
                if recipient:
                    update_data["recipient"] = recipient
                if digest_type:
                    update_data["digest_type"] = digest_type
                if content_types is not None:
                    update_data["content_types"] = content_types
                if tags is not None:
                    update_data["tags"] = tags
                if "active" in kwargs:
                    update_data["active"] = kwargs["active"]
                
                return await scheduler_service.update_scheduled_digest(task_id, update_data)
            
            elif action == "schedule":
                # Schedule a new digest task
                if not recipient:
                    return {
                        "status": "error",
                        "message": "Recipient is required for scheduling"
                    }
                
                # Parse time
                try:
                    hour, minute = map(int, time.split(":"))
                    if not (0 <= hour < 24 and 0 <= minute < 60):
                        raise ValueError("Invalid time format")
                except ValueError:
                    return {
                        "status": "error",
                        "message": f"Invalid time format: {time}. Use HH:MM format."
                    }
                
                # Determine delivery method
                delivery_method = kwargs.get("delivery_method")
                if not delivery_method:
                    # Auto-detect based on recipient format
                    if "@" in recipient:
                        delivery_method = "email"
                    else:
                        delivery_method = "whatsapp"
                
                # Create schedule data
                schedule_data = {
                    "schedule_type": schedule_type,
                    "time": time,
                    "recipient": recipient,
                    "delivery_method": delivery_method,
                    "digest_type": digest_type,
                    "content_types": content_types,
                    "tags": tags,
                }
                
                # Use the scheduler service to schedule the task
                return await scheduler_service.schedule_digest(schedule_data)
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}"
                }
        
        except Exception as e:
            logger.error(f"Error in SchedulingTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error scheduling digest: {str(e)}"
            }
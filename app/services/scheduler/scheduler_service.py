# app/services/scheduler/scheduler_service.py
from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio
import logging
from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.repositories.scheduler_repository import SchedulerRepository
from app.db.schema.scheduler import ScheduledDigest

# Configure logging
logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for scheduling and managing timed tasks"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton implementation"""
        if cls._instance is None:
            cls._instance = super(SchedulerService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the scheduler service"""
        if not self._initialized:
            self._initialized = True
            self._running_tasks = {}  # Task ID -> asyncio.Task
            self._callback_registry = {}  # task_type -> callback function
            self._scheduler_running = False
            self._scheduler_task = None
    
    def register_callback(self, task_type: str, callback: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]):
        """Register a callback function for a task type
        
        Args:
            task_type: Type of task (e.g., "digest_daily")
            callback: Async function to call when task is triggered
        """
        self._callback_registry[task_type] = callback
        logger.info(f"Registered callback for task type: {task_type}")
    
    async def start(self):
        """Start the scheduler main loop"""
        if self._scheduler_running:
            logger.warning("Scheduler is already running")
            return
        
        self._scheduler_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler service started")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self._scheduler_running:
            logger.warning("Scheduler is not running")
            return
        
        self._scheduler_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
        
        # Cancel all running tasks
        for task_id, task in list(self._running_tasks.items()):
            if not task.done():
                task.cancel()
        
        logger.info("Scheduler service stopped")
    
    async def schedule_digest(self, digest_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a new digest
        
        Args:
            digest_data: Digest configuration
            
        Returns:
            Result of the scheduling operation
        """
        # Create the scheduled digest in the database
        db = SessionLocal()
        try:
            scheduler_repo = SchedulerRepository(db)
            scheduled_digest = scheduler_repo.create_scheduled_digest(digest_data)
            
            # Check if we need to schedule it immediately
            now = datetime.now()
            if scheduled_digest.next_run and scheduled_digest.next_run <= now + timedelta(minutes=15):
                # Schedule it to run soon
                task = asyncio.create_task(self._run_task_at_time(
                    scheduled_digest.id,
                    f"digest_{scheduled_digest.digest_type}",
                    scheduled_digest.next_run,
                    {
                        "digest_id": scheduled_digest.id,
                        "digest_type": scheduled_digest.digest_type,
                        "recipient": scheduled_digest.recipient,
                        "delivery_method": scheduled_digest.delivery_method,
                        "content_types": scheduled_digest.content_types.split(",") if scheduled_digest.content_types else None,
                        "tags": scheduled_digest.tags.split(",") if scheduled_digest.tags else None,
                    }
                ))
                self._running_tasks[scheduled_digest.id] = task
            
            return {
                "status": "success",
                "message": f"Digest {scheduled_digest.schedule_type} scheduled successfully",
                "digest_id": scheduled_digest.id,
                "next_run": scheduled_digest.next_run.isoformat() if scheduled_digest.next_run else None
            }
        
        except Exception as e:
            logger.error(f"Error scheduling digest: {str(e)}")
            return {
                "status": "error",
                "message": f"Error scheduling digest: {str(e)}"
            }
        finally:
            db.close()
    
    async def update_scheduled_digest(self, digest_id: str, digest_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a scheduled digest
        
        Args:
            digest_id: ID of the digest to update
            digest_data: Updated digest configuration
            
        Returns:
            Result of the update operation
        """
        db = SessionLocal()
        try:
            scheduler_repo = SchedulerRepository(db)
            updated_digest = scheduler_repo.update_scheduled_digest(digest_id, digest_data)
            
            if not updated_digest:
                return {
                    "status": "error",
                    "message": f"Scheduled digest with ID {digest_id} not found"
                }
            
            # Cancel and reschedule if already running
            if digest_id in self._running_tasks and not self._running_tasks[digest_id].done():
                self._running_tasks[digest_id].cancel()
            
            # Check if we need to schedule it immediately
            now = datetime.now()
            if updated_digest.active and updated_digest.next_run and updated_digest.next_run <= now + timedelta(minutes=15):
                # Schedule it to run soon
                task = asyncio.create_task(self._run_task_at_time(
                    updated_digest.id,
                    f"digest_{updated_digest.digest_type}",
                    updated_digest.next_run,
                    {
                        "digest_id": updated_digest.id,
                        "digest_type": updated_digest.digest_type,
                        "recipient": updated_digest.recipient,
                        "delivery_method": updated_digest.delivery_method,
                        "content_types": updated_digest.content_types.split(",") if updated_digest.content_types else None,
                        "tags": updated_digest.tags.split(",") if updated_digest.tags else None,
                    }
                ))
                self._running_tasks[updated_digest.id] = task
            
            return {
                "status": "success",
                "message": f"Scheduled digest {digest_id} updated successfully",
                "digest_id": updated_digest.id,
                "next_run": updated_digest.next_run.isoformat() if updated_digest.next_run else None
            }
        
        except Exception as e:
            logger.error(f"Error updating scheduled digest: {str(e)}")
            return {
                "status": "error",
                "message": f"Error updating scheduled digest: {str(e)}"
            }
        finally:
            db.close()
    
    async def cancel_scheduled_digest(self, digest_id: str) -> Dict[str, Any]:
        """Cancel a scheduled digest
        
        Args:
            digest_id: ID of the digest to cancel
            
        Returns:
            Result of the cancellation operation
        """
        db = SessionLocal()
        try:
            scheduler_repo = SchedulerRepository(db)
            result = scheduler_repo.deactivate_scheduled_digest(digest_id)
            
            if not result:
                return {
                    "status": "error",
                    "message": f"Scheduled digest with ID {digest_id} not found"
                }
            
            # Cancel running task if exists
            if digest_id in self._running_tasks and not self._running_tasks[digest_id].done():
                self._running_tasks[digest_id].cancel()
                del self._running_tasks[digest_id]
            
            return {
                "status": "success",
                "message": f"Scheduled digest {digest_id} cancelled successfully",
                "digest_id": digest_id
            }
        
        except Exception as e:
            logger.error(f"Error cancelling scheduled digest: {str(e)}")
            return {
                "status": "error",
                "message": f"Error cancelling scheduled digest: {str(e)}"
            }
        finally:
            db.close()
    
    async def get_scheduled_digests(self, active_only: bool = False) -> Dict[str, Any]:
        """Get all scheduled digests
        
        Args:
            active_only: If True, only return active digests
            
        Returns:
            List of scheduled digests
        """
        db = SessionLocal()
        try:
            scheduler_repo = SchedulerRepository(db)
            digests = scheduler_repo.get_all_scheduled_digests(active_only)
            
            result = []
            for digest in digests:
                result.append({
                    "id": digest.id,
                    "schedule_type": digest.schedule_type,
                    "time": digest.time,
                    "recipient": digest.recipient,
                    "delivery_method": digest.delivery_method,
                    "digest_type": digest.digest_type,
                    "content_types": digest.content_types.split(",") if digest.content_types else [],
                    "tags": digest.tags.split(",") if digest.tags else [],
                    "active": digest.active,
                    "last_run": digest.last_run.isoformat() if digest.last_run else None,
                    "next_run": digest.next_run.isoformat() if digest.next_run else None
                })
            
            return {
                "status": "success",
                "scheduled_digests": result,
                "count": len(result)
            }
        
        except Exception as e:
            logger.error(f"Error getting scheduled digests: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting scheduled digests: {str(e)}"
            }
        finally:
            db.close()
    
    async def _scheduler_loop(self):
        """Main scheduler loop that checks for due tasks"""
        try:
            logger.info("Scheduler loop started")
            
            while self._scheduler_running:
                try:
                    # Get due tasks from database
                    db = SessionLocal()
                    scheduler_repo = SchedulerRepository(db)
                    due_tasks = scheduler_repo.get_due_scheduled_digests()
                    
                    # Process each due task
                    for task in due_tasks:
                        task_id = task.id
                        
                        # Check if we already have a running task for this ID
                        if task_id in self._running_tasks and not self._running_tasks[task_id].done():
                            continue
                        
                        # Create task data
                        task_type = f"digest_{task.digest_type}"
                        task_data = {
                            "digest_id": task.id,
                            "digest_type": task.digest_type,
                            "recipient": task.recipient,
                            "delivery_method": task.delivery_method,
                            "content_types": task.content_types.split(",") if task.content_types else None,
                            "tags": task.tags.split(",") if task.tags else None,
                        }
                        
                        # Create and run the task
                        self._running_tasks[task_id] = asyncio.create_task(
                            self._execute_task(task_id, task_type, task_data)
                        )
                    
                    # Close the database session
                    db.close()
                
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {str(e)}")
                
                # Sleep before next check
                await asyncio.sleep(60)  # Check every minute
        
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
        except Exception as e:
            logger.error(f"Scheduler loop crashed: {str(e)}")
    
    async def _run_task_at_time(self, task_id: str, task_type: str, run_time: datetime, task_data: Dict[str, Any]):
        """Run a task at a specific time"""
        try:
            # Calculate delay until task time
            now = datetime.now()
            delay = (run_time - now).total_seconds()
            
            if delay > 0:
                logger.info(f"Task {task_id} scheduled to run in {delay:.1f} seconds")
                await asyncio.sleep(delay)
            
            # Execute the task
            await self._execute_task(task_id, task_type, task_data)
        
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} cancelled")
        except Exception as e:
            logger.error(f"Error running task {task_id} at time: {str(e)}")
    
    async def _execute_task(self, task_id: str, task_type: str, task_data: Dict[str, Any]):
        """Execute a scheduled task"""
        try:
            logger.info(f"Executing task {task_id} of type {task_type}")
            
            # Find the callback for this task type
            callback = self._callback_registry.get(task_type)
            if not callback:
                logger.error(f"No callback registered for task type {task_type}")
                return
            
            # Execute the callback
            result = await callback(task_data)
            
            # Update task status in database
            db = SessionLocal()
            try:
                scheduler_repo = SchedulerRepository(db)
                success = result.get("status") == "success"
                scheduler_repo.update_last_run(task_id, success)
            finally:
                db.close()
            
            logger.info(f"Task {task_id} completed with status: {result.get('status')}")
        
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}")


# Create singleton instance
scheduler_service = SchedulerService()
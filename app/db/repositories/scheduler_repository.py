# app/db/repositories/scheduler_repository.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.schema.scheduler import ScheduledDigest

class SchedulerRepository:
    """Repository for managing scheduled digest operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_scheduled_digest(self, digest_data: Dict[str, Any]) -> ScheduledDigest:
        """Create a new scheduled digest"""
        # Calculate next run time
        now = datetime.now()
        hour, minute = map(int, digest_data.get("time", "09:00").split(":"))
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If target time is in the past, schedule for tomorrow
        if target_time <= now:
            if digest_data.get("schedule_type") == "daily":
                target_time = target_time + timedelta(days=1)
            elif digest_data.get("schedule_type") == "weekly":
                target_time = target_time + timedelta(days=7)
            elif digest_data.get("schedule_type") == "monthly":
                # Approximate next month
                new_month = now.month + 1
                new_year = now.year
                if new_month > 12:
                    new_month = 1
                    new_year += 1
                next_month_day = min(now.day, 28)  # Safe for all months
                target_time = now.replace(year=new_year, month=new_month, day=next_month_day, 
                                       hour=hour, minute=minute, second=0, microsecond=0)
        
        # Format tags and content_types if they are lists
        content_types = digest_data.get("content_types")
        tags = digest_data.get("tags")
        
        if isinstance(content_types, list):
            content_types = ",".join(content_types)
        
        if isinstance(tags, list):
            tags = ",".join(tags)
        
        # Create the scheduled digest
        scheduled_digest = ScheduledDigest(
            schedule_type=digest_data.get("schedule_type", "daily"),
            time=digest_data.get("time", "09:00"),
            recipient=digest_data.get("recipient"),
            delivery_method=digest_data.get("delivery_method", "email"),
            digest_type=digest_data.get("digest_type", "daily"),
            content_types=content_types,
            tags=tags,
            active=True,
            next_run=target_time
        )
        
        self.db.add(scheduled_digest)
        self.db.commit()
        self.db.refresh(scheduled_digest)
        
        return scheduled_digest
    
    def get_scheduled_digest(self, digest_id: str) -> Optional[ScheduledDigest]:
        """Get a scheduled digest by ID"""
        return self.db.query(ScheduledDigest).filter(ScheduledDigest.id == digest_id).first()
    
    def get_all_scheduled_digests(self, active_only: bool = False) -> List[ScheduledDigest]:
        """Get all scheduled digests"""
        query = self.db.query(ScheduledDigest)
        
        if active_only:
            query = query.filter(ScheduledDigest.active == True)
        
        return query.all()
    
    def get_due_scheduled_digests(self) -> List[ScheduledDigest]:
        """Get all scheduled digests that are due to run"""
        now = datetime.now()
        
        return self.db.query(ScheduledDigest).filter(
            ScheduledDigest.active == True,
            ScheduledDigest.next_run <= now
        ).all()
    
    def update_scheduled_digest(self, digest_id: str, digest_data: Dict[str, Any]) -> Optional[ScheduledDigest]:
        """Update a scheduled digest"""
        scheduled_digest = self.get_scheduled_digest(digest_id)
        
        if not scheduled_digest:
            return None
        
        # Update fields if provided
        if "schedule_type" in digest_data:
            scheduled_digest.schedule_type = digest_data["schedule_type"]
        
        if "time" in digest_data:
            scheduled_digest.time = digest_data["time"]
        
        if "recipient" in digest_data:
            scheduled_digest.recipient = digest_data["recipient"]
        
        if "delivery_method" in digest_data:
            scheduled_digest.delivery_method = digest_data["delivery_method"]
        
        if "digest_type" in digest_data:
            scheduled_digest.digest_type = digest_data["digest_type"]
        
        if "content_types" in digest_data:
            content_types = digest_data["content_types"]
            if isinstance(content_types, list):
                content_types = ",".join(content_types)
            scheduled_digest.content_types = content_types
        
        if "tags" in digest_data:
            tags = digest_data["tags"]
            if isinstance(tags, list):
                tags = ",".join(tags)
            scheduled_digest.tags = tags
        
        if "active" in digest_data:
            scheduled_digest.active = digest_data["active"]
        
        if "next_run" in digest_data:
            scheduled_digest.next_run = digest_data["next_run"]
        
        self.db.commit()
        self.db.refresh(scheduled_digest)
        
        return scheduled_digest
    
    def update_last_run(self, digest_id: str, success: bool = True) -> Optional[ScheduledDigest]:
        """Update the last_run time and calculate next_run"""
        scheduled_digest = self.get_scheduled_digest(digest_id)
        
        if not scheduled_digest:
            return None
        
        now = datetime.now()
        scheduled_digest.last_run = now
        
        # Calculate next run time
        hour, minute = map(int, scheduled_digest.time.split(":"))
        
        if scheduled_digest.schedule_type == "daily":
            # Next day at the scheduled time
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
        
        elif scheduled_digest.schedule_type == "weekly":
            # Next week at the scheduled time
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=7)
        
        elif scheduled_digest.schedule_type == "monthly":
            # Next month at the scheduled time
            new_month = now.month + 1
            new_year = now.year
            if new_month > 12:
                new_month = 1
                new_year += 1
            next_month_day = min(now.day, 28)  # Safe for all months
            next_run = now.replace(year=new_year, month=new_month, day=next_month_day, 
                                hour=hour, minute=minute, second=0, microsecond=0)
        
        else:  # Custom or unknown type
            # Default to daily
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
        
        scheduled_digest.next_run = next_run
        
        self.db.commit()
        self.db.refresh(scheduled_digest)
        
        return scheduled_digest
    
    def delete_scheduled_digest(self, digest_id: str) -> bool:
        """Delete a scheduled digest"""
        scheduled_digest = self.get_scheduled_digest(digest_id)
        
        if not scheduled_digest:
            return False
        
        self.db.delete(scheduled_digest)
        self.db.commit()
        
        return True
    
    def deactivate_scheduled_digest(self, digest_id: str) -> Optional[ScheduledDigest]:
        """Deactivate a scheduled digest"""
        return self.update_scheduled_digest(digest_id, {"active": False})
    
    def activate_scheduled_digest(self, digest_id: str) -> Optional[ScheduledDigest]:
        """Activate a scheduled digest"""
        return self.update_scheduled_digest(digest_id, {"active": True})
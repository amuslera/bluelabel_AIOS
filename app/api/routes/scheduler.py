# app/api/routes/scheduler.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.services.scheduler.scheduler_service import scheduler_service

router = APIRouter(
    prefix="/scheduler",
    tags=["scheduler"],
    responses={404: {"description": "Not found"}},
)

class ScheduleDigestRequest(BaseModel):
    schedule_type: str  # daily, weekly, monthly
    time: str  # HH:MM format
    recipient: str  # email or WhatsApp recipient
    digest_type: Optional[str] = "daily"  # daily, weekly, monthly, custom
    content_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    delivery_method: Optional[str] = None  # email, whatsapp

class UpdateDigestRequest(BaseModel):
    schedule_type: Optional[str] = None  # daily, weekly, monthly
    time: Optional[str] = None  # HH:MM format
    recipient: Optional[str] = None  # email or WhatsApp recipient
    digest_type: Optional[str] = None  # daily, weekly, monthly, custom
    content_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    active: Optional[bool] = None
    delivery_method: Optional[str] = None  # email, whatsapp

@router.get("/digests")
async def list_scheduled_digests(active_only: bool = False):
    """List all scheduled digests"""
    result = await scheduler_service.get_scheduled_digests(active_only)
    
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to list scheduled digests"))
    
    return result

@router.post("/digests")
async def schedule_digest(request: ScheduleDigestRequest):
    """Schedule a new digest"""
    schedule_data = request.dict()
    result = await scheduler_service.schedule_digest(schedule_data)
    
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to schedule digest"))
    
    return result

@router.put("/digests/{digest_id}")
async def update_scheduled_digest(digest_id: str, request: UpdateDigestRequest):
    """Update a scheduled digest"""
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    result = await scheduler_service.update_scheduled_digest(digest_id, update_data)
    
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message", f"Scheduled digest {digest_id} not found"))
    
    return result

@router.delete("/digests/{digest_id}")
async def cancel_scheduled_digest(digest_id: str):
    """Cancel a scheduled digest"""
    result = await scheduler_service.cancel_scheduled_digest(digest_id)
    
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message", f"Scheduled digest {digest_id} not found"))
    
    return result
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any
from app.core.security import get_current_admin
from app.db.mongo import get_conversations_collection, get_leads_collection, get_database

router = APIRouter()

class FeedbackMetrics(BaseModel):
    total_feedback: int = Field(..., description="Total feedback reviews submitted")
    up_count: int = Field(..., description="Number of positive feedback reviews")
    down_count: int = Field(..., description="Number of negative feedback reviews")
    average_rating: float = Field(..., description="Ratio of positive feedback to total reviews")

class AnalyticsResponse(BaseModel):
    total_conversations: int = Field(..., description="Number of unique conversation sessions")
    total_turns: int = Field(..., description="Number of total conversation turns")
    intent_breakdown: Dict[str, int] = Field(..., description="Breakdown of query intents")
    feedback_metrics: FeedbackMetrics = Field(..., description="Feedback performance metrics")
    leads_captured_per_day: Dict[str, int] = Field(..., description="Daily breakdown of captured leads")

@router.get("/analytics", response_model=AnalyticsResponse, summary="Get chatbot performance metrics (Admin only)")
def get_analytics(current_admin: str = Depends(get_current_admin)):
    try:
        conversations_coll = get_conversations_collection()
        leads_coll = get_leads_collection()
        db = get_database()
        feedback_coll = db["feedback"]
        
        # 1. Total conversations & turns
        unique_sessions = len(conversations_coll.distinct("session_id"))
        total_turns = conversations_coll.count_documents({})
        
        # 2. Intent breakdown from conversations
        intent_pipeline = [
            {"$group": {"_id": "$intent", "count": {"$sum": 1}}}
        ]
        intent_results = list(conversations_coll.aggregate(intent_pipeline))
        intent_breakdown = {}
        for res in intent_results:
            intent_name = res["_id"] or "Support"
            intent_breakdown[intent_name] = res["count"]
            
        # 3. Average feedback rating
        feedback_pipeline = [
            {"$group": {"_id": "$rating", "count": {"$sum": 1}}}
        ]
        feedback_results = list(feedback_coll.aggregate(feedback_pipeline))
        up_count = 0
        down_count = 0
        for res in feedback_results:
            if res["_id"] == "up":
                up_count = res["count"]
            elif res["_id"] == "down":
                down_count = res["count"]
                
        total_feedback = up_count + down_count
        average_rating = up_count / total_feedback if total_feedback > 0 else 0.0
        
        # 4. Leads captured per day
        leads = list(leads_coll.find({}, {"updated_at": 1}))
        leads_per_day = {}
        for lead in leads:
            updated_at = lead.get("updated_at")
            if updated_at:
                date_str = updated_at[:10]  # "YYYY-MM-DD"
                leads_per_day[date_str] = leads_per_day.get(date_str, 0) + 1
                
        return AnalyticsResponse(
            total_conversations=unique_sessions,
            total_turns=total_turns,
            intent_breakdown=intent_breakdown,
            feedback_metrics=FeedbackMetrics(
                total_feedback=total_feedback,
                up_count=up_count,
                down_count=down_count,
                average_rating=average_rating
            ),
            leads_captured_per_day=leads_per_day
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analytics data: {str(e)}"
        )

@router.get("/leads", summary="Get list of all captured leads (Admin only)")
def get_leads(current_admin: str = Depends(get_current_admin)):
    try:
        leads_coll = get_leads_collection()
        leads = list(leads_coll.find({}).sort("updated_at", -1))
        
        results = []
        for lead in leads:
            results.append({
                "id": str(lead["_id"]),
                "session_id": lead["session_id"],
                "name": lead.get("name"),
                "email": lead.get("email"),
                "company": lead.get("company"),
                "intent": lead.get("intent", "Sales"),
                "score": lead.get("score", 0),
                "updated_at": lead.get("updated_at")
            })
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving leads list: {str(e)}"
        )


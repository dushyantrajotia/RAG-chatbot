from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from app.services.rag_service import query_rag_pipeline
from app.db.mongo import save_conversation_turn, save_feedback
from app.core.security import get_current_user
from app.services.intent import classify_intent
from app.services.lead_scoring import process_and_store_lead

router = APIRouter()




class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique chat session identifier")
    message: str = Field(..., description="User query / prompt message")

class SourceItem(BaseModel):
    source: str = Field(..., description="File name or document source")
    content: str = Field(..., description="Matched text chunk content")
    score: Optional[float] = Field(None, description="Similarity distance score")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer from RAG model")
    sources: List[SourceItem] = Field(default_factory=list, description="Retrieved context sources")
    conversation_id: Optional[str] = Field(None, description="The unique ID of the conversation turn stored in MongoDB")

@router.post("/chat", response_model=ChatResponse, summary="Send message and receive RAG answer")
def chat_endpoint(request: ChatRequest, current_user: str = Depends(get_current_user)):

    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message field cannot be empty."
        )
        
    try:
        result = query_rag_pipeline(query=request.message, session_id=request.session_id)
        
        # Persist turn to MongoDB conversations collection
        turn_id = save_conversation_turn(
            session_id=request.session_id,
            message=request.message,
            answer=result["answer"]
        )

        # Classify message intent & conditionally trigger lead capture for Sales / Pricing queries
        try:
            intent_res = classify_intent(request.message)
            detected_intent = intent_res.get("intent", "Support")
            
            # Save intent to the conversation turn document in MongoDB
            try:
                from bson import ObjectId
                from app.db.mongo import get_conversations_collection
                conversations = get_conversations_collection()
                conversations.update_one({"_id": ObjectId(turn_id)}, {"$set": {"intent": detected_intent}})
            except Exception:
                pass
            
            if detected_intent in ["Sales", "Pricing"]:
                process_and_store_lead(
                    session_id=request.session_id,
                    conversation_text=request.message,
                    intent=detected_intent
                )
        except Exception as le:
            print(f"Warning: Lead scoring processing error: {le}")


        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            conversation_id=turn_id
        )



    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}"
        )

class FeedbackRequest(BaseModel):
    conversation_id: str = Field(..., description="Unique identifier of the conversation turn or session")
    rating: Literal["up", "down"] = Field(..., description="Feedback rating, must be 'up' or 'down'")

class FeedbackResponse(BaseModel):
    status: str = Field(..., description="Feedback submission status")
    message: str = Field(..., description="Success or error details")

@router.post("/feedback", response_model=FeedbackResponse, summary="Submit feedback (up/down) for a conversation turn")
def submit_feedback(request: FeedbackRequest, current_user: str = Depends(get_current_user)):
    success = save_feedback(conversation_id=request.conversation_id, rating=request.rating)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist feedback in MongoDB."
        )
    return FeedbackResponse(
        status="success",
        message="Feedback stored successfully."
    )


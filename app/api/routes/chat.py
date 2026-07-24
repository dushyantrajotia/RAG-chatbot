from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.rag_service import query_rag_pipeline
from app.db.mongo import save_conversation_turn
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
        save_conversation_turn(
            session_id=request.session_id,
            message=request.message,
            answer=result["answer"]
        )

        # Classify message intent & conditionally trigger lead capture for Sales / Pricing queries
        try:
            intent_res = classify_intent(request.message)
            detected_intent = intent_res.get("intent", "Support")
            
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
            sources=result["sources"]
        )


    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}"
        )

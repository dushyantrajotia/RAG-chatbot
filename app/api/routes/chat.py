from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.rag_service import query_rag_pipeline
from app.db.mongo import save_conversation_turn

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
def chat_endpoint(request: ChatRequest):
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

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}"
        )

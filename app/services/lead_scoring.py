import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.rag_service import get_llm
from app.db.mongo import get_leads_collection

class ExtractedLeadInfo(BaseModel):
    name: Optional[str] = Field(None, description="Extracted lead person name")
    email: Optional[str] = Field(None, description="Extracted lead email address")
    company: Optional[str] = Field(None, description="Extracted lead company or organization")

def extract_lead_entities(conversation_text: str) -> Dict[str, Optional[str]]:
    """Uses LLM to extract contact details (name, email, company) from conversation text."""
    cleaned_text = conversation_text.strip()
    if not cleaned_text:
        return {"name": None, "email": None, "company": None}

    from langchain_core.prompts import PromptTemplate

    template = """You are an information extraction assistant.
Extract contact and lead details (Name, Email, Company) from the conversation text provided below.
If any piece of information is missing, set its value to null.

Respond ONLY with a valid JSON object strictly matching this format:
```json
{{
    "name": "<extracted full name or null>",
    "email": "<extracted email address or null>",
    "company": "<extracted company name or null>"
}}
```

Conversation Text:
{conversation_text}

JSON Output:"""

    prompt = PromptTemplate(template=template, input_variables=["conversation_text"])
    
    try:
        llm = get_llm()
        chain = prompt | llm
        response = chain.invoke({"conversation_text": cleaned_text})
        
        raw_output = response.content if hasattr(response, "content") else str(response)
        
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(raw_output.strip())

        def clean_val(val):
            if val and isinstance(val, str) and val.strip().lower() not in ["null", "none", "n/a", ""]:
                return val.strip()
            return None

        return {
            "name": clean_val(data.get("name")),
            "email": clean_val(data.get("email")),
            "company": clean_val(data.get("company"))
        }
    except Exception as e:
        print(f"Warning: Exception during lead entity extraction: {e}")
        # Rule-based regex extraction fallback for email
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", cleaned_text)
        extracted_email = email_match.group(0) if email_match else None
        return {"name": None, "email": extracted_email, "company": None}

def calculate_lead_score(intent: str, extracted_info: Dict[str, Optional[str]], turn_count: int = 1) -> int:
    """Calculates lead score (0-100) based on intent and engagement signals."""
    score = 0
    
    # Intent base score
    intent_scores = {
        "Sales": 40,
        "Pricing": 30,
        "Support": 15,
        "Complaint": 10
    }
    score += intent_scores.get(intent.title(), 15)
    
    # Contact information signals
    if extracted_info.get("email"):
        score += 25
    if extracted_info.get("company"):
        score += 20
    if extracted_info.get("name"):
        score += 10
        
    # Multi-turn engagement depth signals
    if turn_count >= 5:
        score += 15
    elif turn_count >= 3:
        score += 10
    elif turn_count >= 2:
        score += 5

    # Clamp score between 0 and 100
    return max(0, min(100, score))

def process_and_store_lead(session_id: str, conversation_text: str, intent: str = "Sales", turn_count: int = 1) -> Dict[str, Any]:
    """Extracts lead info, computes score (0-100), and stores/upserts lead in MongoDB leads collection."""
    extracted_info = extract_lead_entities(conversation_text)
    score = calculate_lead_score(intent=intent, extracted_info=extracted_info, turn_count=turn_count)
    
    lead_doc = {
        "session_id": session_id,
        "name": extracted_info.get("name"),
        "email": extracted_info.get("email"),
        "company": extracted_info.get("company"),
        "intent": intent,
        "score": score,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        leads_coll = get_leads_collection()
        leads_coll.update_one(
            {"session_id": session_id},
            {"$set": lead_doc},
            upsert=True
        )
    except Exception as e:
        print(f"Warning: Failed to persist lead to MongoDB: {e}")

    return lead_doc

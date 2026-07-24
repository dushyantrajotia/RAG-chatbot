import json
import re
from typing import Dict, Any
from pydantic import BaseModel, Field
from app.services.rag_service import get_llm

class IntentClassificationResult(BaseModel):
    intent: str = Field(..., description="Classified intent: Support, Sales, Pricing, or Complaint")
    confidence: float = Field(default=1.0, description="Classification confidence score between 0.0 and 1.0")
    reasoning: str = Field(default="", description="Brief explanation for the classification")

def classify_intent(message: str) -> Dict[str, Any]:
    """Classifies user message intent into Support, Sales, Pricing, or Complaint using structured JSON LLM prompt."""
    cleaned_message = message.strip()
    if not cleaned_message:
        return {
            "intent": "Support",
            "confidence": 0.0,
            "reasoning": "Empty message string provided."
        }

    from langchain_core.prompts import PromptTemplate

    template = """You are an expert customer query intent classifier.
Analyze the user message and classify it into EXACTLY ONE of the following categories:
- Support (technical help, bug reports, product usage questions)
- Sales (buying interest, enterprise demos, partnership inquiries)
- Pricing (subscription costs, plans, billing, payment options)
- Complaint (dissatisfaction, refund requests, poor service feedback)

Respond ONLY with a valid JSON object strictly matching this format:
```json
{{
    "intent": "<Support | Sales | Pricing | Complaint>",
    "confidence": <number between 0.0 and 1.0>,
    "reasoning": "<brief 1-sentence justification>"
}}
```

User Message: {message}

JSON Output:"""

    prompt = PromptTemplate(template=template, input_variables=["message"])
    
    try:
        llm = get_llm()
        chain = prompt | llm
        response = chain.invoke({"message": cleaned_message})
        
        raw_output = response.content if hasattr(response, "content") else str(response)
        
        # Extract JSON substring if wrapped in markdown code blocks or text
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(raw_output.strip())

        valid_intents = {"Support", "Sales", "Pricing", "Complaint"}
        raw_intent = str(data.get("intent", "Support")).strip().title()
        
        if raw_intent not in valid_intents:
            raw_intent = "Support"

        return {
            "intent": raw_intent,
            "confidence": float(data.get("confidence", 1.0)),
            "reasoning": str(data.get("reasoning", ""))
        }
    except Exception as e:
        print(f"Warning: LLM intent classification exception: {e}")
        # Rule-based fallback if LLM is unavailable or fails
        msg_lower = cleaned_message.lower()
        if any(k in msg_lower for k in ["price", "cost", "plan", "subscription", "billing", "fee", "pay"]):
            fallback_intent = "Pricing"
        elif any(k in msg_lower for k in ["buy", "demo", "sales", "enterprise", "purchase", "quote"]):
            fallback_intent = "Sales"
        elif any(k in msg_lower for k in ["bad", "terrible", "refund", "complaint", "issue", "angry", "cancel"]):
            fallback_intent = "Complaint"
        else:
            fallback_intent = "Support"

        return {
            "intent": fallback_intent,
            "confidence": 0.7,
            "reasoning": "Fallback keyword classification"
        }

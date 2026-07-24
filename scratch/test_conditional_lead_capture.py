import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")
from unittest.mock import MagicMock

# Mock dotenv
sys.modules['dotenv'] = MagicMock()

# Mock fastapi
mock_fastapi = MagicMock()
mock_fastapi.HTTPException = Exception
mock_fastapi.status = MagicMock()
mock_fastapi.Depends = lambda dep: None
class MockAPIRouter:
    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
mock_fastapi.APIRouter = MockAPIRouter
sys.modules['fastapi'] = mock_fastapi

# Mock pydantic
mock_pydantic = MagicMock()
class DummyBaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
mock_pydantic.BaseModel = DummyBaseModel
mock_pydantic.Field = lambda default=..., **kwargs: default
sys.modules['pydantic'] = mock_pydantic

# Mock rag_service
mock_rag = MagicMock()
mock_rag.query_rag_pipeline.return_value = {"answer": "Here is information.", "sources": []}
sys.modules['app.services.rag_service'] = mock_rag

# Mock mongo & security
sys.modules['app.db.mongo'] = MagicMock()
sys.modules['app.core.security'] = MagicMock()

# Mock intent service
mock_intent = MagicMock()
current_mock_intent = "Sales"
mock_intent.classify_intent.side_effect = lambda msg: {"intent": current_mock_intent, "confidence": 0.9, "reasoning": ""}
sys.modules['app.services.intent'] = mock_intent

# Mock lead_scoring service
mock_lead_scoring = MagicMock()
lead_capture_calls = []
def mock_process_and_store(session_id, conversation_text, intent):
    lead_capture_calls.append({"session_id": session_id, "intent": intent})
    return {}

mock_lead_scoring.process_and_store_lead.side_effect = mock_process_and_store
sys.modules['app.services.lead_scoring'] = mock_lead_scoring

# Import chat route
if 'app.api.routes.chat' in sys.modules:
    del sys.modules['app.api.routes.chat']
import app.api.routes.chat as chat_mod

# Test 1: Sales Intent -> Triggers Lead Capture
current_mock_intent = "Sales"
lead_capture_calls.clear()
req_sales = chat_mod.ChatRequest(session_id="s1", message="I want to buy enterprise tier")
chat_mod.chat_endpoint(req_sales, current_user="user@test.com")
assert len(lead_capture_calls) == 1
assert lead_capture_calls[0]["intent"] == "Sales"

# Test 2: Pricing Intent -> Triggers Lead Capture
current_mock_intent = "Pricing"
lead_capture_calls.clear()
req_pricing = chat_mod.ChatRequest(session_id="s2", message="How much does it cost?")
chat_mod.chat_endpoint(req_pricing, current_user="user@test.com")
assert len(lead_capture_calls) == 1
assert lead_capture_calls[0]["intent"] == "Pricing"

# Test 3: Support Intent -> DOES NOT Trigger Lead Capture
current_mock_intent = "Support"
lead_capture_calls.clear()
req_support = chat_mod.ChatRequest(session_id="s3", message="How do I reset my password?")
chat_mod.chat_endpoint(req_support, current_user="user@test.com")
assert len(lead_capture_calls) == 0, "Support intent should NOT trigger lead capture"

print("Verification SUCCESS: Conditional lead capture (Sales/Pricing trigger, Support ignore) verified!")

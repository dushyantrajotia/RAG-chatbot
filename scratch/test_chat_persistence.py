import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")
from unittest.mock import MagicMock

# Mock dotenv
sys.modules['dotenv'] = MagicMock()

# Mock fastapi
mock_fastapi = MagicMock()
mock_fastapi.HTTPException = Exception
mock_fastapi.status = MagicMock()
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

# Mock RAG service
mock_rag_service = MagicMock()
mock_rag_service.query_rag_pipeline.return_value = {
    "answer": "This is a RAG generated response.",
    "sources": []
}
sys.modules['app.services.rag_service'] = mock_rag_service

# Mock save_conversation_turn
mock_mongo = MagicMock()
saved_turns = []
def mock_save(session_id, message, answer):
    saved_turns.append({
        "session_id": session_id,
        "message": message,
        "answer": answer
    })
    return "mock_id_123"

mock_mongo.save_conversation_turn.side_effect = mock_save
sys.modules['app.db.mongo'] = mock_mongo

# Import chat route module
if 'app.api.routes.chat' in sys.modules:
    del sys.modules['app.api.routes.chat']
import app.api.routes.chat as chat_mod

# Call chat_endpoint
req = chat_mod.ChatRequest(session_id="session_xyz", message="What are the store hours?")
res = chat_mod.chat_endpoint(req)

# Verify save_conversation_turn was called with expected arguments
assert len(saved_turns) == 1, "Expected 1 conversation turn saved to MongoDB"
assert saved_turns[0]["session_id"] == "session_xyz"
assert saved_turns[0]["message"] == "What are the store hours?"
assert saved_turns[0]["answer"] == "This is a RAG generated response."

print("Verification SUCCESS: POST /chat conversation turn persistence to MongoDB verified!")

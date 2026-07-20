import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")
from unittest.mock import MagicMock

# Mock dotenv
sys.modules['dotenv'] = MagicMock()

# Mock fastapi
mock_fastapi = MagicMock()
class MockHTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail

mock_fastapi.HTTPException = MockHTTPException
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
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                v = [DummyBaseModel(**item) for item in v]
            setattr(self, k, v)



mock_pydantic.BaseModel = DummyBaseModel
mock_pydantic.Field = lambda default=..., **kwargs: default
sys.modules['pydantic'] = mock_pydantic

# Mock RAG service
mock_rag_service = MagicMock()
mock_rag_service.query_rag_pipeline.return_value = {
    "answer": "RAG stands for Retrieval-Augmented Generation.",
    "sources": [
        {"source": "doc1.txt", "content": "RAG concept explanation", "score": 0.12}
    ]
}
sys.modules['app.services.rag_service'] = mock_rag_service

# Import chat route module
if 'app.api.routes.chat' in sys.modules:
    del sys.modules['app.api.routes.chat']
import app.api.routes.chat as chat_mod

# Execute chat endpoint function directly
request_payload = chat_mod.ChatRequest(session_id="test_session_1", message="Tell me about RAG")
response = chat_mod.chat_endpoint(request_payload)

# Assertions
mock_rag_service.query_rag_pipeline.assert_called_once_with(query="Tell me about RAG")
assert response.answer == "RAG stands for Retrieval-Augmented Generation."
assert len(response.sources) == 1
assert response.sources[0].source == "doc1.txt"
assert response.sources[0].content == "RAG concept explanation"
assert response.sources[0].score == 0.12

print("Verification SUCCESS: POST /chat route logic, payload processing, and RAG service call verified!")

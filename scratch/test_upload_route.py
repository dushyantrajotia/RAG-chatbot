import sys
import io
import asyncio
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")

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
mock_fastapi.File = lambda *args, **kwargs: None
mock_fastapi.UploadFile = MagicMock
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

# Mock ingest_service
mock_ingest_service = MagicMock()
mock_ingest_service.ingest_file_to_faiss.return_value = {
    "filename": "sample.pdf",
    "chunks_added": 5,
    "index_path": "faiss_index"
}
sys.modules['app.services.ingest_service'] = mock_ingest_service

# Import upload route module
if 'app.api.routes.documents' in sys.modules:
    del sys.modules['app.api.routes.documents']
import app.api.routes.documents as docs_mod

# Create mock upload file with BytesIO content and AsyncMock close
mock_upload_file = MagicMock()
mock_upload_file.filename = "sample.pdf"
mock_upload_file.file = io.BytesIO(b"Dummy PDF content for testing upload endpoint.")
mock_upload_file.close = AsyncMock()

async def run_test():
    response = await docs_mod.upload_document(file=mock_upload_file)
    assert response.filename == "sample.pdf"
    assert response.status == "success"
    assert response.chunks_added == 5
    print("Verification SUCCESS: POST /documents/upload file ingestion and response payload verified!")

asyncio.run(run_test())

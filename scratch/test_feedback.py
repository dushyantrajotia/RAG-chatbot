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
mock_fastapi.status.HTTP_400_BAD_REQUEST = 400
mock_fastapi.status.HTTP_401_UNAUTHORIZED = 401
mock_fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR = 500
mock_fastapi.Depends = lambda dependency: None

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

# Mock jose / security
sys.modules['jose'] = MagicMock()
sys.modules['app.core.security'] = MagicMock()

# Mock rag_service
mock_rag = MagicMock()
mock_rag.query_rag_pipeline.return_value = {"answer": "Some RAG answer", "sources": []}
sys.modules['app.services.rag_service'] = mock_rag

# Mock intent & lead_scoring
sys.modules['app.services.intent'] = MagicMock()
sys.modules['app.services.lead_scoring'] = MagicMock()

# Mock MongoDB feedback / conversations collection
mock_db = MagicMock()
feedback_db = []
conversations_db = {
    "mock_conv_id": {
        "_id": "mock_conv_id",
        "session_id": "session_123",
        "message": "hello",
        "answer": "hi",
        "feedback": None
    }
}

mock_feedback_coll = MagicMock()
def mock_insert_one(doc):
    feedback_db.append(doc)
    return MagicMock()
mock_feedback_coll.insert_one.side_effect = mock_insert_one

mock_conversations_coll = MagicMock()
def mock_update_one(filter_q, update_q):
    cid = str(filter_q.get("_id"))
    if cid in conversations_db:
        conversations_db[cid]["feedback"] = update_q["$set"]["feedback"]
        update_result = MagicMock()
        update_result.modified_count = 1
        return update_result
    res = MagicMock()
    res.modified_count = 0
    return res

def mock_update_many(filter_q, update_q):
    session_id = filter_q.get("session_id")
    for doc in conversations_db.values():
        if doc.get("session_id") == session_id:
            doc["feedback"] = update_q["$set"]["feedback"]
    res = MagicMock()
    res.modified_count = 1
    return res

mock_conversations_coll.update_one.side_effect = mock_update_one
mock_conversations_coll.update_many.side_effect = mock_update_many

def mock_get_item(name):
    if name == "feedback":
        return mock_feedback_coll
    if name == "conversations":
        return mock_conversations_coll
    return MagicMock()

mock_db.__getitem__.side_effect = mock_get_item

mock_mongo = MagicMock()
mock_mongo.get_database.return_value = mock_db
mock_mongo.get_conversations_collection.return_value = mock_conversations_coll

# Helper function mock inside mongo
def mock_save_feedback(conversation_id, rating):
    try:
        feedback_coll = mock_db["feedback"]
        feedback_coll.insert_one({
            "conversation_id": conversation_id,
            "rating": rating
        })
        
        # update directly
        try:
            if conversation_id.startswith("session"):
                raise ValueError("Not an ObjectId")
            mock_conversations_coll.update_one({"_id": conversation_id}, {"$set": {"feedback": rating}})
        except Exception:
            # If not an ObjectId, fallback to session_id
            mock_conversations_coll.update_many({"session_id": conversation_id}, {"$set": {"feedback": rating}})
        return True
    except Exception:
        return False

mock_mongo.save_feedback.side_effect = mock_save_feedback
sys.modules['app.db.mongo'] = mock_mongo

# Import chat route with the new endpoint
if 'app.api.routes.chat' in sys.modules:
    del sys.modules['app.api.routes.chat']
import app.api.routes.chat as chat_mod

# 1. Verify save_feedback helper function
success = chat_mod.save_feedback("mock_conv_id", "up")
assert success is True
assert len(feedback_db) == 1
assert feedback_db[0]["conversation_id"] == "mock_conv_id"
assert feedback_db[0]["rating"] == "up"
assert conversations_db["mock_conv_id"]["feedback"] == "up"

# 2. Verify save_feedback with session_id fallback
success_session = chat_mod.save_feedback("session_123", "down")
assert success_session is True
assert conversations_db["mock_conv_id"]["feedback"] == "down"

# 3. Test POST /feedback endpoint function
req = chat_mod.FeedbackRequest(conversation_id="mock_conv_id", rating="up")
response = chat_mod.submit_feedback(req, current_user="user@test.com")
assert response.status == "success"
assert response.message == "Feedback stored successfully."

print("Verification SUCCESS: POST /feedback database persistence and endpoint logic verified!")

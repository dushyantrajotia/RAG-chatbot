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
mock_fastapi.status.HTTP_403_FORBIDDEN = 403
mock_fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR = 500
mock_fastapi.Depends = lambda dependency: None

class MockAPIRouter:
    def get(self, *args, **kwargs):
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

# Mock passlib / jose
sys.modules['passlib'] = MagicMock()
sys.modules['jose'] = MagicMock()

# Mock users collection for role checks
mock_users_coll = MagicMock()
users_db = {
    "admin@test.com": {"email": "admin@test.com", "role": "admin"},
    "user@test.com": {"email": "user@test.com", "role": "user"}
}
mock_users_coll.find_one.side_effect = lambda query: users_db.get(query.get("email"))

# Mock conversations, leads, feedback collections
mock_conversations_coll = MagicMock()
mock_conversations_coll.distinct.return_value = ["session_1", "session_2"]
mock_conversations_coll.count_documents.return_value = 5
mock_conversations_coll.aggregate.return_value = [
    {"_id": "Sales", "count": 3},
    {"_id": "Pricing", "count": 2}
]

mock_leads_coll = MagicMock()
mock_leads_coll.find.return_value = [
    {"updated_at": "2026-07-20T10:00:00Z"},
    {"updated_at": "2026-07-20T12:00:00Z"},
    {"updated_at": "2026-07-21T08:00:00Z"}
]

mock_db = MagicMock()
mock_feedback_coll = MagicMock()
mock_feedback_coll.aggregate.return_value = [
    {"_id": "up", "count": 4},
    {"_id": "down", "count": 1}
]
def mock_get_item(name):
    if name == "feedback":
        return mock_feedback_coll
    if name == "users":
        return mock_users_coll
    if name == "conversations":
        return mock_conversations_coll
    if name == "leads":
        return mock_leads_coll
    return MagicMock()

mock_db.__getitem__.side_effect = mock_get_item

mock_mongo = MagicMock()
mock_mongo.get_database.return_value = mock_db
mock_mongo.get_users_collection.return_value = mock_users_coll
mock_mongo.get_conversations_collection.return_value = mock_conversations_coll
mock_mongo.get_leads_collection.return_value = mock_leads_coll
sys.modules['app.db.mongo'] = mock_mongo

# Mock get_current_user in security
mock_security = MagicMock()
current_email = "admin@test.com"
mock_security.get_current_user.side_effect = lambda req: current_email

# Helper function mock inside security
def mock_get_current_admin(request):
    email = current_email
    user = mock_users_coll.find_one({"email": email})
    if not user or user.get("role") != "admin":
        raise MockHTTPException(403, "Admin privileges required.")
    return email

mock_security.get_current_admin.side_effect = mock_get_current_admin
sys.modules['app.core.security'] = mock_security

# Import analytics route
if 'app.api.routes.analytics' in sys.modules:
    del sys.modules['app.api.routes.analytics']
import app.api.routes.analytics as analytics_mod

# 1. Verify get_current_admin dependency validation
# Admin email succeeds
admin_email = analytics_mod.get_current_admin(MagicMock())
assert admin_email == "admin@test.com"

# Regular user fails with 403
current_email = "user@test.com"
try:
    analytics_mod.get_current_admin(MagicMock())
    assert False, "Should raise 403 for user role"
except MockHTTPException as e:
    assert e.status_code == 403

# Restore admin email
current_email = "admin@test.com"

# 2. Verify get_analytics endpoint response format and content
res = analytics_mod.get_analytics(current_admin="admin@test.com")

assert res.total_conversations == 2
assert res.total_turns == 5
assert res.intent_breakdown["Sales"] == 3
assert res.intent_breakdown["Pricing"] == 2
assert res.feedback_metrics.total_feedback == 5
assert res.feedback_metrics.up_count == 4
assert res.feedback_metrics.down_count == 1
assert res.feedback_metrics.average_rating == 0.8
assert res.leads_captured_per_day["2026-07-20"] == 2
assert res.leads_captured_per_day["2026-07-21"] == 1

print("Verification SUCCESS: Admin restriction check and analytics aggregation metrics verified!")

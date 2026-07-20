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
mock_fastapi.status.HTTP_401_UNAUTHORIZED = 401
mock_fastapi.status.HTTP_400_BAD_REQUEST = 400
mock_fastapi.status.HTTP_201_CREATED = 201

class MockAPIRouter:
    def post(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def get(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

mock_fastapi.APIRouter = MockAPIRouter
sys.modules['fastapi'] = mock_fastapi
sys.modules['fastapi.responses'] = MagicMock()

class MockJSONResponse:
    def __init__(self, content, **kwargs):
        self.content = content
        self.cookies = {}
    def set_cookie(self, key, value, **kwargs):
        self.cookies[key] = value

sys.modules['fastapi.responses'].JSONResponse = MockJSONResponse

# Mock pydantic
mock_pydantic = MagicMock()
class DummyBaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
mock_pydantic.BaseModel = DummyBaseModel
mock_pydantic.Field = lambda default=..., **kwargs: default
sys.modules['pydantic'] = mock_pydantic

# Mock jose & passlib
mock_jose = MagicMock()
mock_jose.jwt.encode.return_value = "mock_jwt_token_abc123"
def mock_decode(token, secret, algorithms):
    if token == "mock_jwt_token_abc123":
        return {"sub": "user@example.com"}
    return None

mock_jose.jwt.decode.side_effect = mock_decode
sys.modules['jose'] = mock_jose

mock_passlib = MagicMock()
mock_pwd_ctx = MagicMock()
mock_pwd_ctx.hash.return_value = "$2b$12$mock_hashed"
mock_pwd_ctx.verify.return_value = True
mock_passlib.context = MagicMock()
mock_passlib.context.CryptContext.return_value = mock_pwd_ctx
sys.modules['passlib'] = mock_passlib
sys.modules['passlib.context'] = mock_passlib.context

# Mock config
mock_settings = MagicMock()
mock_settings.JWT_SECRET = "supersecret"
mock_settings.JWT_ALGORITHM = "HS256"
mock_config_module = MagicMock()
mock_config_module.settings = mock_settings
sys.modules['app.core.config'] = mock_config_module

# Mock users collection
users_db = {}
mock_users_coll = MagicMock()
def mock_find_one(query):
    return users_db.get(query.get("email"))
def mock_insert_one(doc):
    users_db[doc["email"]] = doc
    return MagicMock()

mock_users_coll.find_one.side_effect = mock_find_one
mock_users_coll.insert_one.side_effect = mock_insert_one

mock_mongo = MagicMock()
mock_mongo.get_users_collection.return_value = mock_users_coll
sys.modules['app.db.mongo'] = mock_mongo

# Import auth module
if 'app.api.routes.auth' in sys.modules:
    del sys.modules['app.api.routes.auth']
import app.api.routes.auth as auth_mod

# 1. Register User with custom Name and Role
reg_req = auth_mod.UserRegisterRequest(email="user@example.com", password="password123", name="Alice Smith", role="admin")
auth_mod.register_user(reg_req)

assert users_db["user@example.com"]["name"] == "Alice Smith"
assert users_db["user@example.com"]["role"] == "admin"

# 2. Test GET /auth/me with valid cookie
mock_request = MagicMock()
mock_request.cookies = {"access_token": "Bearer mock_jwt_token_abc123"}
me_res = auth_mod.get_current_user_me(mock_request)

assert me_res.name == "Alice Smith"
assert me_res.role == "admin"
assert me_res.email == "user@example.com"

# 3. Test GET /auth/me with missing cookie -> 401
mock_req_empty = MagicMock()
mock_req_empty.cookies = {}
try:
    auth_mod.get_current_user_me(mock_req_empty)
    assert False, "Should have raised 401 on missing cookie"
except MockHTTPException as e:
    assert e.status_code == 401

print("Verification SUCCESS: GET /auth/me cookie decoding, user profile lookup (name, role), and 401 error handling verified!")

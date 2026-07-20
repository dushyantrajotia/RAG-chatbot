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
mock_fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR = 500
mock_fastapi.Depends = lambda dependency: None
mock_fastapi.File = lambda *args, **kwargs: None
mock_fastapi.UploadFile = MagicMock

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

# Mock jose
mock_jose = MagicMock()
def mock_decode(token, secret, algorithms):
    if token == "valid_jwt_token":
        return {"sub": "user@example.com"}
    return None

mock_jose.jwt.decode.side_effect = mock_decode
sys.modules['jose'] = mock_jose

# Mock passlib
mock_passlib = MagicMock()
mock_passlib.context = MagicMock()
sys.modules['passlib'] = mock_passlib
sys.modules['passlib.context'] = mock_passlib.context

# Mock config

mock_settings = MagicMock()
mock_settings.JWT_SECRET = "supersecret"
mock_settings.JWT_ALGORITHM = "HS256"
mock_config_module = MagicMock()
mock_config_module.settings = mock_settings
sys.modules['app.core.config'] = mock_config_module

# Import security
import app.core.security as security_mod

# 1. Test get_current_user with missing cookie -> 401
req_missing = MagicMock()
req_missing.cookies = {}
try:
    security_mod.get_current_user(req_missing)
    assert False, "Should have raised 401 for missing cookie"
except MockHTTPException as e:
    assert e.status_code == 401

# 2. Test get_current_user with invalid cookie -> 401
req_invalid = MagicMock()
req_invalid.cookies = {"access_token": "invalid_token_str"}
try:
    security_mod.get_current_user(req_invalid)
    assert False, "Should have raised 401 for invalid token"
except MockHTTPException as e:
    assert e.status_code == 401

# 3. Test get_current_user with valid cookie -> returns user sub
req_valid = MagicMock()
req_valid.cookies = {"access_token": "Bearer valid_jwt_token"}
user_sub = security_mod.get_current_user(req_valid)
assert user_sub == "user@example.com"

print("Verification SUCCESS: get_current_user dependency cookie validation and 401 rejection verified!")

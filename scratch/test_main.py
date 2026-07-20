import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")
from unittest.mock import MagicMock

# Mock modules
sys.modules['dotenv'] = MagicMock()
mock_fastapi = MagicMock()
mock_cors = MagicMock()

# Setup FastAPI class mock
mock_app_instance = MagicMock()
mock_app_instance.routes = []

def mock_get(path, **kwargs):
    def decorator(func):
        mock_route = MagicMock()
        mock_route.path = path
        mock_app_instance.routes.append(mock_route)
        return func
    return decorator

mock_app_instance.get = mock_get
mock_fastapi.FastAPI.return_value = mock_app_instance

sys.modules['fastapi'] = mock_fastapi
sys.modules['fastapi.middleware'] = MagicMock()
sys.modules['fastapi.middleware.cors'] = mock_cors
mock_cors.CORSMiddleware = "CORSMiddleware"

# Mock app.core.config
mock_settings = MagicMock()
mock_settings.PROJECT_NAME = "RAG Chatbot Backend"
mock_settings.FRONTEND_ORIGIN = "http://localhost:3000, http://localhost:5173"
mock_config_module = MagicMock()
mock_config_module.settings = mock_settings
sys.modules['app.core.config'] = mock_config_module

# Import main module
import app.main as main_mod

# Verify FastAPI was instantiated
mock_fastapi.FastAPI.assert_called_once_with(
    title="RAG Chatbot Backend",
    description="FastAPI Backend for RAG Chatbot",
    version="1.0.0"
)

# Verify CORSMiddleware was added with allow_credentials=True and expected origins
mock_app_instance.add_middleware.assert_called_once_with(
    "CORSMiddleware",
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Verify routes were registered
route_paths = [r.path for r in mock_app_instance.routes]
assert "/" in route_paths, "Root route '/' missing"
assert "/health" in route_paths, "Health check route '/health' missing"

print("Verification SUCCESS: app/main.py FastAPI instance, CORS middleware, and routes verified!")

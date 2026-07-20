from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI Backend for RAG Chatbot",
    version="1.0.0"
)

# Parse FRONTEND_ORIGIN into a list of origins
frontend_origin = settings.FRONTEND_ORIGIN
if frontend_origin:
    origins = [origin.strip() for origin in frontend_origin.split(",") if origin.strip()]
else:
    origins = ["http://localhost:3000"]

# Add CORS Middleware with allow_credentials=True for cookie-based authentication
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.auth import router as auth_router

app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])



from app.db.mongo import connect_to_mongo, close_mongo_connection

@app.on_event("startup")
def startup_db_client():
    try:
        connect_to_mongo()
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB on startup: {e}")

@app.on_event("shutdown")
def shutdown_db_client():
    close_mongo_connection()

@app.get("/", tags=["Root"])
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"}



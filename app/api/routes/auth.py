from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.db.mongo import get_users_collection
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter()

class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (minimum 6 characters)")
    name: Optional[str] = Field(None, description="Optional user display name")
    role: Optional[str] = Field("user", description="Optional user role (default: user)")

class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class AuthResponse(BaseModel):
    message: str = Field(..., description="Status message")
    email: str = Field(..., description="User email address")

class UserMeResponse(BaseModel):
    name: str = Field(..., description="User display name")
    role: str = Field(..., description="User system role")
    email: str = Field(..., description="User email address")

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user")
def register_user(request: UserRegisterRequest):
    email = request.email.strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address cannot be empty."
        )

    users_coll = get_users_collection()
    existing_user = users_coll.find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered."
        )

    name = request.name.strip() if request.name and request.name.strip() else email.split("@")[0]
    role = request.role if request.role else "user"
    hashed_pwd = hash_password(request.password)

    user_doc = {
        "email": email,
        "name": name,
        "role": role,
        "hashed_password": hashed_pwd,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    users_coll.insert_one(user_doc)

    return AuthResponse(
        message="User registered successfully.",
        email=email
    )

@router.post("/login", response_model=AuthResponse, summary="Authenticate user and set httpOnly JWT cookie")
def login_user(request: UserLoginRequest, response: Response):
    email = request.email.strip().lower()
    users_coll = get_users_collection()
    
    user = users_coll.find_one({"email": email})
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password."
        )

    access_token = create_access_token({"sub": email})

    # Prepare response with httpOnly, sameSite=lax cookie
    res = JSONResponse(
        content={
            "message": "Login successful.",
            "email": email
        }
    )
    res.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400  # 24 hours
    )
    return res

@router.get("/me", response_model=UserMeResponse, summary="Get current authenticated user info from JWT cookie")
def get_current_user_me(request: Request):
    token_cookie = request.cookies.get("access_token")
    if not token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication cookie missing."
        )

    token = token_cookie.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )

    email = payload["sub"]
    users_coll = get_users_collection()
    user = users_coll.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found."
        )

    return UserMeResponse(
        name=user.get("name", email.split("@")[0]),
        role=user.get("role", "user"),
        email=user.get("email", email)
    )

@router.post("/logout", summary="Logout user and clear JWT cookie")
def logout_user(response: Response):
    res = JSONResponse(content={"message": "Logged out successfully."})
    res.delete_cookie(key="access_token", samesite="lax")
    return res

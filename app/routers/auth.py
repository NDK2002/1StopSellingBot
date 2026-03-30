from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import bcrypt
import os
from app.config import get_supabase_client

router = APIRouter(prefix="/api/auth", tags=["auth"])
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-default")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    supabase = get_supabase_client()
    res = supabase.table("staff").select("id, name, email, role, password_hash").eq("email", req.email).execute()
    
    if not res.data:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác")
    
    user = res.data[0]
    
    if not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Tài khoản chưa được thiết lập mật khẩu")
    
    provided_pw = req.password.encode('utf-8')
    stored_hash = user['password_hash'].encode('utf-8')
    
    if not bcrypt.checkpw(provided_pw, stored_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác")
    
    exp = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user["id"], 
        "email": user["email"], 
        "role": user.get("role", "staff"), 
        "exp": exp
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    del user["password_hash"]
    
    return LoginResponse(
        access_token=token,
        user=user
    )

# OAuth2 dependency for protecting routes
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"id": payload["sub"], "email": payload.get("email"), "role": payload.get("role")}
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ hoặc đã hết hạn")

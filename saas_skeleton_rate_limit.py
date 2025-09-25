"""
saas_skeleton_rate_limit.py

基于之前 saas_skeleton 的扩展：加入 Redis 限流（固定窗口 per-second）。
功能总结：
- 多租户 Org/User/APIKey（key_hash + key_preview）
- 用户类型：NORMAL / VIP / ENTERPRISE
- JWT 登录 / token
- API Key create/list/revoke（创建时返回明文一次）
- 双鉴权：Bearer JWT 或 x-api-key
- Redis 固定窗口限流：按 user.id，NORMAL=10 QPS, VIP=100 QPS, ENTERPRISE=unlimited
- 限流函数位于 rate_limit_check()
"""

import os
import secrets
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, List, Dict

from fastapi import FastAPI, Depends, HTTPException, status, Header, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

import redis

# -----------------------
# Config
# -----------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./saas.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-jwt-secret")
API_KEY_HASH_SECRET = os.environ.get("API_KEY_HASH_SECRET", "dev-api-hash-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Quota by user type (QPS)
API_KEY_QUOTA = {
    "NORMAL": 10,       # 10 QPS
    "VIP": 100,         # 100 QPS
    "ENTERPRISE": 0,    # 0 means unlimited in our logic
}

# Default scopes by user type
DEFAULT_SCOPES = {
    "NORMAL": ["generate:text"],
    "VIP": ["generate:text", "generate:image", "tts"],
    "ENTERPRISE": ["generate:text", "generate:image", "tts", "generate:video", "admin"],
}

# -----------------------
# Redis client
# -----------------------
# Use redis-py client; ensure redis server is accessible
rcli = redis.Redis.from_url(REDIS_URL)

# -----------------------
# DB setup
# -----------------------
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -----------------------
# Models
# -----------------------
class Org(Base):
    __tablename__ = "orgs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserTypeEnum(str, Enum):
    NORMAL = "NORMAL"
    VIP = "VIP"
    ENTERPRISE = "ENTERPRISE"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    username = Column(String(150), unique=True, index=True)
    hashed_password = Column(String(300))
    is_admin = Column(Boolean, default=False)
    user_type = Column(SQLEnum(UserTypeEnum), default=UserTypeEnum.NORMAL)
    created_at = Column(DateTime, default=datetime.utcnow)

    org = relationship("Org", backref="users")

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(128), unique=True, index=True)   # HMAC-SHA256 hex
    key_preview = Column(String(64), index=True)              # Masked preview for UI
    name = Column(String(200), nullable=True)
    scopes = Column(Text, nullable=True)  # comma-separated scopes
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User")
    org = relationship("Org")

# -----------------------
# Utilities
# -----------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(pw: str) -> str:
    return pwd_context.hash(pw)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def gen_api_key(prefix="sk", length=32) -> str:
    token = secrets.token_hex(length // 2)
    return f"{prefix}-{token}"

def mask_key(key: str) -> str:
    if not key or len(key) <= 9:
        return key
    return key[:5] + "****" + key[-4:]

def hash_key_hmac(key: str) -> str:
    return hmac.new(API_KEY_HASH_SECRET.encode(), key.encode(), hashlib.sha256).hexdigest()

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)
    to_encode.update({"iat": int(now.timestamp()), "exp": int(expire.timestamp())})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise

# -----------------------
# Rate limit logic (Redis fixed-window per-second)
# -----------------------
def rate_limit_check_by_user(user_id: int, user_type: str) -> (bool, Optional[Dict]):
    """
    Fixed-window per-second limiter.
    Returns (allowed: bool, info: dict or None)
    If user_type is ENTERPRISE -> unlimited (allowed=True).
    """
    # ENTERPRISE unlimited
    if user_type == UserTypeEnum.ENTERPRISE.value:
        return True, None

    limit = API_KEY_QUOTA.get(user_type, 10)
    if limit <= 0:
        return True, None

    now_s = int(time.time())
    key = f"rl:user:{user_id}:{now_s}"
    try:
        cur = rcli.incr(key)
        if cur == 1:
            # set expire slightly larger than 1 second to allow some jitter
            rcli.expire(key, 2)
        if cur > limit:
            return False, {"limit": limit, "current": cur}
    except redis.RedisError:
        # 在 Redis 出现错误时，采用降级策略：允许请求通过（或可改为拒绝）
        return True, None
    return True, None

# -----------------------
# Pydantic Schemas
# -----------------------
class SignupReq(BaseModel):
    org_name: str
    username: str
    password: str
    user_type: Optional[UserTypeEnum] = UserTypeEnum.NORMAL
    is_admin: Optional[bool] = False

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class APIKeyCreateReq(BaseModel):
    name: Optional[str] = None
    expires_days: Optional[int] = None
    scopes: Optional[List[str]] = None  # optional override

class APIKeyOut(BaseModel):
    id: int
    org_id: int
    user_id: int
    key: str  # when returned from create -> plaintext; when listed -> masked
    name: Optional[str]
    scopes: Optional[List[str]]
    revoked: bool
    created_at: datetime
    expires_at: Optional[datetime]

# -----------------------
# FastAPI app & DB dependency
# -----------------------
app = FastAPI(title="SaaS Multi-tenant API Key + JWT + Redis Rate Limit")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# Startup: init tables and demo data
# -----------------------
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        org = db.query(Org).filter_by(name="demo_org").first()
        if not org:
            org = Org(name="demo_org")
            db.add(org)
            db.commit()
            db.refresh(org)
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(org_id=org.id, username="admin", hashed_password=get_password_hash("password"), is_admin=True, user_type=UserTypeEnum.ENTERPRISE)
            db.add(admin)
            db.commit()
    finally:
        db.close()

# -----------------------
# Auth endpoints
# -----------------------
@app.post("/signup", summary="Create org + user (for testing / demo)")
def signup(payload: SignupReq, db: Session = Depends(get_db)):
    if db.query(Org).filter_by(name=payload.org_name).first():
        raise HTTPException(status_code=400, detail="org exists")
    org = Org(name=payload.org_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    user = User(org_id=org.id, username=payload.username, hashed_password=get_password_hash(payload.password), is_admin=payload.is_admin, user_type=payload.user_type)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"org_id": org.id, "user_id": user.id, "username": user.username}

@app.post("/token", response_model=TokenOut, summary="Username/password -> JWT")
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    payload = {"sub": str(user.id), "org": str(user.org_id), "user_type": user.user_type.value}
    token = create_access_token(payload)
    return {"access_token": token, "token_type": "bearer"}

# -----------------------
# Auth dependency: support x-api-key or Bearer
# -----------------------
def get_current_user(x_api_key: Optional[str] = Header(None), authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    # 1) API Key authentication
    if x_api_key:
        key_h = hash_key_hmac(x_api_key)
        api = db.query(APIKey).filter_by(key_hash=key_h, revoked=False).first()
        if not api:
            raise HTTPException(status_code=401, detail="Invalid API key")
        if api.expires_at and api.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="API key expired")
        user = db.query(User).filter_by(id=api.user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {"user": user, "auth_type": "api_key", "api_obj": api}

    # 2) Bearer JWT authentication
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        try:
            payload = decode_access_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = int(payload.get("sub"))
        org_id = int(payload.get("org"))
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.org_id != org_id:
            raise HTTPException(status_code=401, detail="org mismatch in token")
        return {"user": user, "auth_type": "jwt", "token_payload": payload}
    raise HTTPException(status_code=401, detail="No authentication provided")

# -----------------------
# API Key management endpoints
# -----------------------
@app.post("/apikeys", response_model=APIKeyOut, summary="Create API key (JWT required)")
def create_api_key(req: APIKeyCreateReq = Body(...), auth = Depends(get_current_user), db: Session = Depends(get_db)):
    if auth["auth_type"] != "jwt":
        raise HTTPException(status_code=403, detail="Only JWT users can create keys in this sample")
    user = auth["user"]
    quota = API_KEY_QUOTA.get(user.user_type.value, 10)
    existing_count = db.query(APIKey).filter_by(user_id=user.id, revoked=False).count()
    if existing_count >= quota:
        raise HTTPException(status_code=403, detail=f"API key quota exceeded for user type {user.user_type.value} (quota={quota})")

    clear_key = gen_api_key(prefix="sk", length=32)
    key_hash = hash_key_hmac(clear_key)
    preview = mask_key(clear_key)

    scopes = req.scopes if req.scopes is not None else DEFAULT_SCOPES.get(user.user_type.value, ["generate:text"])
    scopes_str = ",".join(scopes)

    expires_at = None
    if req.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=req.expires_days)

    api = APIKey(org_id=user.org_id, user_id=user.id, key_hash=key_hash, key_preview=preview, name=req.name, scopes=scopes_str, expires_at=expires_at)
    db.add(api)
    db.commit()
    db.refresh(api)

    # return plaintext key only once
    return {
        "id": api.id,
        "org_id": api.org_id,
        "user_id": api.user_id,
        "key": clear_key,
        "name": api.name,
        "scopes": scopes,
        "revoked": api.revoked,
        "created_at": api.created_at,
        "expires_at": api.expires_at
    }

@app.get("/apikeys", summary="List API keys for current JWT user (masked)")
def list_api_keys(auth = Depends(get_current_user), db: Session = Depends(get_db)):
    if auth["auth_type"] != "jwt":
        raise HTTPException(status_code=403, detail="Only JWT users can list keys")
    user = auth["user"]
    apis = db.query(APIKey).filter_by(user_id=user.id).all()
    out = []
    for a in apis:
        scopes = a.scopes.split(",") if a.scopes else []
        out.append({
            "id": a.id,
            "org_id": a.org_id,
            "user_id": a.user_id,
            "key": a.key_preview,
            "name": a.name,
            "scopes": scopes,
            "revoked": a.revoked,
            "created_at": a.created_at,
            "expires_at": a.expires_at
        })
    return out

@app.delete("/apikeys/{key_id}", summary="Revoke an API key")
def revoke_api_key(key_id: int, auth = Depends(get_current_user), db: Session = Depends(get_db)):
    if auth["auth_type"] != "jwt":
        raise HTTPException(status_code=403, detail="Only JWT users can revoke keys")
    user = auth["user"]
    api = db.query(APIKey).filter_by(id=key_id, user_id=user.id).first()
    if not api:
        raise HTTPException(status_code=404, detail="API key not found")
    api.revoked = True
    db.add(api)
    db.commit()
    return {"status": "revoked", "id": api.id}

# -----------------------
# Protected endpoint with rate limiting
# -----------------------
@app.post("/generate", summary="Example generation endpoint (JWT or x-api-key) with rate limiting")
def generate(payload: Dict = Body(...), auth = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    1) Authenticated via JWT or API Key (get_current_user already resolved)
    2) Rate limit check by user id & user_type
    3) Scope check for API Key auth
    """
    user = auth["user"]

    # Rate limiting: check by user.id and user.user_type
    allowed, info = rate_limit_check_by_user(user.id, user.user_type.value)
    if not allowed:
        detail = f"rate limit exceeded (limit={info['limit']}, current={info['current']})"
        raise HTTPException(status_code=429, detail=detail)

    # If API Key auth, validate scopes
    if auth["auth_type"] == "api_key":
        api_obj = auth["api_obj"]
        scopes = api_obj.scopes.split(",") if api_obj.scopes else []
        if "generate:text" not in scopes:
            raise HTTPException(status_code=403, detail="API key missing required scope")
        # Mock generation result
        return {"message": f"Generated content for org {user.org_id} by api_key user {user.username}", "payload": payload}

    # If JWT auth, simple permission check (could be extended)
    return {"message": f"Generated content for org {user.org_id} by user {user.username}", "payload": payload}

# -----------------------
# Admin endpoints (example)
# -----------------------
@app.get("/orgs/{org_id}/keys", summary="Admin: list keys for org (only same-org admin)")
def list_org_keys(org_id: int, auth = Depends(get_current_user), db: Session = Depends(get_db)):
    user = auth["user"]
    if user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    keys = db.query(APIKey).filter_by(org_id=org_id).all()
    out = []
    for a in keys:
        out.append({
            "id": a.id,
            "user_id": a.user_id,
            "key_preview": a.key_preview,
            "name": a.name,
            "scopes": a.scopes.split(",") if a.scopes else [],
            "revoked": a.revoked,
            "created_at": a.created_at
        })
    return out

# -----------------------
# Run:
# uvicorn saas_skeleton_rate_limit:app --reload
# -----------------------
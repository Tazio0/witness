from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
# REMOVED: from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
import bcrypt # ADDED: Using raw bcrypt directly
from app.core.database import get_db

router = APIRouter()

# REMOVED: pwd_context = CryptContext(...)

# JWT settings — change SECRET_KEY to something random and private in production
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # 1 week


# --- Request/Response models ---

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# --- Helpers (FIXED FOR BCRYPT) ---

def hash_password(password: str) -> str:
    """Hashes a password using raw bcrypt."""
    # bcrypt requires bytes, so we encode the string
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # Return it as a normal string to store in SQLite easily
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the hashed version."""
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)


def create_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# --- Routes ---

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest):
    """Create a new Witness account."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (body.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )

    # Use the new hash_password helper
    hashed = hash_password(body.password)
    
    cursor.execute(
        "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
        (body.email, body.username, hashed)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    token = create_token(user_id, body.username)
    return AuthResponse(access_token=token, username=body.username)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """Log in and get a JWT token."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, password_hash FROM users WHERE email = ?",
        (body.email,)
    )
    user = cursor.fetchone()
    conn.close()

    # Use the new verify_password helper
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_token(user["id"], user["username"])
    return AuthResponse(access_token=token, username=user["username"])
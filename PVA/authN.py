from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from passlib.hash import pbkdf2_sha256
import sqlite3
import logging

SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
app = FastAPI()
app.include_router(router, prefix="/auth")


def get_db():
    """Get database connection with row factory"""
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        file_path TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()
    logger.info("Database intialized successfully")


init_db()

# Pydantic models


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict

# Token generation and verification


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get current user from token"""
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "user_id": payload.get("user_id"),
        "username": payload.get("sub"),
        "email": payload.get("email")
    }

# Authentication endpoints


@router.post("/register", status_code=201)
def register(user: UserRegister):
    """Register a new user"""
    db = get_db()
    cursor = db.cursor()
    try:
        # Check if user already exists
        cursor.execute(
            "SELECT id FROM users WHERE username = ?", (user.username,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )

        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        hashed_password = pbkdf2_sha256.hash(user.password)
        # Create user
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password)
            VALUES (?, ?, ?)
        """, (user.username, user.email, hashed_password))
        db.commit()
        user_id = cursor.lastrowid
        # Get the created user
        cursor.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        new_user = cursor.fetchone()
        logger.info(f"New user registered: {user.username}")
        return {
            "message": "User registered successfully",
            "user": dict(new_user)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )
    finally:
        db.close()


@router.post("/login", response_model=Token)
def login(user: UserLogin):
    """Login user and return JWT token"""
    db = get_db()
    cursor = db.cursor()
    try:
        # Find user by username
        cursor.execute(
            "SELECT id, username, email, hashed_password FROM users WHERE username = ?",
            (user.username,)
        )
        db_user = cursor.fetchone()
        if not db_user:
            logger.warning(
                f"Login attempt for non-existent user: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        # Verify password
        if not pbkdf2_sha256.verify(user.password, db_user["hashed_password"]):
            logger.warning(f"Failed login attempt for user: {user.username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        # Prepare token data
        token_data = {
            "sub": db_user["username"],
            "user_id": db_user["id"],
            "email": db_user["email"]
        }
        # Create access token
        access_token = create_access_token(data=token_data)
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (db_user["id"],)
        )
        db.commit()
        logger.info(f"User logged in: {user.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": db_user["id"],
                "username": db_user["username"],
                "email": db_user["email"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )
    finally:
        db.close()


@router.get("/verify-token")
def verify_token_endpoint(current_user: dict = Depends(get_current_user)):
    """Verify if the provided token is valid"""
    return {
        "valid": True,
        "message": "Token is valid",
        "user": current_user,
        "timestamp": datetime.now().isoformat()
    }

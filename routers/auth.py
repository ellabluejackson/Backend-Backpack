import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from database import get_db
from security import create_access_token, decode_access_token, parse_bearer_authorization

router = APIRouter(prefix="/auth", tags=["auth"])

# bcrypt rejects passwords over 72 bytes; enforce before hashing
PW_MAX_BYTES = 72


def _hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > PW_MAX_BYTES:
        raise HTTPException(status_code=400, detail="Password is too long (max 72 bytes)")
    hashed = bcrypt.hashpw(raw, bcrypt.gensalt())
    return hashed.decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    raw = password.encode("utf-8")
    if len(raw) > PW_MAX_BYTES:
        return False
    try:
        stored = password_hash.encode("utf-8")
    except AttributeError:
        stored = str(password_hash).encode("utf-8")
    return bcrypt.checkpw(raw, stored)


class SignupIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def _normalize_email(email: str) -> str:
    value = email.strip().lower()
    if "@" not in value or "." not in value:
        raise HTTPException(status_code=400, detail="Invalid email")
    return value


@router.post("/signup")
def signup(body: SignupIn, db=Depends(get_db)):
    name = body.name.strip()
    email = _normalize_email(body.email)
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    password_hash = _hash_password(body.password)
    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    db.commit()
    row = db.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = last_insert_rowid()"
    ).fetchone()
    token = create_access_token(row["id"], row["email"])
    return {"access_token": token, "token_type": "bearer", "user": dict(row)}


@router.post("/login")
def login(body: LoginIn, db=Depends(get_db)):
    email = _normalize_email(body.email)
    row = db.execute(
        "SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(row["id"], row["email"])
    user = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me")
def me(authorization: str | None = Header(default=None), db=Depends(get_db)):
    token = parse_bearer_authorization(authorization)
    claims = decode_access_token(token)
    try:
        user_id = int(claims.get("sub", "0"))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token subject")
    row = db.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(row)

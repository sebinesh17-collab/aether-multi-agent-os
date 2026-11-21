import os, base64, hashlib, hmac
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .config import settings

oauth = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(value: str) -> str:
    salt=os.urandom(16)
    digest=hashlib.scrypt(value.encode("utf-8"),salt=salt,n=2**15,r=8,p=1,dklen=32)
    return "scrypt$32768$8$1$"+base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(digest).decode()

def verify_password(value: str, encoded: str) -> bool:
    try:
        scheme,n,r,p,salt_b64,digest_b64=encoded.split("$",5)
        if scheme!="scrypt": return False
        salt=base64.urlsafe_b64decode(salt_b64.encode()); expected=base64.urlsafe_b64decode(digest_b64.encode())
        actual=hashlib.scrypt(value.encode("utf-8"),salt=salt,n=int(n),r=int(r),p=int(p),dklen=len(expected))
        return hmac.compare_digest(actual,expected)
    except Exception: return False

def create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user.id), "email": user.email, "exp": exp}, settings.jwt_secret, algorithm="HS256")

def current_user(token: str = Depends(oauth), db: Session = Depends(get_db)) -> User:
    try: uid = int(jwt.decode(token, settings.jwt_secret, algorithms=["HS256"]).get("sub", "0"))
    except (jwt.InvalidTokenError, ValueError): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, uid)
    if not user: raise HTTPException(status_code=401, detail="User not found")
    return user

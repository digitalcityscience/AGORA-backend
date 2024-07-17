from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import database
from app.auth.config import settings
from app.schemas import user_login
from app.models import user_model

# tokenUrl come from under router/auth.py login function
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
# to get a string like this run:
# openssl rand -hex 32
# SECRET_KEY = "09d25e094faa6ca2556c818145b7a9563b93f7958f6f0f4caa6cf63b88e8d3e7"
SECRET_KEY = settings.SECRET_KEY
# ALGORITHM = "HS256"
ALGORITHM = settings.ALGORITHM
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credential_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id = str(payload.get("user_id"))
        if id is None:
            raise credential_exception
        token_data = user_login.TokenData(id=id)

    except JWTError:
        raise Exception("Invalid token")

    return token_data


def verify_refresh_token(token: str, credential_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print("payload",payload)
        # "30" keyword fo refreshing token
        if "30" in str(payload.get("user_id")).split("_"):
            id = str(payload.get("user_id")).split("_")[0]
        else:
            raise credential_exception
        if id is None:
            raise credential_exception
        token_data = user_login.TokenData(id=id)
        access_token = create_access_token(data={"user_id": id})
    except JWTError:
        raise Exception("Invalid token")

    return {
        "access_token": access_token,
        "refresh_token": token,
        "token_type": "bearer",
    }


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    print("token", token)
    token = verify_access_token(token, credentials_exception)

    user = db.query(user_model.User).filter(user_model.User.id == token.id).first()

    return user

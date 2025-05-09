from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import auth, geometry_operations, test, administrative, ligfinder,parcel_maximizer

from app.auth.database import Base
from app.auth.database import engine

from sqlalchemy.orm import Session
from app.auth.database import get_db
from fastapi import FastAPI, Depends
from sqlalchemy import text


Base.metadata.create_all(bind=engine)

app = FastAPI()
origin = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello world"}


app.include_router(test.router)
app.include_router(auth.router)
app.include_router(geometry_operations.router)
app.include_router(administrative.router)
app.include_router(ligfinder.router)
app.include_router(parcel_maximizer.router)

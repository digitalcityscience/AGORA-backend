from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import auth, test

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


# burayi kontrol edip tum  lig yapisini buna dondurmeye caliscaz
# @app.get("/sql")
# def sql_test(db: Session = Depends(get_db)):
#     # sql_text="select table_name from information_schema.columns where column_name = 'geom' AND table_name NOT in ('bike_network', 'counties_daily', 'drive_network', 'parcel', 'building', 'walk_network', 'geocoded_address', 'counties', 'pop', 'elbvertiefung',	'bezirke', 'gemarkungen', 'stadtteile', 'statistischegebiete') "
#     sql_text="SELECT * FROM parcel where gid=32"
#     result = db.execute(text(sql_text))
#     for row in result:
#         print(row)
#     return {"data":result}

app.include_router(test.router)
app.include_router(auth.router)

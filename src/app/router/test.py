from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from app.auth import database, utils, oauth2
from app.schemas import user_login
from app.models import user_model
from app.auth.config import settings

from pydantic import BaseModel

# class Item(BaseModel):
#     item_id: int


router = APIRouter(prefix="/test", tags=["Test"])


@router.get("/v1/{item_id}")
def test(
    item_id: int,
    current_user: int = Depends(oauth2.get_current_user),
    db: Session = Depends(database.get_db),
):
    print(item_id)
    return {"message": "Vote deleted successfully"}


from sqlalchemy import text
import logging


@router.get("/table/{table_name}")
def get_table(table_name: str, db: Session = Depends(database.get_db)):
    print(table_name)
    try:
        # SQL sorgusunu hazırla
        query = text(
            f"""
            SELECT json_build_object(
                'name', 'public.{table_name}', 
                'oid', (SELECT 'public.{table_name}'::regclass::oid), 
                'left', (SELECT min(ST_XMin(geom)) FROM public.{table_name}), 
                'bottom', (SELECT min(ST_YMin(geom)) FROM public.{table_name}), 
                'right', (SELECT max(ST_XMax(geom)) FROM public.{table_name}), 
                'top', (SELECT max(ST_YMax(geom)) FROM public.{table_name}),
                'type', 'FeatureCollection',
                'features', json_agg(ST_AsGeoJSON(t.*)::json ORDER BY t.name ASC)
            )
            FROM public.{table_name} AS t;
        """
        )
        print(query)
        # Sorguyu çalıştır ve sonucu al
        result = db.execute(query)
        print(result)
        table_info = result.fetchone()[0]  # İlk sütunun değerini al

        return table_info
    except Exception as error:
        print(error)
        logging.error(f"!!! Error : {error}")
        raise HTTPException(status_code=500, detail="Internal server error")

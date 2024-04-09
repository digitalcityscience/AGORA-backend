from fastapi import APIRouter, Body, status, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field,field_validator,validator
import json  
import geopandas as gpd


from app.auth import database, utils, oauth2
from app.schemas import user_login
from app.models import user_model
from app.auth.config import settings
from app.models.ligfinderModel import FilterFeatureCollection 
import app.common.geopandsFuncs as geopandsFuncs

router = APIRouter(prefix="/geometry", tags=["geometryOperations"])

@router.post("/filter",status_code=status.HTTP_201_CREATED)
def geo_filter(data: FilterFeatureCollection = Body(...)):
    try:
        gdf = gpd.read_file(data.model_dump_json(), driver='GeoJSON')
        if data.union==True:
            input_geometry = gdf.unary_union
        else:
            input_geometry = geopandsFuncs.intersect_geodataframe(gdf)
            if not input_geometry:
                raise HTTPException(status_code=409, detail="Geometry does not intersect")
        
        sql_query = """
            SELECT json_build_object('gids', json_agg(gid)) AS result
            FROM %s AS p
            WHERE ST_Intersects(p.geom, ST_GeomFromGeoJSON('%s') );
            """ %(data.tableName,json.dumps(input_geometry.__geo_interface__))
        sql_answer = database.execute_sql_query(sql_query)
        # we get the first row of the result which is geojson
        raw_data = sql_answer.fetchone()
        return raw_data[0]
    except ValueError as e:
        # Handle data validation errors
        raise HTTPException(status_code=400, detail=f"An ValueError error occurred: {e}")
    except Exception as e:  # Catch generic errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
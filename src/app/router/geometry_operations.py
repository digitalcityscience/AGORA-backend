from fastapi import APIRouter, Body, status, HTTPException, Response
from sqlalchemy.orm import Session
import json
import geopandas as gpd


from app.auth import database
from app.models.geometryOperationModel import FilterFeatureCollection
import app.common.geopandsFuncs as geopandsFuncs

router = APIRouter(prefix="/geometry", tags=["geometryOperations"])




@router.post("/filter", status_code=status.HTTP_201_CREATED)
def geo_filter(data: FilterFeatureCollection = Body(...)):
    try:
        gdf = gpd.read_file(data.model_dump_json(), driver="GeoJSON")
        if data.union == True:
            input_geometry = gdf.unary_union
        else:
            input_geometry = geopandsFuncs.intersect_geodataframe(gdf)
            if not input_geometry:
                return Response(status_code=status.HTTP_409_CONFLICT)
        sql_query = """
            SELECT json_build_object('gids', json_agg(gid)) AS result
            FROM %s AS p
            WHERE ST_Intersects(p.geom, ST_GeomFromGeoJSON('%s') );
            """ % (
            data.tableName,
            json.dumps(input_geometry.__geo_interface__)
        )
        sql_answer = database.execute_sql_query(sql_query)
        # we get the first row of the result which is geojson
        raw_data = sql_answer.fetchone()
        return raw_data[0]
    except ValueError as e:
        # Handle data validation errors
        raise HTTPException(
            status_code=400, detail=f"An ValueError error occurred: {e}"
        )
    except Exception as e:  # Catch generic errors
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )


from app.models.isochronesModel import IsochroneCreate
from app.common.isochronesFuncs import get_iso_aoi


@router.post("/isochrone", status_code=status.HTTP_201_CREATED)
def create_isochrones(data: IsochroneCreate = Body(...)):
    """
    Create isochrones by sending the center coordinates, time and mode.
    Sample request object:

    Modes: walk_network,bike_network,drive_network


    {
        "time": "3",
        "center": {
          "lng": 9.990004262251006,
          "lat": 53.55316847206518
        },
        "mode": "walk_network"
    }
    """
    try:
        time = float(data.time) * 60
        center = data.center
        lng = float(center.lng)
        lat = float(center.lat)
        mode = data.mode
        return get_iso_aoi(mode, lng, lat, time)  # done

    except ValueError as e:
        # Handle data validation errors
        raise HTTPException(
            status_code=400, detail=f"An ValueError error occurred: {e}"
        )
    except Exception as e:  # Catch generic errors
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )

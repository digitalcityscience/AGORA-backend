from fastapi import APIRouter, Body, status, HTTPException
from app.models.isochronesModel import IsochroneCreate
from app.common.isochronesFuncs import get_iso_aoi

router = APIRouter(prefix="/isochrones", tags=["isochronesOperations"])

@router.post("/create",status_code=status.HTTP_201_CREATED)
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
            time = float(data.time)*60
            center = data.center
            lng = float(center.lng)
            lat = float(center.lat)
            mode = data.mode
            return get_iso_aoi(mode, lng, lat, time)  # done

    except ValueError as e:
        # Handle data validation errors
        raise HTTPException(status_code=400, detail=f"An ValueError error occurred: {e}")
    except Exception as e:  # Catch generic errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
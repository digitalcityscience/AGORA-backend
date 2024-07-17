from pydantic import BaseModel, Field


class CenterObject(BaseModel):
    lng: float = Field(..., example=13.4)
    lat: float = Field(..., example=52.5)


class IsochroneCreate(BaseModel):
    mode: str = Field(..., example="walk_network,bike_network,drive_network")
    time: float = Field(..., example=30)
    center: CenterObject = Field(..., example={"lng": 13.4, "lat": 52.5})

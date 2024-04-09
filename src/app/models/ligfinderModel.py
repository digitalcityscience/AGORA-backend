from geojson_pydantic import Feature
from pydantic import BaseModel,field_validator,Field

class FilterFeatureCollection(BaseModel):
    type: str
    features: list[Feature] = Field(min_items=1)
    union: bool
    tableName:str='parcel'
    @field_validator("type")
    def validate_type(cls, value):
        if value != "FeatureCollection":
            raise ValueError("Invalid 'type' value. Expected 'FeatureCollection'.")
        return value





"""
# test purpose our own geojson model
class GeoFilterInput(BaseModel):
    type: str = Field(..., example="FeatureCollection")
    union: bool
    features: list[dict]
    @validator("features", each_item=True)
    def validate_feature(cls, value):
        # Check for missing 'geometry' property
        if not value.get("geometry"):
            raise ValueError("Missing 'geometry' property in feature.")

        # Ensure geometry is not empty (assuming a dictionary)
        geometry = value.get("geometry", {})
        if not geometry:
            raise ValueError("Empty 'geometry' property in feature.")
        # Validate geometry structure (optional, based on your needs)
        # You can add checks for specific keys or data types here
        # ...
        return value
    @validator("features", pre=True)
    def validate_features_length(cls, value: list[dict]) -> Optional[list[dict]]:
        # Check for empty features list
        if not value:
            raise ValueError("Missing features in GeoJSON data.")
        return value

    @field_validator("type")
    def validate_type(cls, value):
        if value != "FeatureCollection":
            raise ValueError("Invalid 'type' value. Expected 'FeatureCollection'.")
        return value



"""
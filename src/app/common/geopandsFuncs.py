import geopandas as gpd

def intersect_geodataframe(input_geodataframe):
    """
    Function to intersect geometries in a geopandas dataframe. It returns a geopandas dataframe with the intersection of all geometries in the input geopandas dataframe.

    Input: geopandas dataframe
    Output: geopandas dataframe
    """
    # create geo list
    geometries = input_geodataframe['geometry'].tolist()
    # get first geometry as a base geo
    intersection = geometries[0]
    for geometry in geometries[1:]:
        if not intersection.intersects(geometry):
            return False
        intersection = intersection.intersection(geometry)

    intersection_gdf = gpd.GeoDataFrame(geometry=[intersection], crs=input_geodataframe.crs)
    return intersection

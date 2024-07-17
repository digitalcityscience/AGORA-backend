from fastapi import APIRouter, Body, status, HTTPException
from geojson_pydantic import FeatureCollection
from app.models.ligfinderModel import TableRequest
from app.auth import database
from app.common.ligfinderFunc import generate_criteria_sql


router = APIRouter(prefix="/ligfinder", tags=["ligfinder"])

@router.post("/filter", status_code=status.HTTP_201_CREATED)
def ligfinder_filter(data: TableRequest = Body(...)):
    """
    This function filters the data based on the given criteria and metric.
    It returns the filtered data as a GeoJSON FeatureCollection.

    Sample object:
    {
      "geometry": ["1", "2"],
      "criteria": [
        {
          "status": "included",
          "data": { "type": "value", "column": ["test"], "value": "1111" }
        }
      ],
      "metric": [
        {
          "column": "test",
          "operation": ">",
          "value": "5000"
        }
      ]
    }
    """
    try:
        sql_query = """
        SELECT json_build_object(
          'type', 'FeatureCollection',
          'features', json_agg(ST_AsGeoJSON(parcel.*)::json)
        )
        FROM 
        """
        sql_query += f" {data.table_name} "
        where_clauses = []
        geometry_id = tuple(data.geometry)
        criteria = data.criteria
        metric = data.metric
        
        if geometry_id:
            where_clauses.append(f"gid IN {geometry_id}")
        if criteria:
            criteria_sql = generate_criteria_sql(criteria)
            if criteria_sql:
                where_clauses.append(criteria_sql)
        if metric:
            metric_sql_query = []
            for m in metric:
                metric_sql_query.append(
                    f"{m.column} {m.operation} {m.value}"
                )
            metric_sql_query = "(" + " AND ".join(metric_sql_query) + ")"
            where_clauses.append(metric_sql_query)

        if where_clauses:
            sql_query += " WHERE " + " AND ".join(where_clauses)

        # Print the final query for debugging
        print(f"Constructed SQL Query: {sql_query}")

        sql_answer = database.execute_sql_query(sql_query)
        raw_data = sql_answer.fetchone()

        if not raw_data or not raw_data[0] or not raw_data[0].get("features"):
            return {
                "type": "FeatureCollection",
                "features": []
            }

        print(f'{len(raw_data[0]["features"])} features found.')
        return raw_data[0]
    except ValueError as e:
        # Handle data validation errors
        raise HTTPException(
            status_code=400, detail=f"A ValueError occurred: {e}" 
        )
    except Exception as e:  # Catch generic errors
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )

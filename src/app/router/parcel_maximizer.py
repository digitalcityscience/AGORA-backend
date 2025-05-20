from fastapi import APIRouter, Body, HTTPException, status
from typing import List, Optional, Any
from pydantic import BaseModel
from app.auth import database
from app.common.ligfinderFunc import generate_criteria_sql
from app.models.ligfinderModel import MaximizerRequest

router = APIRouter(prefix="/ligfinder", tags=["ligfinder"])

@router.post("/maximizer", status_code=status.HTTP_200_OK)
def discover_parcel_islands(data: MaximizerRequest = Body(...)):
    """
    Identifies clusters (islands) of adjacent parcels using PG Routing's
    connected components algorithm, filtered by dynamic input criteria.
    Returns GeoJSON FeatureCollection of parcel clusters larger than a given threshold.
    """
    try:
        # Construct dynamic WHERE conditions based on request input
        where_clauses = []

        # Filter by geometry UUIDs if provided
        if data.geometry:
            if len(data.geometry) == 1:
                where_clauses.append(f""""UUID" = '{data.geometry[0]}'""")
            else:
                uuids = ', '.join(f"'{uuid}'" for uuid in data.geometry)
                where_clauses.append(f""""UUID" IN ({uuids})""")

        # Filter by complex LGB/XPlanung-style criteria
        if data.criteria:
            criteria_sql = generate_criteria_sql(data.criteria)
            if criteria_sql:
                where_clauses.append(criteria_sql)

        # Metric-based filtering (e.g., Shape_Area > value)
        if data.metric:
            metric_sql = " AND ".join(
                f'"{m.column}" {m.operation} {m.value}' for m in data.metric
            )
            if metric_sql:
                where_clauses.append(metric_sql)

        # GRZ (site occupancy index) filtering
        if data.grz:
            grz_sql = " AND ".join(
                f'"{g.column}" {g.operation} {g.value}' for g in data.grz
            )
            if grz_sql:
                where_clauses.append(grz_sql)

        # Combine all filters into a single WHERE clause
        final_where = " AND ".join(where_clauses) if where_clauses else "TRUE"

        # SQL query using CTEs to:
        # - Filter parcels
        # - Select edges between touching parcels
        # - Map UUIDs to PG Routing node IDs
        # - Run pgr_connectedComponents on edge list
        # - Aggregate clusters that exceed threshold area
        sql = f"""
WITH
filtered AS (
    SELECT "UUID", geom, "Shape_Area"
    FROM {data.table_name}
    WHERE {final_where}
),
touch_edges AS (
    SELECT 
        e.uuid_source,
        e.uuid_target
    FROM parcel_touch_edges_20250507 e
    JOIN filtered f1 ON e.uuid_source = f1."UUID"
    JOIN filtered f2 ON e.uuid_target = f2."UUID"
),
node_ids AS (
    SELECT "UUID", ROW_NUMBER() OVER () AS node_id
    FROM (
        SELECT uuid_source AS "UUID" FROM touch_edges
        UNION
        SELECT uuid_target AS "UUID" FROM touch_edges
    ) all_uuids
),
components AS (
    SELECT * FROM pgr_connectedComponents($$
        WITH
        filtered AS (
            SELECT "UUID" FROM {data.table_name}
            WHERE {final_where}
        ),
        touch_edges AS (
            SELECT 
                e.uuid_source,
                e.uuid_target
            FROM parcel_touch_edges_20250507 e
            JOIN filtered f1 ON e.uuid_source = f1."UUID"
            JOIN filtered f2 ON e.uuid_target = f2."UUID"
        ),
        node_ids AS (
            SELECT "UUID", ROW_NUMBER() OVER () AS node_id
            FROM (
                SELECT uuid_source AS "UUID" FROM touch_edges
                UNION
                SELECT uuid_target AS "UUID" FROM touch_edges
            ) all_uuids
        )
        SELECT 
            ROW_NUMBER() OVER () AS id,
            na.node_id AS source,
            nb.node_id AS target,
            1::float AS cost
        FROM touch_edges e
        JOIN node_ids na ON e.uuid_source = na."UUID"
        JOIN node_ids nb ON e.uuid_target = nb."UUID"
    $$)
),
clustered AS (
    SELECT c.component AS cluster_id, n."UUID"
    FROM components c
    JOIN node_ids n ON c.node = n.node_id
)
SELECT 
    cl.cluster_id,
    SUM(f."Shape_Area") AS total_area,
    STRING_AGG(cl."UUID", ', ') AS uuids,
    ST_AsGeoJSON(ST_Union(f.geom))::json AS geometry
FROM clustered cl
JOIN filtered f ON cl."UUID" = f."UUID"
GROUP BY cl.cluster_id
HAVING SUM(f."Shape_Area") > {data.threshold}
ORDER BY total_area DESC;
"""

        # Execute SQL and convert results into GeoJSON
        result = database.execute_sql_query(sql).fetchall()
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": row[3],
                    "properties": {
                        "id": row[0],
                        "total_area": row[1],
                        "uuids": row[2],
                    },
                }
                for row in result
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

from fastapi import APIRouter, Body, HTTPException, status
from typing import List, Optional, Any
from pydantic import BaseModel
from app.auth import database
from app.common.ligfinderFunc import generate_criteria_sql

router = APIRouter(prefix="/ligfinder", tags=["ligfinder"])

# Giriş modelleri
class CriteriaObject(BaseModel):
    status: str
    data: dict

class MetricCriteria(BaseModel):
    column: str
    operation: str
    value: str

class GRZCriteria(BaseModel):
    column: str
    operation: str
    value: str

class TableRequest(BaseModel):
    geometry: Optional[List[Any]]
    criteria: Optional[List[CriteriaObject]]
    metric: Optional[List[MetricCriteria]]
    grz: Optional[List[GRZCriteria]]
    table_name: Optional[str] = "parcel_grz_29042025"

@router.post("/islands", status_code=status.HTTP_200_OK)
def discover_parcel_islands(data: TableRequest = Body(...)):
    try:
        # Dinamik WHERE üretimi
        where_clauses = []

        if data.geometry:
            geometry_id = tuple(data.geometry)
            where_clauses.append(f'"UUID" IN {geometry_id}')

        if data.criteria:
            criteria_sql = generate_criteria_sql(data.criteria)
            if criteria_sql:
                where_clauses.append(criteria_sql)

        if data.metric:
            metric_sql = " AND ".join(
                f'"{m.column}" {m.operation} {m.value}' for m in data.metric
            )
            if metric_sql:
                where_clauses.append(metric_sql)

        if data.grz:
            grz_sql = " AND ".join(
                f'"{g.column}" {g.operation} {g.value}' for g in data.grz
            )
            if grz_sql:
                where_clauses.append(grz_sql)

        final_where = " AND ".join(where_clauses) if where_clauses else "TRUE"

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
ORDER BY total_area DESC;
"""

        result = database.execute_sql_query(sql).fetchall()

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": row[3],
                    "properties": {
                        "cluster_id": row[0],
                        "total_area": row[1],
                        "uuids": row[2],
                    },
                }
                for row in result
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# Parcel Cluster Discovery API - Developer Documentation

## Overview

This system enables spatial clustering of parcels (land plots) that are geometrically adjacent (touching). The objective is to discover parcel islands (connected components) based on filtered attributes and spatial relationships.

## Purpose

Instead of recalculating spatial relationships (touching parcels) on every API request—which is computationally expensive—this system precomputes the touch graph (edges) once, and uses it efficiently in an API that dynamically applies attribute and spatial filters to discover parcel clusters.

---

## Database Components

### 1. Base Parcel Table

* **Name:** `parcel_grz_29042025`
* **Key Columns:**

  * `UUID`: unique identifier
  * `geom`: geometry (polygon)
  * `Shape_Area`: area in square meters
  * `lgb_art_values`, `lgb_typ_values`, `nutzart_list_final`: attribute columns used for filtering

### 2. Touch Graph Table

* **Name:** `parcel_touch_edges_20250507`
* **Purpose:** Stores pairs of parcels that geometrically touch.
* **Schema:**

  ```sql
  CREATE TABLE parcel_touch_edges_20250507 AS
  SELECT
      a.id AS source,
      b.id AS target,
      a."UUID" AS uuid_source,
      b."UUID" AS uuid_target,
      a."Shape_Area" AS area_source,
      b."Shape_Area" AS area_target
  FROM parcel_grz_29042025 a
  JOIN parcel_grz_29042025 b
    ON ST_Touches(a.geom, b.geom)
  WHERE a.id < b.id;
  ```

This table is created once and reused. It must be indexed for performance:

```sql
CREATE INDEX idx_touch_edges_source ON parcel_touch_edges_20250507 (source);
CREATE INDEX idx_touch_edges_target ON parcel_touch_edges_20250507 (target);
```

---

## FastAPI Endpoint

### Route: `POST /ligfinder/maximizer`

### Request Body (JSON)

```json
{
  "geometry": [],
  "criteria": [...],
  "metric": [...],
  "grz": [...],
  "threshold": 10000
}
```

### Backend Processing Steps

1. **Dynamic Filtering**

   * Filters applied to the parcel base table using given criteria.
   * Produces the `filtered` CTE.
   * ⚠️ Additional filtering can be enabled to **exclude unwanted land use types** such as roads, water bodies, or forests (see Filtering Modes below).

2. **Touch Edges**

   * Only those edges are selected from `parcel_touch_edges_20250507` where both parcels are present in the `filtered` set.

3. **Graph Construction**

   * A node list is generated for filtered UUIDs.
   * An edge list (id, source, target, cost=1) is built dynamically.

4. **Connected Components**

   * `pgr_connectedComponents()` is used on the filtered graph to assign `cluster_id` values.

5. **Aggregation & Output**

   * Each cluster is aggregated into one geometry (`ST_Union`) and `total_area`.
   * Only those clusters whose total area exceeds the `threshold` are returned.

### Output Format

GeoJSON FeatureCollection of parcel clusters:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { ... },
      "properties": {
        "cluster_id": 1,
        "total_area": 10500,
        "uuids": "abc,def,ghi"
      }
    }
  ]
}
```

---

## Filtering Modes

This system supports two modes for filtering undesired parcel types (e.g. roads, water):

### ✅ Option A: Automatic Exclusion (Hardcoded)

The backend can be configured to **always exclude** parcels with unwanted `nutzungvalue` entries.

**Default exclusion list:**

```json
[
  "strassenverkehr", "weg", "fliessgewaesser", "stehendesgewaesser",
  "meer", "moor", "sumpf", "friedhof", "flugverkehr", "schiffsverkehr",
  "bahnverkehr", "platz", "wald", "gehoelz", "heide", "hafenbecken",
  "sportfreizeitunderholungsflaeche", "unlandvegetationsloseflaeche"
]
```

This can be implemented as:

```sql
AND NOT (
  nutzart_list_final ILIKE ANY (ARRAY[
    '%strassenverkehr%', '%weg%', '%fliessgewaesser%', '%stehendesgewaesser%',
    '%meer%', '%moor%', '%sumpf%', '%friedhof%', '%flugverkehr%', '%schiffsverkehr%',
    '%bahnverkehr%', '%platz%', '%wald%', '%gehoelz%', '%heide%', '%hafenbecken%',
    '%sportfreizeitunderholungsflaeche%', '%unlandvegetationsloseflaeche%'
  ])
)
```

### ✅ Option B: Manual Control (Frontend)

Alternatively, the frontend can be allowed to fully define the filter. The system applies **only what the user specifies**, including any exclusions.

This gives full flexibility to the user at the cost of potential noisy clusters if exclusions are omitted.

---

## Best Practices & Notes

* `parcel_touch_edges_20250507` should be regenerated **only when the base parcel dataset changes**.
* Filtering logic is centralized via a function like `generate_criteria_sql()`.
* `threshold` allows clients to filter out insignificant clusters.
* For performance, consider caching or rate-limiting cluster queries for large geometries.
* Encourage clients to apply water/road exclusion when the goal is identifying contiguous buildable parcels.

---

## Dependencies

* PostgreSQL + PostGIS
* pgRouting (for `pgr_connectedComponents`)
* FastAPI + SQLAlchemy for backend

---

## Authors

* Initial implementation: Mehmet Akif Ortak

from fastapi import HTTPException, status
from app.auth import database


def get_iso_aoi(mode, lng, lat, time):
    try:
        sql_query = """
          select json_build_object(
          'type', 'FeatureCollection',
          'features', json_agg(ST_AsGeoJSON(iso.*)::json)
          )
        from (SELECT ST_ConcaveHull(ST_Collect(the_geom), 0.9) from pgr_drivingDistance(
              'SELECT gid AS id, source, target, cost_time AS cost FROM %s',
            (SELECT id
        FROM %s_vertices_pgr
        ORDER BY st_setSRID(ST_MakePoint( %s, %s), 4326) <-> %s_vertices_pgr.the_geom
        LIMIT 1),%s, false
      ) AS pt JOIN %s_vertices_pgr rd ON pt.node = rd.id ) as iso;""" % (
            mode,
            mode,
            lng,
            lat,
            mode,
            time,
            mode,
        )
        sql_answer = database.execute_sql_query(sql_query)
        raw_data = sql_answer.fetchone()
        if raw_data:
            return raw_data[0]
        else:
            # Veritabanı sorgusu başarısız oldu
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Veritabanı sorgusu başarısız oldu",
            )
    except Exception as e:
        # Diğer tüm hatalar için genel bir HTTP 500 hatası fırlat
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Beklenmeyen bir hata oluştu: {e}",
        )
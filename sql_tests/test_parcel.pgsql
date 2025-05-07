SELECT COUNT(*) 
FROM parcel_grz_29042025 p
JOIN statistischegebiete s 
  ON ST_Intersects(
    p.geom,
    ST_Transform(s.geom, ST_SRID(p.geom))  -- İkinci geometriyi birincinin CRS’sine dönüştürüyoruz
  )
WHERE s."name" = 3001   -- 85 parcel
---
SELECT *
FROM parcel_grz_29042025 p
JOIN statistischegebiete s 
  ON ST_Intersects(
    p.geom,
    ST_Transform(s.geom, ST_SRID(p.geom))  -- İkinci geometriyi birincinin CRS’sine dönüştürüyoruz
  )
WHERE s."name" = 3001   -- 85 parcel


---

SELECT json_build_object(
    'type', 'FeatureCollection',
    'features', json_agg(ST_AsGeoJSON(iso.*)::json)
)
FROM (
    SELECT ST_ConcaveHull(ST_Collect(the_geom), 0.9)  -- ConcaveHull, bir noktadan oluşan çizgiler ile alandaki bölgeyi oluşturur
    FROM pgr_drivingDistance(
        'SELECT gid, source, target, cost_time AS cost FROM drive_network',  -- 'gid' kullanıyoruz
        (SELECT id  -- 'id' kullanıyoruz, doğru kolon adı
         FROM drive_network_vertices_pgr
         ORDER BY st_setSRID(ST_MakePoint(9.990004262251006, 53.55316847206518), 4326) <-> drive_network_vertices_pgr.the_geom
         LIMIT 1),  -- Verilen koordinat ile en yakın verteksi buluyor
        30,  -- 30 dakikalık isochrone süresi
        false  -- Geriye doğru yönlü bağlantılar kullanılsın mı? (false olduğu için tek yönlü bağlantı)
    ) AS pt
    JOIN drive_network_vertices_pgr rd ON pt.node = rd.id  -- Burada 'id' kullandık
) AS iso;
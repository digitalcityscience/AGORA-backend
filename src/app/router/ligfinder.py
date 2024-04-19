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

Sample object"    
{{
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
        sql_query = f"""
        select json_build_object(
          'type', 'FeatureCollection',
          'features', json_agg(ST_AsGeoJSON(parcel.*)::json)
          )
        from parcel where 
        """
        where_clauses = []
        geometry_id = tuple(data.geometry)
        criteria = data.criteria
        metric = data.metric
        
        if geometry_id:
            where_clauses.append(f" gid in {geometry_id}")
        if criteria:
            criteria_sql = generate_criteria_sql(criteria)
            where_clauses.append(criteria_sql)
        if metric:
            metric_sql_query = []
            for i in range(len(metric)):
                metric_sql_query.append(
                    f"{metric[i].column} {metric[i].operation} {metric[i].value}"
                )
            metric_sql_query = "(" +" AND ".join(metric_sql_query) + ")"
            where_clauses.append(metric_sql_query)
        sql_query += " AND ".join(where_clauses)
        sql_answer = database.execute_sql_query(sql_query)
        raw_data = sql_answer.fetchone()
        if not raw_data[0]["features"]:
            return {
            "type": "FeatureCollection",
            "features": []
            }
        print(f'{len(raw_data[0]["features"])} features found.')
        return raw_data[0]
    except ValueError as e:
        # Handle data validation errors
        raise HTTPException(
            status_code=400, detail=f"An ValueError error occurred: {e}" 
        )
    except Exception as e:  # Catch generic errors
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )


"""
{'featureIds': [162556, 186781, 160264, 195493, 234416, 57616, 158989, 43833, 57625, 57905, 11633, 57741, 9337, 57938, 57940, 58007, 58319, 59257, 59375, 59574, 64845, 72926, 104581, 159739, 165429, 249511, 160472, 160844, 64149, 58112, 219769, 159383, 159235, 6601, 12156, 57806, 58096, 105075, 159380, 159600, 159865, 160093, 160685, 160825, 165355, 165955, 104547, 164918, 160471, 58161, 198847, 58249, 160251, 165899, 19965, 33310, 10051, 39554, 55233, 57793, 58209, 58305, 63820, 64250, 104970, 159219, 160837, 164991, 165711, 166108, 195127, 195289, 233754, 251520, 159993, 160832, 219203, 159491, 2342, 12096, 32115, 41234, 57761, 57891, 57894, 57903, 58114, 58366, 59432, 59474, 70951, 72918, 83804, 106964, 107427, 128519, 159632, 159738, 160097, 160815, 165433, 166072, 45204, 73142, 160799, 57708, 58307, 59162, 65262, 243497, 84031, 165389, 150006, 159482, 159895, 161765, 165388, 165470, 166198, 2629, 6717, 7276, 9504, 11822, 30874, 38312, 58115, 59513, 61346, 65039, 65148, 70587, 72968, 105097, 159723, 163171, 164867, 165439, 165645, 89014, 165800, 166199, 58252, 73128, 2291, 232055, 57849, 63909, 72954, 88374, 107035, 159250, 159342, 2321, 59585, 168685, 160575, 160802, 165142, 165878, 191095, 57739, 59376, 38946, 42929, 45563, 48730, 57800, 57794, 57890, 57952, 160098, 58041, 59937, 65149, 106268, 149381, 159504, 159743, 160698, 162143, 163701, 165056, 165182, 165250, 190395, 140754, 107583, 3690, 8761, 166105, 58158, 105583, 159259, 159762, 164026, 165274, 165467, 166201, 195958, 63682, 72407, 159465, 159626, 210194, 190158, 59532, 190979, 11942, 50802, 166757, 160602, 160828, 165597, 166059, 194225, 195279, 84576, 57844, 34572, 248703, 234359, 7439, 33000, 46162, 57854, 57856, 59348, 88063, 140007, 159358, 159604, 160373, 160581, 168856, 189894, 64961, 70321, 165831, 2067, 11978, 58306, 104757, 73148, 59142, 188085, 59561, 59569, 146254, 165551, 168473, 32713, 57807, 72232, 189735, 209485, 106551, 164898, 59431, 59883, 63641, 103258, 37621, 44683, 57937, 59827, 120958, 149915, 159372, 160100, 164870, 165243, 189651, 159247, 159863, 194479, 223308, 32205, 53127, 57743, 58060, 58953, 59328, 59573, 159982, 160797, 164506, 164925, 165349, 165834, 188638, 160845, 64944, 65040, 65088, 72956, 103227, 104389, 159379, 194259, 194728, 58255, 59958, 159605, 160224, 2108, 39845, 57945, 59313, 59522, 64235, 57765, 57896, 58168, 70287, 104205, 150935, 159359, 160347, 160706, 164922, 165060, 166758, 168266, 169063, 189265, 190159, 191336, 194708, 194832, 103948, 106098, 65074, 142259, 18467, 34600, 45389, 57799, 58006, 64089, 159628, 159860, 160246, 160341, 160839, 161361, 165067, 165357, 165828, 169057, 231999, 248622, 57846, 159218, 166205, 159773, 165239, 6749, 45059, 72934, 42318, 55406, 158991, 95636, 273, 64332, 64397, 105068, 159229, 159512, 164866, 164928, 165526, 1464, 58256, 59292, 153071, 165637, 166202, 160474, 159461, 159637, 159888, 249514, 64222, 64376, 64846, 64919, 97603, 105795, 106879, 129288, 169252, 194030, 194512, 195039, 165607, 3039, 58098, 165548, 239993, 160838, 1003, 1769, 58108, 59290, 63725, 73784, 159240, 159518, 160222, 168676, 195833, 252251, 160092, 2109, 57908, 14857, 57993, 59261, 70037, 102661, 54485, 156884, 158963, 159258, 159355, 159869, 160496, 160596, 165647, 240002, 253292, 85396, 165649, 3739, 51533, 54776, 106330, 59123, 59231, 59331, 64107, 159849, 65026, 93156, 101782, 104542, 104832, 148789, 158946, 158984, 164901, 165069, 165143, 165426, 165635, 166109, 166195, 169250, 188771, 188878, 96244, 98589, 15497, 19036, 59995, 615, 58362, 59430, 72970, 6702, 9376, 55837, 105898, 150390, 159487, 159488, 159866, 159894, 159972, 159979, 160258, 165348, 165900, 165904, 188722, 189454, 194808, 195003, 59288, 59568, 161512, 165236, 128471, 102295, 159742, 106911, 159464, 9913, 2788, 57804, 58046, 166063, 190257, 243052, 159718, 169067, 160256, 158957, 58147, 14641, 57902, 59132, 59382, 59499, 59828, 64854, 64930, 103607, 160811, 165045, 165707, 168073, 188320, 193868, 222205, 250712, 59475, 72925, 159970, 161637, 59437, 64979, 1774, 11952, 40991, 58103, 58884, 123215, 158965, 159223, 159861, 160603, 164906, 165093, 165181, 165549, 165601, 165910, 173883, 190541, 231457, 189404, 59455, 158981, 159216, 11891, 58205, 63902, 65025, 105864, 160487, 165905, 165993, 166206, 194999, 57845, 831, 6744, 34256, 10175, 14642, 44645, 62921, 64436, 64939, 73159, 93688, 94596, 102143, 105019, 106083, 153077, 158936, 158958, 159484, 193402, 195924, 160817, 15500, 57699, 159510, 2181, 2325, 59143, 59881, 71471, 104189, 105018, 106112, 106799, 110432, 160600, 160723, 165183, 165383, 165393, 165879, 166322, 168864, 187937, 235643, 6783, 43847, 57760, 58258, 58301, 59399, 64861, 65223, 72310, 108682, 155980, 159220, 160235, 160507, 164995, 165158, 165268, 234114, 253149, 104934, 51311, 2339, 10025, 19823, 57791, 58313, 59245, 59397, 63784, 65247, 72955, 96712, 105272, 159347, 194156, 160004, 160824, 59438, 41160, 58300, 59380, 59489, 63314, 101957, 64221, 64955, 65224, 165641, 65219, 65315, 72913, 79226, 159995, 160005, 160499, 165832, 168861, 222542, 237160, 246365, 57750, 88969, 57958, 166102, 169249],
 'excludeTags': [{'name': '082_2480 Landesbetrieb Erziehung und Beratung (LEB)', 'columns': ['T_1_47_A'], 
'filterType': 'value', 'value': '082_2480'}, {'name': '082 Landesbetriebe - alle', 'columns': ['art_1_47'], 'filterType': 'value', 'value': '082'}], 
'includeTags': [{'name': '081_2902 AGV (belastet mit EBR)', 'columns': ['T_1_47_A'], 
'filterType': 'value', 'value': '081_2902'}, {'name': '081_2901 AGV (ohne EBR)', 'columns': ['T_1_47_A'], 'filterType': 'value', 'value': '081_2901'}], 'operator': 'OR'}
"""

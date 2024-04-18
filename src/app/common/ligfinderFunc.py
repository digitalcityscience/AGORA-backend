
def generate_sql_criteria_clause(criteria):
    """
    This function generates the SQL query for the criteria.

    Args:
        criteria: List of criteria objects.    
    Returns:
        SQL query string.
    
    """
    included_sql_query = " "
    excluded_sql_query = " "
    for i in range(len(criteria)):
        if criteria[i].status == "excluded":
            for j in criteria[i].data.column:
                if criteria[i].data.type == "value":
                    excluded_sql_query +=" " + f"{j} not in ('{criteria[i].data.value}')" + " or"
                elif criteria[i].data.type == "prozent":
                    excluded_sql_query +=" " + f"({j} in (0,null))" + " or"

        if criteria[i].status == "included":
            for j in criteria[i].data.column:
                if criteria[i].data.type == "value":
                    included_sql_query +=" " + f"{j} = '{criteria[i].data.value}'" + " or"
                elif criteria[i].data.type == "prozent":
                    included_sql_query +=" " + f"{j} > 0" + " or"
        
    
    if included_sql_query:
        included_sql_query = included_sql_query[:-2]
    if not included_sql_query:
        excluded_sql_query = excluded_sql_query[:-2]
    sql_query = excluded_sql_query+" " + "(" + included_sql_query + ")"
    return sql_query
################### -------------------------------
def generate_criteria_sql(criteria):
    """
    Generates SQL WHERE clause based on the provided criteria.

    Args:
        criteria (list[dict]): List of criteria objects with the following structure:
            - status (str): "included" or "excluded"
            - data:
                - type (str): "value" or "prozent" (percent).
                - column (list[str]): Column names for the criteria.
                - value (str, optional): Value for "value" type criteria.

    Returns:
        str: The generated SQL WHERE clause (empty string if no criteria).
    """
    # print("from func")
    # print(criteria)
    included= []
    excluded = []
    where_clauses = []
    for criterion in criteria:
        if criterion.status == "included":
            for column in criterion.data.column:
                if criterion.data.type == "value":
                    included.append(f"{column} = '{criterion.data.value}'")
                elif criterion.data.type  == "prozent":
                    included.append(f"{column} > 0")

        elif criterion.status == "excluded":
            if criterion.data.type == "value":
                for column in criterion.data.column:
                    excluded.append(f"{column} is distinct from '{criterion.data.value}'")
            elif criterion.data.type == "prozent":
                for column in criterion.data.column:
                    excluded.append(f"{column} IN (0, null)")

    if not included and excluded:
        return ""
    included_clause = " OR ".join(included)
    excluded_clause = " OR ".join(excluded)
    where_clauses.append(f"({excluded_clause})")
    where_clauses.append(f"({included_clause})")
    where_clause_str = " OR ".join(where_clauses)
    # print("whereeee")
    print(where_clause_str)
    return where_clause_str




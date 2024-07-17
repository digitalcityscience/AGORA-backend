def generate_criteria_sql(criteria):
    """
    Generates SQL WHERE clause based on the provided criteria.

    Args:
        criteria (list): List of criteria objects with the following structure:
            - status (str): "included" or "excluded"
            - data:
                - type (str): "value" or "prozent" (percent).
                - column (list[str]): Column names for the criteria.
                - value (str, optional): Value for "value" type criteria.

    Returns:
        str: The generated SQL WHERE clause (empty string if no criteria).
    """
    included = []
    excluded = []
    where_clauses = []

    for criterion in criteria:
        if criterion.status == "included":
            for column in criterion.data.column:
                if criterion.data.type == "value":
                    included.append(f"{column} = '{criterion.data.value}'")
                elif criterion.data.type == "prozent":
                    included.append(f"{column} > 0")
        elif criterion.status == "excluded":
            for column in criterion.data.column:
                if criterion.data.type == "value":
                    excluded.append(f"{column} IS DISTINCT FROM '{criterion.data.value}'")
                elif criterion.data.type == "prozent":
                    excluded.append(f"{column} IN (0, null)")

    if included:
        included_clause = " OR ".join(included)
        where_clauses.append(f"({included_clause})")
    
    if excluded:
        excluded_clause = " OR ".join(excluded)
        where_clauses.append(f"({excluded_clause})")
    
    if not where_clauses:
        return ""

    where_clause_str = " AND ".join(where_clauses)
    return where_clause_str

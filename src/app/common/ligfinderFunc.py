MAX_VALUE_LENGTH = 255   # Max characters per filter value — prevents DoS via long strings
MAX_LIST_SIZE = 100      # Max values per list — prevents DoS via large SQL arrays
MAX_CRITERIA_ITEMS = 50  # Max criteria items per call — prevents DoS via query overload


def _sanitise_list(raw_list) -> list:
    """
    Clean a list of filter values before SQL generation.
    Removes: None, empty strings, whitespace-only, null bytes, oversized values.
    Converts: integers to strings.
    Limits: list to MAX_LIST_SIZE items.
    """
    if not raw_list:
        return []

    clean = []

    for val in raw_list:
        # Skip None values
        if val is None:
            continue

        # Convert to string and strip whitespace
        val = str(val).strip()
        if not val:
            continue

        # Remove null bytes BEFORE length check to prevent null byte injection
        val = val.replace('\x00', '')
        if not val:
            continue

        # Skip values exceeding max length
        if len(val) > MAX_VALUE_LENGTH:
            continue

        clean.append(val)

    # Truncate to MAX_LIST_SIZE to prevent oversized SQL arrays
    return clean[:MAX_LIST_SIZE]


def generate_criteria_sql(criteria):
    """
    Build a parameterised SQL WHERE clause from a list of criteria items.

    Returns a tuple of (sql_string, params) where:
        - sql_string contains %s placeholders instead of raw values
        - params is a flat list of values to pass to the DB driver

    Usage with psycopg2:
        sql, params = generate_criteria_sql(criteria)
        cursor.execute(f"SELECT * FROM parcels WHERE {sql}", params)

    Why parameterised:
        Passing values separately means the DB driver handles all escaping.
        SQL injection is impossible because values never touch the SQL string.
    """
    if len(criteria) > MAX_CRITERIA_ITEMS:
        raise ValueError(
            f"Too many criteria items: {len(criteria)}. Maximum is {MAX_CRITERIA_ITEMS}."
        )

    included = []
    excluded = []
    where_clauses = []
    params = []  # flat list of all values — passed separately to DB driver

    for item in criteria:
        data = item.data
        status = item.status

        if not isinstance(data, dict):
            continue

        is_included = status == "included"
        clause = None

        # LGB ART (has children => art filter)
        if "children" in data:
            art_list = _sanitise_list(data.get("art"))
            if art_list:
                # One %s placeholder per value — DB driver fills these in safely
                placeholders = ', '.join(['%s'] * len(art_list))
                clause = f"ARRAY[{placeholders}]::text[] && string_to_array(lgb_art_values, ',')"
                params.extend(art_list)

        # LGB TYP (has typ, no children => typ filter)
        elif "typ" in data:
            typ_list = _sanitise_list(data.get("typ"))
            if typ_list:
                placeholders = ', '.join(['%s'] * len(typ_list))
                clause = f"ARRAY[{placeholders}]::text[] && string_to_array(lgb_typ_values, ',')"
                params.extend(typ_list)

        # Nutzung
        elif "nutzungvalue" in data:
            nutzung_list = _sanitise_list(data.get("nutzungvalue"))
            if nutzung_list:
                placeholders = ', '.join(['%s'] * len(nutzung_list))
                clause = f"ARRAY[{placeholders}]::text[] && string_to_array(nutzart_list_final, ',')"
                params.extend(nutzung_list)

        # Add to included or excluded lists
        if clause:
            if is_included:
                included.append(clause)
            else:
                # NOT wraps the clause — params order is unchanged
                excluded.append(f"NOT ({clause})")

    # Final SQL
    if included:
        where_clauses.append("(" + " OR ".join(included) + ")")
    if excluded:
        where_clauses.append("(" + " AND ".join(excluded) + ")")

    sql = " AND ".join(where_clauses)
    return sql, params
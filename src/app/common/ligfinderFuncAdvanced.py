from app.models.ligfinderModelAdvanced import CriteriaBlock, CriteriaCondition

DEFAULT_MAX_VALUE_LENGTH = 255   # Max characters per filter value — prevents DoS via long strings
DEFAULT_MAX_LIST_SIZE = 200      # Max values per list — prevents DoS via large SQL arrays
DEFAULT_MAX_CRITERIA_ITEMS = 100 # Max criteria items per call — prevents DoS via query overload


class CriteriaLimitExceeded(ValueError):
    """Raised when input exceeds a configured safety limit.
    Callers should catch this and return a 4xx, not let it bubble as a 500."""
    pass


def _sanitise_list(raw_list, max_value_length: int) -> list:
    """
    Clean a list of filter values before SQL generation.
    Does NOT enforce list size — caller rejects oversized lists.
    Removes: None, empty strings, whitespace-only, null bytes.
    Converts: integers to strings.
    Raises CriteriaLimitExceeded if any value exceeds max_value_length.
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

        # Reject values exceeding max length — silent drop would give partial results
        if len(val) > max_value_length:
            raise CriteriaLimitExceeded(
                f"Filter value exceeds maximum length of {max_value_length} characters: "
                f"{val[:40]!r}{'...' if len(val) > 40 else ''}"
            )

        clean.append(val)

    # No size limit enforced here — caller checks len(clean) against
    # max_list_size and raises CriteriaLimitExceeded if it's too large.
    return clean


def generate_criteria_sql(
    criteria,
    max_value_length: int = DEFAULT_MAX_VALUE_LENGTH,
    max_list_size: int = DEFAULT_MAX_LIST_SIZE,
    max_criteria_items: int = DEFAULT_MAX_CRITERIA_ITEMS,
):
    """
    Build a parameterised SQL WHERE clause from a list of criteria items.

    Returns a tuple of (sql_string, params) where:
        - sql_string contains :p0, :p1, ... named placeholders
        - params is a dict of {"p0": value, "p1": value, ...}

    Usage with SQLAlchemy:
        from sqlalchemy import text
        sql, params = generate_criteria_sql(criteria)
        connection.execute(text(f"SELECT * FROM parcels WHERE {sql}"), params)

    Why named parameters:
        SQLAlchemy's text() binds by name regardless of the underlying DBAPI.
        Passing values separately means SQL injection is impossible — the driver
        handles all escaping, values never touch the SQL string.

    Raises:
        CriteriaLimitExceeded — oversized input is rejected, not silently
        truncated, so results are never partial without an error.
    """
    # Reject too many criteria items outright — do not process a partial set
    if len(criteria) > max_criteria_items:
        raise CriteriaLimitExceeded(
            f"Too many criteria items: {len(criteria)}. Maximum is {max_criteria_items}."
        )

    included = []
    excluded = []
    where_clauses = []
    params = {}       # named placeholders — SQLAlchemy text() requires a dict, not a list
    param_counter = 0

    def _next_placeholders(values):
        # Registers each value under a unique name and returns its :pN references
        nonlocal param_counter
        names = []
        for v in values:
            name = f"p{param_counter}"
            params[name] = v
            names.append(f":{name}")
            param_counter += 1
        return names

    for item in criteria:
        data = item.data
        status = item.status

        # Skip items whose data is not a dict — prevents crash on None/string data
        if not isinstance(data, dict):
            continue

        is_included = status == "included"
        clause = None

        # LGB ART (has children => art filter)
        if "children" in data:
            art_list = _sanitise_list(data.get("art"), max_value_length)
            if art_list:
                # Reject rather than truncate — a partial list gives silently wrong results
                if len(art_list) > max_list_size:
                    raise CriteriaLimitExceeded(
                        f"Art list has {len(art_list)} values, exceeds max_list_size={max_list_size}."
                    )
                placeholders = ', '.join(_next_placeholders(art_list))
                clause = f"ARRAY[{placeholders}]::text[] && string_to_array(lgb_art_values, ',')"

        # LGB TYP (has typ, no children => typ filter)
        elif "typ" in data:
            typ_list = _sanitise_list(data.get("typ"), max_value_length)
            if typ_list:
                if len(typ_list) > max_list_size:
                    raise CriteriaLimitExceeded(
                        f"Typ list has {len(typ_list)} values, exceeds max_list_size={max_list_size}."
                    )
                placeholders = ', '.join(_next_placeholders(typ_list))
                clause = f"ARRAY[{placeholders}]::text[] && string_to_array(lgb_typ_values, ',')"

        # Nutzung
        elif "nutzungvalue" in data:
            nutzung_list = _sanitise_list(data.get("nutzungvalue"), max_value_length)
            if nutzung_list:
                if len(nutzung_list) > max_list_size:
                    raise CriteriaLimitExceeded(
                        f"Nutzung list has {len(nutzung_list)} values, exceeds max_list_size={max_list_size}."
                    )
                placeholders = ', '.join(_next_placeholders(nutzung_list))
                clause = f"ARRAY[{placeholders}]::text[] && string_to_array(nutzart_list_final, ',')"

        # Add to included or excluded lists
        if clause:
            if is_included:
                included.append(clause)
            else:
                # NOT wraps the clause — params dict is unaffected by wrapping
                excluded.append(f"NOT ({clause})")

    # Final SQL
    if included:
        where_clauses.append("(" + " OR ".join(included) + ")")
    if excluded:
        where_clauses.append("(" + " AND ".join(excluded) + ")")

    sql = " AND ".join(where_clauses)
    return sql, params


# ══════════════════════════════════════════════════════════════════════════════
# Advanced (block-based) criteria tree
#
# The frontend builds the exact same tree to drive its MapLibre pre-filter
# (see AGORA/src/store/ligfinder/criteriaAdvanced.ts), so this compiler and
# that one must stay in lock-step: same attribute->column map, same
# exact-token matching semantics, same null handling.
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_MAX_TREE_DEPTH = 10  # Max block nesting — prevents DoS via deeply nested trees

CRITERIA_ATTRIBUTE_COLUMN = {
    "art": "lgb_art_values",
    "typ": "lgb_typ_values",
    "nutzung": "nutzart_list_final",
}


def generate_criteria_tree_sql(
    root,
    max_value_length: int = DEFAULT_MAX_VALUE_LENGTH,
    max_list_size: int = DEFAULT_MAX_LIST_SIZE,
    max_conditions: int = DEFAULT_MAX_CRITERIA_ITEMS,
    max_depth: int = DEFAULT_MAX_TREE_DEPTH,
):
    """
    Build a parameterised SQL WHERE clause from an advanced criteria tree
    (CriteriaBlock / CriteriaCondition nodes).

    Returns (sql_string, params) like generate_criteria_sql, but placeholders
    are named :c0, :c1, ... so they never collide with the flat compiler's :pN.

    Semantics:
        - condition: the parcel's comma-separated column shares at least one
          exact token with `values`; `negate` wraps it in NOT (...)
        - NULL columns are treated as empty, so a negated condition keeps them
        - block: children joined by its operator; empty children/blocks are pruned

    Raises:
        CriteriaLimitExceeded — too deep, too many conditions, or an oversized value/list.
    """
    params = {}
    param_counter = 0
    condition_count = 0

    def _next_placeholders(values):
        nonlocal param_counter
        names = []
        for v in values:
            name = f"c{param_counter}"
            params[name] = v
            names.append(f":{name}")
            param_counter += 1
        return names

    def _compile(node, depth):
        nonlocal condition_count
        if depth > max_depth:
            raise CriteriaLimitExceeded(
                f"Criteria tree is nested deeper than max_depth={max_depth}."
            )

        if node.type == "condition":
            condition_count += 1
            if condition_count > max_conditions:
                raise CriteriaLimitExceeded(
                    f"Too many criteria conditions. Maximum is {max_conditions}."
                )
            values = _sanitise_list(node.values, max_value_length)
            if not values:
                return ""
            if len(values) > max_list_size:
                raise CriteriaLimitExceeded(
                    f"{node.attribute} list has {len(values)} values, exceeds max_list_size={max_list_size}."
                )
            column = CRITERIA_ATTRIBUTE_COLUMN[node.attribute]
            placeholders = ', '.join(_next_placeholders(values))
            clause = (
                f"ARRAY[{placeholders}]::text[] && "
                f"string_to_array(coalesce({column}, ''), ',')"
            )
            return f"NOT ({clause})" if node.negate else clause

        # block node
        parts = [p for p in (_compile(child, depth + 1) for child in node.children) if p]
        if not parts:
            return ""
        joiner = " AND " if node.operator == "and" else " OR "
        return "(" + joiner.join(parts) + ")"

    sql = _compile(root, 1)
    return sql, params


def _normalise_operator(op, default: str, label: str) -> str:
    op = (op or default).strip().lower()
    if op not in ("and", "or"):
        raise ValueError(f"Invalid {label}: {op!r}. Expected 'AND' or 'OR'.")
    return op


def _legacy_item_to_condition(item):
    """Map a flat {data, status} criteria item onto a CriteriaCondition (or None)."""
    data = item.data
    if not isinstance(data, dict):
        return None
    if "children" in data:
        attribute, raw = "art", data.get("art")
    elif "typ" in data:
        attribute, raw = "typ", data.get("typ")
    elif "nutzungvalue" in data:
        attribute, raw = "nutzung", data.get("nutzungvalue")
    else:
        return None
    if not isinstance(raw, list):
        return None
    return CriteriaCondition(
        attribute=attribute,
        values=[str(v) for v in raw if v is not None],
        negate=item.status != "included",
    )


def groups_to_criteria_tree(groups, between_groups_operator=None):
    """
    Convert the two-level `groups` request format into an advanced criteria tree,
    so `inner_operator` / `between_groups_operator` are actually honoured.

    Each group becomes:  (included_1 <inner_op> included_2 ...) AND NOT excluded_1 AND ...
    i.e. excluded items keep their flat-list meaning ("must not match") regardless
    of the inner operator. Groups are then joined by `between_groups_operator`.
    """
    between = _normalise_operator(between_groups_operator, "and", "between_groups_operator")
    blocks = []
    for group in groups:
        inner = _normalise_operator(group.inner_operator, "or", "inner_operator")
        conditions = [c for c in (_legacy_item_to_condition(i) for i in group.criteria) if c]
        included = [c for c in conditions if not c.negate]
        excluded = [c for c in conditions if c.negate]
        blocks.append(CriteriaBlock(
            operator="and",
            children=[CriteriaBlock(operator=inner, children=included), *excluded],
        ))
    return CriteriaBlock(operator=between, children=blocks)


def build_request_criteria_sql(data):
    """
    Compile whichever criteria format a TableRequest / MaximizerRequest carries.
    Precedence: criteria_group (advanced tree) > groups > criteria (flat list).
    Returns (sql_string, params); ("", {}) when no criteria are given.
    """
    if data.criteria_group:
        return generate_criteria_tree_sql(data.criteria_group)
    if data.groups:
        tree = groups_to_criteria_tree(data.groups, data.between_groups_operator)
        return generate_criteria_tree_sql(tree)
    if data.criteria:
        return generate_criteria_sql(data.criteria)
    return "", {}

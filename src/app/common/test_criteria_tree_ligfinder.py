import pytest
from pydantic import ValidationError
from unittest.mock import MagicMock

from app.models.ligfinderModelAdvanced import (
    CriteriaBlock,
    CriteriaCondition,
    Group,
    CriteriaGroup,
    TableRequest,
)
from .ligfinderFuncAdvanced import (
    generate_criteria_tree_sql,
    groups_to_criteria_tree,
    build_request_criteria_sql,
    CriteriaLimitExceeded,
    DEFAULT_MAX_LIST_SIZE,
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def cond(attribute: str, values, negate: bool = False) -> CriteriaCondition:
    return CriteriaCondition(attribute=attribute, values=values, negate=negate)


def block(operator: str, *children) -> CriteriaBlock:
    return CriteriaBlock(operator=operator, children=list(children))


def make_item(status: str, data: dict) -> MagicMock:
    item = MagicMock()
    item.status = status
    item.data = data
    return item


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Model parsing (wire shape shared with the frontend)
# ══════════════════════════════════════════════════════════════════════════════

class TestModelParsing:

    def test_nested_tree_parses_from_json(self):
        req = TableRequest.model_validate({
            "geometry": [],
            "criteria_group": {
                "type": "group", "operator": "or", "children": [
                    {"type": "condition", "attribute": "art", "values": ["1000"]},
                    {"type": "group", "operator": "and", "children": [
                        {"type": "condition", "attribute": "typ", "values": ["A"], "negate": True},
                    ]},
                ],
            },
        })
        root = req.criteria_group
        assert isinstance(root.children[0], CriteriaCondition)
        assert isinstance(root.children[1], CriteriaBlock)
        assert root.children[1].children[0].negate is True

    def test_unknown_attribute_is_rejected(self):
        with pytest.raises(ValidationError):
            CriteriaCondition(attribute="lgb_art_values; DROP TABLE x", values=["1"])

    def test_unknown_operator_is_rejected(self):
        with pytest.raises(ValidationError):
            CriteriaBlock(operator="xor", children=[])

    def test_criteria_group_defaults_to_none(self):
        assert TableRequest().criteria_group is None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — SQL generation
# ══════════════════════════════════════════════════════════════════════════════

class TestTreeSql:

    def test_single_condition(self):
        sql, params = generate_criteria_tree_sql(block("and", cond("art", ["1000"])))
        assert sql == "(ARRAY[:c0]::text[] && string_to_array(coalesce(lgb_art_values, ''), ','))"
        assert params == {"c0": "1000"}

    def test_attribute_column_mapping(self):
        sql, _ = generate_criteria_tree_sql(block(
            "and", cond("art", ["a"]), cond("typ", ["t"]), cond("nutzung", ["n"])
        ))
        assert "coalesce(lgb_art_values, '')" in sql
        assert "coalesce(lgb_typ_values, '')" in sql
        assert "coalesce(nutzart_list_final, '')" in sql

    def test_or_block(self):
        sql, _ = generate_criteria_tree_sql(block("or", cond("art", ["a"]), cond("typ", ["t"])))
        assert " OR " in sql and " AND " not in sql

    def test_negate_wraps_in_not(self):
        sql, _ = generate_criteria_tree_sql(block("and", cond("art", ["a"], negate=True)))
        assert sql.startswith("(NOT (ARRAY[:c0]")

    def test_nested_blocks_keep_structure(self):
        tree = block(
            "or",
            block("and", cond("art", ["a"]), cond("typ", ["t"])),
            cond("nutzung", ["n"]),
        )
        sql, params = generate_criteria_tree_sql(tree)
        assert sql == (
            "(("
            "ARRAY[:c0]::text[] && string_to_array(coalesce(lgb_art_values, ''), ',')"
            " AND "
            "ARRAY[:c1]::text[] && string_to_array(coalesce(lgb_typ_values, ''), ',')"
            ")"
            " OR "
            "ARRAY[:c2]::text[] && string_to_array(coalesce(nutzart_list_final, ''), ',')"
            ")"
        )
        assert params == {"c0": "a", "c1": "t", "c2": "n"}

    def test_empty_conditions_and_blocks_are_pruned(self):
        tree = block("and", cond("art", []), block("or"), cond("typ", ["t"]))
        sql, params = generate_criteria_tree_sql(tree)
        assert sql == "(ARRAY[:c0]::text[] && string_to_array(coalesce(lgb_typ_values, ''), ','))"
        assert params == {"c0": "t"}

    def test_fully_empty_tree_returns_empty(self):
        assert generate_criteria_tree_sql(block("and")) == ("", {})
        assert generate_criteria_tree_sql(block("or", block("and", cond("art", [])))) == ("", {})

    def test_values_are_sanitised(self):
        sql, params = generate_criteria_tree_sql(block("and", cond("art", ["  a  ", "", "   ", "b\x00"])))
        assert params == {"c0": "a", "c1": "b"}
        assert sql.count(":c") == 2

    def test_injection_payload_stays_in_params(self):
        payload = "a') OR 1=1 --"
        sql, params = generate_criteria_tree_sql(block("and", cond("art", [payload])))
        assert payload not in sql
        assert params["c0"] == payload


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Limits
# ══════════════════════════════════════════════════════════════════════════════

class TestTreeLimits:

    def test_too_deep_is_rejected(self):
        tree = cond("art", ["a"])
        for _ in range(5):
            tree = block("and", tree)
        with pytest.raises(CriteriaLimitExceeded):
            generate_criteria_tree_sql(tree, max_depth=4)

    def test_depth_at_limit_is_allowed(self):
        tree = cond("art", ["a"])
        for _ in range(3):
            tree = block("and", tree)
        sql, _ = generate_criteria_tree_sql(tree, max_depth=4)
        assert sql

    def test_too_many_conditions_is_rejected(self):
        tree = block("or", *[cond("art", [str(i)]) for i in range(4)])
        with pytest.raises(CriteriaLimitExceeded):
            generate_criteria_tree_sql(tree, max_conditions=3)

    def test_oversized_list_is_rejected(self):
        tree = block("and", cond("art", [str(i) for i in range(DEFAULT_MAX_LIST_SIZE + 1)]))
        with pytest.raises(CriteriaLimitExceeded):
            generate_criteria_tree_sql(tree)

    def test_oversized_value_is_rejected(self):
        with pytest.raises(CriteriaLimitExceeded):
            generate_criteria_tree_sql(block("and", cond("art", ["x" * 300])))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — `groups` format is compiled through the tree
# ══════════════════════════════════════════════════════════════════════════════

class TestGroupsConversion:

    def test_inner_and_between_operators_are_honoured(self):
        groups = [
            Group(inner_operator="AND", criteria=[
                CriteriaGroup(status="included", data={"children": True, "art": ["a"]}),
                CriteriaGroup(status="included", data={"typ": ["t"]}),
            ]),
            Group(inner_operator="OR", criteria=[
                CriteriaGroup(status="included", data={"nutzungvalue": ["n"]}),
            ]),
        ]
        tree = groups_to_criteria_tree(groups, "OR")
        sql, params = generate_criteria_tree_sql(tree)
        assert sql == (
            "((("
            "ARRAY[:c0]::text[] && string_to_array(coalesce(lgb_art_values, ''), ',')"
            " AND "
            "ARRAY[:c1]::text[] && string_to_array(coalesce(lgb_typ_values, ''), ',')"
            "))"
            " OR "
            "((ARRAY[:c2]::text[] && string_to_array(coalesce(nutzart_list_final, ''), ','))))"
        )
        assert params == {"c0": "a", "c1": "t", "c2": "n"}

    def test_excluded_items_are_always_and_not(self):
        groups = [Group(inner_operator="OR", criteria=[
            CriteriaGroup(status="included", data={"typ": ["t1"]}),
            CriteriaGroup(status="included", data={"typ": ["t2"]}),
            CriteriaGroup(status="excluded", data={"typ": ["t3"]}),
        ])]
        sql, _ = generate_criteria_tree_sql(groups_to_criteria_tree(groups))
        # (t1 OR t2) AND NOT t3
        assert sql.startswith("(((ARRAY[:c0]")
        assert " OR ARRAY[:c1]" in sql
        assert ") AND NOT (ARRAY[:c2]" in sql

    def test_default_operators(self):
        tree = groups_to_criteria_tree([Group(criteria=[])], None)
        assert tree.operator == "and"
        assert tree.children[0].children[0].operator == "or"

    def test_invalid_operator_raises_value_error(self):
        with pytest.raises(ValueError):
            groups_to_criteria_tree([Group(inner_operator="XOR", criteria=[])])
        with pytest.raises(ValueError):
            groups_to_criteria_tree([], "NAND")

    def test_unrecognised_items_are_skipped(self):
        groups = [Group(criteria=[
            CriteriaGroup(status="included", data={"unknown": ["x"]}),
            CriteriaGroup(status="included", data={"typ": "not-a-list"}),
        ])]
        assert generate_criteria_tree_sql(groups_to_criteria_tree(groups)) == ("", {})

    def test_integer_values_are_stringified(self):
        groups = [Group(criteria=[CriteriaGroup(status="included", data={"typ": [1, None, 2]})])]
        _, params = generate_criteria_tree_sql(groups_to_criteria_tree(groups))
        assert params == {"c0": "1", "c1": "2"}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Request dispatch precedence
# ══════════════════════════════════════════════════════════════════════════════

class TestBuildRequestCriteriaSql:

    def test_criteria_group_wins(self):
        req = TableRequest(
            criteria_group=block("and", cond("art", ["tree"])),
            groups=[Group(criteria=[CriteriaGroup(status="included", data={"typ": ["grp"]})])],
            criteria=[{"status": "included", "data": {"typ": ["flat"]}}],
        )
        _, params = build_request_criteria_sql(req)
        assert list(params.values()) == ["tree"]

    def test_groups_before_flat_criteria(self):
        req = TableRequest(
            groups=[Group(criteria=[CriteriaGroup(status="included", data={"typ": ["grp"]})])],
            criteria=[{"status": "included", "data": {"typ": ["flat"]}}],
        )
        _, params = build_request_criteria_sql(req)
        assert list(params.values()) == ["grp"]

    def test_flat_criteria_uses_legacy_compiler(self):
        req = TableRequest(criteria=[{"status": "included", "data": {"typ": ["flat"]}}])
        sql, params = build_request_criteria_sql(req)
        assert params == {"p0": "flat"}
        assert "coalesce" not in sql

    def test_no_criteria(self):
        assert build_request_criteria_sql(TableRequest()) == ("", {})


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Maximizer literal embedding (inside pgr_connectedComponents $$...$$)
# ══════════════════════════════════════════════════════════════════════════════

class TestEmbedParams:

    @pytest.fixture
    def embed(self):
        from app.router.parcel_maximizer import _embed_params
        return _embed_params

    def test_prefix_keys_do_not_clobber_each_other(self, embed):
        params = {f"c{i}": f"v{i}" for i in range(11)}
        sql = "ARRAY[:c1, :c10]::text[]"
        assert embed(sql, params) == "ARRAY['v1', 'v10']::text[]"

    def test_embedded_values_are_not_rescanned(self, embed):
        params = {"c0": ":c1", "c1": " OR TRUE OR "}
        assert embed("ARRAY[:c0, :c1]", params) == "ARRAY[':c1', ' OR TRUE OR ']"

    def test_casts_and_unknown_refs_untouched(self, embed):
        assert embed("x::text = :other", {"c0": "a"}) == "x::text = :other"

from typing import List, Optional, Any, Union, Annotated, Literal
from pydantic import BaseModel, Field


class CriteriaItem(BaseModel):
    type: str
    column: List[Any]
    value: str


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

class CriteriaGroup(BaseModel):
    data: dict
    status: str

class Group(BaseModel):
    inner_operator: Optional[str] = "OR"
    criteria: List[CriteriaGroup]


# Advanced (block-based) criteria tree. The frontend builds the same tree to
# drive its MapLibre pre-filter (AGORA/src/store/ligfinder/criteriaAdvanced.ts),
# so the wire shape — including the "group"/"condition" discriminators — must
# stay in lock-step with it.
class CriteriaCondition(BaseModel):
    """A single leaf condition in an advanced criteria tree, e.g. art/typ/nutzung IN (values)."""
    type: Literal["condition"] = "condition"
    attribute: Literal["art", "typ", "nutzung"]
    values: List[str]
    negate: bool = False


class CriteriaBlock(BaseModel):
    """A block (or block of blocks) combining conditions/sub-blocks with a single and/or operator."""
    type: Literal["group"] = "group"
    operator: Literal["and", "or"]
    children: List["CriteriaNode"]


CriteriaNode = Annotated[Union[CriteriaBlock, CriteriaCondition], Field(discriminator="type")]
CriteriaBlock.model_rebuild()


class TableRequest(BaseModel):
    geometry: Optional[List[Any]] = None
    criteria: Optional[List[CriteriaObject]] = None
    groups: Optional[List[Group]] = None
    between_groups_operator: Optional[str] = "AND"
    criteria_group: Optional[CriteriaBlock] = None
    metric: Optional[List[MetricCriteria]] = None
    grz: Optional[List[GRZCriteria]] = None
    table_name: Optional[str] = "parcel_grz_29042025"

class MaximizerRequest(BaseModel):
    geometry: Optional[List[Any]] = None
    criteria: Optional[List[CriteriaObject]] = None
    groups: Optional[List[Group]] = None
    between_groups_operator: Optional[str] = "AND"
    criteria_group: Optional[CriteriaBlock] = None
    metric: Optional[List[MetricCriteria]] = None
    grz: Optional[List[GRZCriteria]] = None
    table_name: Optional[str] = "parcel_grz_29042025"
    threshold: Optional[float] = 0.0

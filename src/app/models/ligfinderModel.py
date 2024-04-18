from typing import List, Optional,Any
from pydantic import BaseModel

class CriteriaItem(BaseModel):
    type: str
    column: List[Any]
    value: str

class CriteriaObject(BaseModel):
    status:str
    data:CriteriaItem

class MetricCriteria(BaseModel):
    column: str
    operation: str
    value: str

class TableRequest(BaseModel):
    geometry: Optional[List[Any]]
    criteria: Optional[List[CriteriaObject]]
    metric: Optional[List[MetricCriteria]]


"""
{
  "geometry": ["1", "2"],
  "criteria": [{ "type": "value", "column": ["T_1_47_A"], "value": "081" }],
  "metric": [
    {
      "column": "area_fme",
      "operation": ">",
      "value": "5000"
    }
  ]
}
"""

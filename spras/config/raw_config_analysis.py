from pydantic import BaseModel
from typing import Optional

class SummaryAnalysis(BaseModel):
    include: bool

class GraphspaceAnalysis(BaseModel):
    include: bool

class CytoscapeAnalysis(BaseModel):
    include: bool

class MlAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool
    components: int
    labels: bool
    # TODO: enumify
    linkage: str
    # TODO: enumify
    metric: str

class EvaluationAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool


class Analysis(BaseModel):
    summary: Optional[SummaryAnalysis]
    graphspace: Optional[GraphspaceAnalysis]
    cytoscape: Optional[CytoscapeAnalysis]
    ml: Optional[MlAnalysis]
    evaluation: Optional[EvaluationAnalysis]

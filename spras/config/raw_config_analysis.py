from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SummaryAnalysis(BaseModel):
    include: bool

class GraphspaceAnalysis(BaseModel):
    include: bool

class CytoscapeAnalysis(BaseModel):
    include: bool

class MlLinkage(str, Enum):
    ward = 'ward'
    complete = 'complete'
    average = 'average'
    single = 'single'

class MlMetric(str, Enum):
    euclidean = 'euclidean'
    manhattan = 'manhattan'
    cosine = 'cosine'

class MlAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool
    components: int
    labels: bool
    linkage: MlLinkage
    metric: MlMetric

class EvaluationAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool


class Analysis(BaseModel):
    summary: Optional[SummaryAnalysis]
    graphspace: Optional[GraphspaceAnalysis]
    cytoscape: Optional[CytoscapeAnalysis]
    ml: Optional[MlAnalysis]
    evaluation: Optional[EvaluationAnalysis]

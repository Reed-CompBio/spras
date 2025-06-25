from spras.config.util_enum import CaseInsensitiveEnum

from pydantic import BaseModel


class SummaryAnalysis(BaseModel):
    include: bool

class GraphspaceAnalysis(BaseModel):
    include: bool

class CytoscapeAnalysis(BaseModel):
    include: bool

class MlLinkage(CaseInsensitiveEnum):
    ward = 'ward'
    complete = 'complete'
    average = 'average'
    single = 'single'

class MlMetric(CaseInsensitiveEnum):
    euclidean = 'euclidean'
    manhattan = 'manhattan'
    cosine = 'cosine'

class MlAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool = False
    components: int = 2
    labels: bool = True
    linkage: MlLinkage = MlLinkage.ward
    metric: MlMetric = MlMetric.euclidean

class EvaluationAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool = False


class Analysis(BaseModel):
    summary: SummaryAnalysis = SummaryAnalysis(include=False)
    graphspace: GraphspaceAnalysis = GraphspaceAnalysis(include=False)
    cytoscape: CytoscapeAnalysis = CytoscapeAnalysis(include=False)
    ml: MlAnalysis = MlAnalysis(include=False)
    evaluation: EvaluationAnalysis = EvaluationAnalysis(include=False)

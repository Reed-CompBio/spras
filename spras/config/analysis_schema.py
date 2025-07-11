from pydantic import BaseModel, ConfigDict

from spras.config.util_enum import CaseInsensitiveEnum


class SummaryAnalysis(BaseModel):
    include: bool

    model_config = ConfigDict(extra='forbid')

class CytoscapeAnalysis(BaseModel):
    include: bool

    model_config = ConfigDict(extra='forbid')

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

    model_config = ConfigDict(extra='forbid')

class EvaluationAnalysis(BaseModel):
    include: bool
    aggregate_per_algorithm: bool = False

    model_config = ConfigDict(extra='forbid')

class Analysis(BaseModel):
    summary: SummaryAnalysis = SummaryAnalysis(include=False)
    cytoscape: CytoscapeAnalysis = CytoscapeAnalysis(include=False)
    ml: MlAnalysis = MlAnalysis(include=False)
    evaluation: EvaluationAnalysis = EvaluationAnalysis(include=False)

    model_config = ConfigDict(extra='forbid')

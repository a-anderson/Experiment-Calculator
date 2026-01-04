from typing import Literal, TypedDict

OutcomeType = Literal["binary", "normal"]
EffectType = Literal["Absolute Effect", "Relative Effect"]
CalculationType = Literal["Minimum Sample Size", "Minimum Detectable Effect"]
ComparisonType = Literal["Compare to first", "Compare all pairs"]
MTCType = Literal["Bonferroni", "None"]
SequentialType = Literal["O'Brien-Fleming", "None"]
AlternativeType = Literal["two-sided", "smaller", "larger"]

class ConfidenceIntervalResult(TypedDict):
    """Result from confidence interval calculations."""
    point_estimate: list[float]
    ci_lower: list[float]
    ci_upper: list[float]
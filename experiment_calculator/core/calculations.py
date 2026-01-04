import numpy as np
import pandas as pd
from typing import Union, List, Tuple
from experiment_calculator.core.types import (
    OutcomeType,
    EffectType,
    MTCType,
    SequentialType,
    AlternativeType,
    CalculationType,
    ComparisonType,
    ConfidenceIntervalResult,
)
from math import ceil
from itertools import combinations
from statsmodels.stats.proportion import proportion_effectsize
from statsmodels.stats.power import tt_ind_solve_power
from statsmodels.stats import proportion
from scipy import stats

#===============================================#
#--------------- Alpha Functions ---------------#
#===============================================#

def obrien_fleming_correction(information_fraction:float, alpha:float=0.05):
    """ 
    Calculate an approximation of the O'Brien-Fleming alpha spending function.
    Function taken from: https://github.com/zalando/expan/blob/master/expan/core/early_stopping.py

    Parameters
    ----------
    information_fraction : float
        Share of the information amount at the point of evaluation, 
        e.g., the share of the maximum sample size.
    alpha : float
        Type-I error rate.

    Returns
    -------
    float
        Redistributed alpha value at the time point with the given information fraction.
    """
    return (1 - stats.norm.cdf(stats.norm.ppf(1 - alpha / 2) / np.sqrt(information_fraction))) * 2

def adjusted_alpha(
    base_alpha:float,
    num_comparisons:int,
    multiple_comparisons:MTCType,
    sequential_testing:SequentialType=None,
    information_fraction:float=None,
):
    """
    Calculates and adjusted alpha for multiple comparisons correction and/or
    sequential testing. 

    Parameters
    ----------
    base_alpha : float
        The alpha (significance) defined for the experiment.
    num_comparisons : int
        The number of comparisons to be made for each experiment.
    multiple_comparisons : str in ["Bonferroni", "None"]
        The type of mulitple comparisons correction to be implemented.
    sequential_testing : str in ["O'Brien-Fleming", "None"]
        The type of sequential testing to be implemented
    information_fraction : float
        The proportion of the experiment that has been completed compared to 
        to total duration of the experiment (used for O'Brien-Fleming correction).

    Returns
    -------
    float
        adjusted alpha
    """
    assert num_comparisons >= 1

    if multiple_comparisons == "Bonferroni":
        alpha = base_alpha / num_comparisons
    else: 
        alpha = base_alpha

    if sequential_testing == "O'Brien-Fleming":
        alpha = obrien_fleming_correction(information_fraction=information_fraction, alpha=alpha)
        # set a minimum value for alpha in case the above calculation is 0
        alpha = max(alpha, 0.0000000000001)

    return alpha

#===============================================#
#----------------- Effect Size -----------------#
#===============================================#
def minimum_detectable_effect(
    outcome_type:OutcomeType,
    effect_type:EffectType,
    mde_input:float,
):
    """
    Calculates the correct type of minimum detectable effect for the specified
    outcome and effect type.

    Parameters
    ----------
    outcome_type : str
        String of either 'binary or 'normal' indicating the distribution
        of the outcome being measured. 
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.
    mde_input : float
        The minimum detectable effect specified for the experiment design.

    Returns
    -------
    float
        Returns the correct type of minimum detectable effect for the specified
        outcome and effect type.
    """
    if outcome_type == "normal" and effect_type == "Absolute Effect":
        return mde_input
    return mde_input / 100


def binary_effect_size(
    effect_type:EffectType,
    baseline_mean:float,
    mde:float,
):
    """
    Converts the given minimum detectable effect to a proportion effect size
    for the specified effect type.

    Parameters
    ----------
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.
    baseline_mean : float
        Conversion rate in the baseline group.
    mde : float
        Minimum detectable effect.

    Returns
    -------
    float
        The effect size calculation for the specified effect type.
    """
    assert effect_type in ("Absolute Effect", "Relative Effect")
    if effect_type == "Absolute Effect":
        proportion_1 = baseline_mean + mde
        return proportion_effectsize(prop1=proportion_1, prop2=baseline_mean, method="normal")

    proportion_1 = (1 + mde) * baseline_mean
    return proportion_effectsize(prop1=proportion_1, prop2=baseline_mean, method="normal")

def convert_effect_size_for_binary_outcome(
    effect_type:EffectType,
    effect_size:float,
    prop1:float,
):
    """
    Converts the effect size to an absolute or relative effect for a binomially 
    distributed sample. 

    Parameters
    ----------
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.
    effect_size : float
        The effect size to be converted for the appropriate effect type.
    prop1 : float
        The proportion (response rate) for the first group.

    Returns
    -------
    return type
        The effect size converted to an absolute or relative effect. 
    """
    delta = effect_size * np.sqrt(prop1 * (1 - prop1))
    prop2 = np.clip(prop1 + delta, 0, 1) 

    if effect_type == "Absolute Effect":
        return round((prop2 - prop1) * 100, 2)
    return round((prop2 / prop1 - 1) * 100, 2)

def convert_effect_size_for_normal_outcome(
    effect_type:EffectType,
    effect_size:float,
    baseline_mean:float,
    baseline_stdev:float,
):
    """
    Converts the effect size from Cohen's D to an absolute or relative effect. 
    
    Parameters
    ----------
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.
    effect_size : float
        The effect size to be converted for the appropriate effect type.
    baseline_mean : float
        Mean in the baseline group for the experiment - used as a proxy to estimate
        the mean in the experiment control group.
    baseline_stdev : float
        Standard deviation in the baseline group for the experiment - used as a proxy
        to estimate the standard deviation in the experiment control group.

    Returns
    -------
    return type
        The effect size converted from Cohen's D to an absolute or relative effect. 
    """
    absolute_effect = effect_size * baseline_stdev
    if effect_type == "Absolute Effect":
        return round(absolute_effect, 3)
    
    return round(100 * (absolute_effect / baseline_mean), 2)


def normal_effect_size(
    effect_type:EffectType,
    baseline_mean:float,
    mde:float,
    baseline_stdev:float,
):
    """
    Calculates the effect size for normally distributed samples.

    Parameters
    ----------
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.
    baseline_mean : float
        Mean in the baseline group for the experiment - used as a proxy to estimate
        the mean in the experiment control group.
    mde : float
        Minimum detectable effect.
    baseline_stdev : float
        Standard deviation in the baseline group for the experiment - used as a proxy
        to estimate the standard deviation in the experiment control group.

    Returns
    -------
    return type
        float
    """
    if baseline_stdev is None or baseline_stdev <= 0:
        raise ValueError("Baseline standard deviation must be positive.")
    
    if effect_type == "Relative Effect":
        new_mean = baseline_mean * (1 + mde)
    else:
        new_mean = baseline_mean + mde

    return (new_mean - baseline_mean) / baseline_stdev

def effect_size(
    outcome_type:OutcomeType,
    effect_type:EffectType,
    baseline_mean:float,
    mde:float,
    baseline_stdev:float=None,
):
    """
    Determines the correct type of effect size calculation for the given outcome and
    effect types, and returns those calculations.

    Parameters
    ----------
    outcome_type : str
        String of either 'binary or 'normal' indicating the distribution
        of the outcome being measured. 
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.
    baseline_mean : float
        Mean in the baseline group for the experiment - used as a proxy to estimate
        the mean in the experiment control group.
    mde : float
        Minimum detectable effect.
    baseline_stdev : float
        Standard deviation in the baseline group for the experiment - used as a proxy
        to estimate the standard deviation in the experiment control group.

    Returns
    -------
    return float
        The effect size to be used in all experiment design calculations.
    """
    assert outcome_type in ("binary", "normal")
    if outcome_type == "binary":
        return binary_effect_size(effect_type, baseline_mean, mde)
    return normal_effect_size(effect_type, baseline_mean, mde, baseline_stdev)

#===============================================#
#-------------- Sample/MDE Calcs ---------------#
#===============================================#
def n1_sample_size(
    effect_size:float,
    alpha:float,
    power:float,
    ratio:float,
    alternative:AlternativeType="two-sided"
):
    """
    Calculates the group 1 sample size required to reach the desired power for an 
    experiment with the specified minimum detectable effect.

    Parameters
    ----------
    effect_size : float
        The desired effect size for the experiment.
    alpha : float
        Alpha (significance) value used for the confidence interval calculation.
    power : float
        Desired power for the experiment.
    ratio : float
        The required group1:group2 sample size ratio.
    alternative : str in ['two-sided', 'smaller', 'larger']
        The alternative hypothesis specifying either a two-sided or the type of
        one-sided test.

    Returns
    -------
    float
        The group 1 sample size required to reach the desired power for an 
        experiment with the specified minimum detectable effect. 
    """

    return ceil(
        tt_ind_solve_power(
            effect_size = effect_size,
            nobs1 = None,
            alpha = alpha,
            power = power,
            ratio = ratio,
            alternative = alternative
        )
    )

def sample_size_list(
    effect_size:float,
    power_range:Union[list, np.ndarray],
    alpha:float,
    limiting_ratio:float,
    flight_ratios:Union[list, np.ndarray, pd.Series],
    alternative:AlternativeType="two-sided"
):
    """
    Calculates a list of sample sizes required for an experiment for each power
    in the provided power range.

    Parameters
    ----------
    effect_size : float
        The desired effect size for the experiment.
    power_range : iterable
        The range of desired power value for the plot y-axis.
    alpha : float
        alpha (significance) value used for the confidence interval calculation.
    limiting_ratio : float
        The ratio to be used for the sample size or minimum detectable effect calculation.
    flight_ratios : iterable
        Iterable of ratios of each group to the first group in the experiment.
    alternative : str in ['two-sided', 'smaller', 'larger']
        The alternative hypothesis specifying either a two-sided or the type of
        one-sided test.

    Returns
    -------
    return type
        explanation
    """
    nobs1 = np.array([n1_sample_size(effect_size=effect_size, alpha=alpha, power=p, ratio=limiting_ratio, alternative=alternative) for p in power_range])
    total_obs = nobs1 * sum(flight_ratios)
    return list(np.ceil(total_obs))

def minimum_detectable_effect_size(
    nobs1:int,
    power:float,
    alpha:float,
    ratio:float,
    alternative:AlternativeType="two-sided"
):
    """
    Calculates the minimum detectable effect for an experiment where the sample size
    and alpha are already pre-set.

    Parameters
    ----------
    nobs1 : int
        The sample size for group 1.
    power : float
        The desired power for the experiment.
    alpha : float
        alpha (significance) value used for the confidence interval calculation.
    ratio : float
        The ratio to be used for the sample size or minimum detectable effect calculation.
    alternative : str in ['two-sided', 'smaller', 'larger']
        The alternative hypothesis specifying either a two-sided or the type of
        one-sided test.

    Returns
    -------
    return type
        explanation
    """
    return tt_ind_solve_power(
            nobs1 = nobs1,
            alpha = alpha,
            power = power,
            ratio = ratio,
            alternative = alternative
    )

def effect_size_list(
    nobs1:float,
    power_range:Union[list, np.ndarray],
    alpha:float,
    limiting_ratio:float,
    outcome_type:OutcomeType,
    effect_type:EffectType,
    baseline_mean:float,
    baseline_stdev:float,
    alternative:AlternativeType="two-sided"
):
    """
    Parameters
    ----------
    nobs1 : int
        The sample size for group 1.
    power_range : iterable
        The range of power percents for the plot y-axis.
    alpha : float
        alpha (significance) value used for the confidence interval calculation.
    limiting_ratio : float
        The ratio to be used for the sample size or minimum detectable effect calculation.
    outcome_type : str
        String of either 'binary or 'normal' indicating the distribution
        of the outcome being measured. 
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.
    baseline_mean : float
        Mean in the baseline cohort.
    baseline_stdev : float
        Standard deviation in the baseline cohort.
    alternative : str in ['two-sided', 'smaller', 'larger']
        The alternative hypothesis specifying either a two-sided or the type of
        one-sided test.

    Returns
    -------
    List
        List of effect size values to be used in the x-axis of the power-curve.
    """
    assert outcome_type in ("binary", "normal")
    effect_sizes = np.array([minimum_detectable_effect_size(nobs1=nobs1, alpha=alpha, power=p, ratio=limiting_ratio, alternative=alternative) for p in list(power_range)])
    if outcome_type == "binary":
        vectorised_conversion = np.vectorize(convert_effect_size_for_binary_outcome)
        return list(vectorised_conversion(effect_type, effect_sizes, baseline_mean))

    vectorised_conversion = np.vectorize(convert_effect_size_for_normal_outcome)
    return list(vectorised_conversion(effect_type, effect_sizes, baseline_mean, baseline_stdev))

def plot_x_data(
    calculation_type:CalculationType,
    power_range:Union[list, np.ndarray],
    nobs1:int,
    effect_size:float,
    alpha:float,
    limiting_ratio:float,
    flight_ratios:Union[list, np.ndarray, pd.Series],
    outcome_type:OutcomeType,
    effect_type:EffectType,
    baseline_mean:float,
    baseline_stdev:float,
    alternative:AlternativeType="two-sided",
) -> List[float]:
    """
    Calculate the values to be used for the the x-data in the power curve plot.

    Parameters
    ----------
    calculation_type : str in ["Minimum Sample Size", "Minimum Detectable Effect"]
        The calculation type to be displayed in the power plot.
    power_range : iterable
        The range of power percents for the plot y-axis.
    nobs1 : int
        The sample size for group 1.
    effect_size : float
        The effect size (Cohen's D) to be used for sample size calculations.
    alpha : float
        alpha (significance) value used for the confidence interval calculation.
    limiting_ratio : float
        The ratio to be used for the sample size or minimum detectable effect calculation.
    flight_ratios : iterable
        explanation
    outcome_type : str
        String of either 'binary or 'normal' indicating the distribution
        of the outcome being measured. 
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.
    baseline_mean : float
        Mean in the baseline cohort.
    baseline_stdev : float
        Standard deviation in the baseline cohort.
    alternative : str in ['two-sided', 'smaller', 'larger']
        The alternative hypothesis specifying either a two-sided or the type of
        one-sided test.

    Returns
    -------
    List
        List of values to be used in the x-axis of the power-curve.
    """
    assert calculation_type in ("Minimum Sample Size", "Minimum Detectable Effect")
    
    if calculation_type == "Minimum Sample Size":
        return sample_size_list(
            effect_size,
            power_range,
            alpha,
            limiting_ratio,
            flight_ratios,
            alternative,
        )

    return effect_size_list(
        nobs1,
        power_range,
        alpha,
        limiting_ratio,
        outcome_type,
        effect_type,
        baseline_mean,
        baseline_stdev,
        alternative,
    )

#===============================================#
#----------------- Other Calcs -----------------#
#===============================================#

def design_ratio(ratios:Union[list, np.ndarray, pd.Series]):
    """
    Identify the sample size comparison ratio that will be the limiting ratio
    for the experiment design.

    Parameters
    ----------
    ratios : iterable
        Iterable of ratios for the expected traffic proportion of group 1 to
        each other group in the experiment.

    Returns
    -------
    float
        The ratio to be used for the sample size or minimum detectable effect calculation.
    """
    if (biggest_ratio:=max(ratios)) >= 1 / (smallest_ratio:=min(ratios)):
            return biggest_ratio
    return smallest_ratio

def get_comparison_pairs(
    comparison_type:ComparisonType, 
    num_flights:int,
):
    """
    Generate a lits of row pairs to compare for group comparison results.

    Parameters
    ----------
    comparison_type : str
        String of either 'Compare to first' or 'Compare all pairs' indicating 
        how the comparison pairs should be calculated.
    num_flights : int
        Number of flights (groups) to be compared in the experiment.

    Returns
    -------
    List[Tuple[int, int]]
        List of tuples containg the comparison pairs as they would appear as
        rows in a dataframe.
    """
    if comparison_type == "Compare to first":
        return [(0, i) for i in range(1, num_flights)]
    return list(combinations(range(num_flights), 2))


#===============================================#
#------------- Significance Calcs --------------#
#===============================================#

def group_responses(
    outcome_type:OutcomeType, 
    experiment_data_summary:pd.DataFrame, 
    alpha:float=0.05
):
    """
    Calculate the point estimates and confidence intervals for each group 
    in the experiment.

    Parameters
    ----------
    outcome_type : str
        String of either 'binary or 'normal' indicating the distribution
        of the outcome being measured. 
    experiment_data_summary : pd.DataFrame
        Dataframe containing summary statistics for each group in the experiment.
    alpha : float
        alpha (significance) value used for the confidence interval calculation.

    Returns
    -------
    pd.DataFrame
        Dataframe with point estimate and confidence interval calculations for each
        group in the experiment.
    """

    if outcome_type == "binary":
        confint = proportion.proportion_confint(
            count = experiment_data_summary["Num Successes"],
            nobs = experiment_data_summary["Sample Size"],
            alpha = alpha,
            method = "normal"
        )
        confint_df = pd.DataFrame(confint).T
        confint_df.columns = ["ci_lower", "ci_upper"]
        confint_df["point_estimate"] = experiment_data_summary["Num Successes"] / experiment_data_summary["Sample Size"]
    
    else:
        standard_error = experiment_data_summary["StdDev"] / np.sqrt(experiment_data_summary["Sample Size"])
        confidence = 1 - alpha
        confint = stats.norm.interval(confidence, loc=experiment_data_summary["Mean"], scale=standard_error)
        confint_df = pd.DataFrame(confint).T
        confint_df.columns = ["ci_lower", "ci_upper"]
        confint_df["point_estimate"] = experiment_data_summary["Mean"]

    confint_df["group_name"] = experiment_data_summary["Group Name"]
    return confint_df[["group_name", "point_estimate", "ci_lower", "ci_upper"]]

def binomial_standard_error(
    proportion:float, 
    sample_size:int
):
    """
    Calculate the standard error for binomially distributed samples.

    Parameters
    ----------
    proportion : float
        Response rate (proportion) for the group outcome.
    sample_size : int
        Sample of the group/

    Returns
    -------
    float
        Standard error for the given proportion and sample size.
    """
    return np.sqrt(proportion * (1 - proportion) / sample_size)

def binomial_confidence_interval(
    prop1:float, 
    n1:int, 
    prop2:float, 
    n2:int, 
    confidence:float, 
    effect_type:EffectType
) -> ConfidenceIntervalResult:
    """
    Calculate the point estimate and confidence interval for the difference
    between two groups that have binomially distributed outcomes.

    Parameters
    ----------
    prop1 : float
        Response rate (proportion) for group 1.
    n1 : int
        Sample size for group 1.
    prop2 : float
        Response rate (proportion) for group 2.
    n2 : int
        Sample size for group 1.
    confidence : float
        Confidence (1 - alpha) to be used in confidence interval calulaitons.
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.

    Returns
    -------
    Dict
        Dictionary containing the point estimate and confidence interval calculations 
        for binomial confidence intervals.
    """

    # Difference in proportions
    prop_diff = prop2 - prop1
    
    std_err_1 = binomial_standard_error(proportion=prop1, sample_size=n1)
    std_err_2 = binomial_standard_error(proportion=prop2, sample_size=n2)

    if effect_type == "Relative Effect":
        prop_diff = prop_diff / prop1
        # Use the delta method to estimate the standard error for the relative effect
        se_diff = np.sqrt(1/(prop1 ** 2) * (std_err_2 ** 2) + (prop2 ** 2) / (prop1 ** 4) * (std_err_1 ** 2))
    else:
        # Standard error of the difference
        se_diff = np.sqrt(std_err_1**2 + std_err_2**2)
    
    # Critical z-value for the desired confidence level
    z_crit = stats.norm.ppf((1 + confidence) / 2)
    
    # Confidence interval
    margin_of_error = z_crit * se_diff

    ci_lower = prop_diff - margin_of_error
    ci_upper = prop_diff + margin_of_error
    
    return {
        "point_estimate": [prop_diff], 
        "ci_lower": [ci_lower], 
        "ci_upper": [ci_upper],
    }

def normal_standard_error(
    stdev:float, 
    sample_size:int,

):
    """
    Calculate the standard error for normally distributed samples.

    Parameters
    ----------
    stdev : float
        Standard deviation
    sample_size : int
        Sample size

    Returns
    -------
    float
        Standard error for the given standard deviation and sample size.
    """
    return stdev / np.sqrt(sample_size)

def dof_welch_satterthwaithe(
    stdev1:float, 
    n1:int, 
    stdev2:float, 
    n2:int
):
    """
    Calculate degrees of freedom for a t-test using the Welch–Satterthwaite equation
    to calculate degrees of freedom for two-sample t-tests where the variance may
    be unequal in both groups.

    Parameters
    ----------
    stdev1 : float
        Standard deviation for group 1.
    n1 : int
        Sample size for group 1.
    stdev2 : float
        Standard deviation for group 2.
    n2 : int
        Sample size for group 2.

    Returns
    -------
    int
        Degrees of freedom for t-test calculations.
    """
    numerator = ((stdev1**2 / n1) + (stdev2**2 / n2))**2
    denominator = (((stdev1**2 / n1)**2 / (n1 - 1)) + ((stdev2**2 / n2)**2 / (n2 - 1)))
    return numerator / denominator

def normal_confidence_interval(
    mean1:float, 
    stdev1:float, 
    n1:int, 
    mean2:float, 
    stdev2:float, 
    n2:int, 
    confidence:float, 
    effect_type:EffectType
):
    """
    Calculate the point estimate and confidence interval for the difference
    between two groups that have normally distributed outcomes.

    Parameters
    ----------
    mean1 : float
        Mean response for experiment group 1.
    stdev1 : float
        Standard deviation for experiment group 1.
    n1 : int
        Sample size for experiment group 1.
    mean2 : float
        Mean response for experiment group 2.
    stdev2 : float
        Standard deviation for experiment group 2.
    n2 : int
        Sample size for experiment group 2.
    confidence : float
        Confidence level (1 - alpha) to be used for confidence interval calculaitons.
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.

    Returns
    -------
    Dict
        Dictionary containing the point estimate and confidence interval calculations 
        for between group differences.
    """

    # Difference of means
    mean_diff = mean2 - mean1

    std_err_1 = stdev1 / np.sqrt(n1)
    std_err_2 = stdev2 / np.sqrt(n2)

    if effect_type == "Relative Effect":
        mean_diff = mean_diff / mean1 
        # Use the delta method to estimate the standard error for the relative effect
        std_err_diff = np.sqrt(1/(mean1 ** 2) * (std_err_2 ** 2) + (mean2 ** 2) / (mean1 ** 4) * (std_err_1 ** 2))
    else:
        std_err_diff = np.sqrt(std_err_1**2 + std_err_2**2)
    
    # Degrees of freedom using the Welch–Satterthwaite equation
    # which calcuates the dof where samples may have unequal variances.
    dof = dof_welch_satterthwaithe(stdev1, n1, stdev2, n2)

    # t critical value for the confidence level
    t_crit = stats.t.ppf((1 + confidence) / 2, dof)
    
    # confidence interval
    margin_of_error = t_crit * std_err_diff
    ci_lower = mean_diff - margin_of_error
    ci_upper = mean_diff + margin_of_error
    
    return {
        "point_estimate": [mean_diff], 
        "ci_lower": [ci_lower], 
        "ci_upper": [ci_upper],
    }

def group_differences(
    experiment_data_summary:pd.DataFrame,
    alpha:float,
    comparison_pairs:List[Tuple[int, int]],
    outcome_type:OutcomeType,
    effect_type:EffectType,
) -> pd.DataFrame:
    """
    Parameters
    ----------
    experiment_data_summary : pd.DataFrame
        Dataframe containing summary statistics for each group in the experiment.
    alpha : float
        alpha (significance) value used for the confidence interval calculation.
    comparison_pairs : List[Tuple[int, int]]
        List of row number comparison pairs, to identify which groups from the 
        experiment_data_summary are to be used for group difference calculations.
    outcome_type : str
        String of either 'binary or 'normal' indicating the distribution
        of the outcome being measured. 
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.

    Returns
    -------
    pd.DataFrame
        Dataframe containing calculations for group difference comparisons. 
    """

    group_differences = pd.DataFrame()
    for group1, group2 in comparison_pairs:
        group1 = experiment_data_summary.iloc[group1]
        group1_name = group1['Group Name']

        group2 = experiment_data_summary.iloc[group2]
        group2_name = group2['Group Name']

        comparison_name = f"{group2_name} - {group1_name}"

        if outcome_type == "binary":
            diff_summary = binomial_confidence_interval(
                prop1=group1["Num Successes"] / group1["Sample Size"],
                n1=group1["Sample Size"],
                prop2=group2["Num Successes"] / group2["Sample Size"],
                n2=group2["Sample Size"],
                confidence=1.0-alpha,
                effect_type=effect_type,
            )

        else:
            diff_summary = normal_confidence_interval(
                mean1=group1["Mean"], 
                stdev1=group1["StdDev"], 
                n1=group1["Sample Size"], 
                mean2=group2["Mean"], 
                stdev2=group2["StdDev"], 
                n2=group2["Sample Size"], 
                confidence=1.0-alpha, 
                effect_type=effect_type,
            )
        
        group_difference = pd.DataFrame({
            "group_name": comparison_name, 
            "group1_name": group1_name,
            "group2_name": group2_name,
            **diff_summary
        })

        if group_differences.empty:
            group_differences = group_difference
        else:
            group_differences = pd.concat([group_differences, group_difference])
    return group_differences

def format_outcomes_for_plots(
    experiment_results:pd.DataFrame, 
    outcome_type:OutcomeType, 
    effect_type:EffectType
):
    """
    Format outcomes for significance plots.

    Parameters
    ----------
    experiment_results : pd.DataFrame
        Dataframe containing summary results from the experiment.
    outcome_type : str
        String of either 'binary or 'normal' indicating the distribution
        of the outcome being measured. 
    effect_type : str
        String of either 'Absolute Effect' or 'Relative Effect' indicating
        the type of minimum detectable effect being measured  in the experiment.

    Returns
    -------
    pd.DataFrame
        Dataframe containing the provided experiment results where the point estimate and 
        confidence bounds have been formatted for the result plots.
    """

    if outcome_type == "binary" or effect_type == "Relative Effect":
        decimal_places = 2
        multiplier = 100
    else:
        decimal_places = 4
        multiplier = 1

    experiment_results["point_estimate"] = round(experiment_results["point_estimate"] * multiplier, decimal_places)
    experiment_results["ci_lower"] = round(experiment_results["ci_lower"] * multiplier, decimal_places)
    experiment_results["ci_upper"] = round(experiment_results["ci_upper"] * multiplier, decimal_places)

    return experiment_results

#===============================================#
#------------------ SRM Calcs ------------------#
#===============================================#

def srm_pvalue(sample_size_data:pd.DataFrame):

    """
    Parameters
    ----------
    sample_size_data : pd.DataFrame
        Dataframe containing the sample size and expected proportions for 
        each group in the experiment.

    Returns
    -------
    float
        The p-value (float in the range [0.0, 1.0]) indicating whether the 
        provided sample sizes match their expected proportions.
    """

    total_samples = sample_size_data["Sample Size"].sum()
    # actual_proportions = sample_size_data["Sample Size"] / total_samples # TODO: double check removing this

    p_value = proportion.proportions_chisquare(
        count = sample_size_data["Sample Size"], 
        nobs = total_samples, 
        value = sample_size_data["Expected Proportion"] 
    )[1]

    return p_value
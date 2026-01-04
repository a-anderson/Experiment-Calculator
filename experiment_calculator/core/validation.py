import pandas as pd
from experiment_calculator.core.types import OutcomeType

def valid_traffic_allocation(traffic_allocation:pd.DataFrame):
    
    min_allocation = traffic_allocation["Traffic Allocation (%)"].min()
    max_allocation = traffic_allocation["Traffic Allocation (%)"].max()
    total_traffic = traffic_allocation["Traffic Allocation (%)"].sum()

    return min_allocation > 0 and max_allocation < 100 and total_traffic <= 100

def valid_summary_data(summary_data:pd.DataFrame, outcome_type:OutcomeType):

    valid_samples = summary_data["Sample Size"] > 0
    all_samples_valid = valid_samples.all()

    if outcome_type == "binary":
        valid_successes = summary_data["Num Successes"] >= 0
        all_successes_valid = valid_successes.all()

        return all_samples_valid and all_successes_valid

    valid_means = summary_data["Mean"] >= 0
    all_means_valid = valid_means.all()

    valid_stdevs = summary_data["StdDev"] >= 0
    all_stdevs_valid = valid_stdevs.all()

    return all_samples_valid and all_means_valid and all_stdevs_valid

def valid_srm_data(summary_data:pd.DataFrame):
    
    valid_samples = summary_data["Sample Size"] > 0
    all_samples_valid = valid_samples.all()

    min_expected_proportion = summary_data["Expected Proportion (%)"].min()
    max_expected_proportion = summary_data["Expected Proportion (%)"].max()

    return all_samples_valid and min_expected_proportion > 0 and max_expected_proportion < 100

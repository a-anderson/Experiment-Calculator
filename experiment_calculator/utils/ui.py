import streamlit as st
import pandas as pd
from typing import Union, Literal

def calculation_type_selection():
    return st.radio(
        label="##### What do you want to calculate?",
        options=["Minimum Sample Size", "Minimum Detectable Effect"],
        index=0
    )

    
def baseline_success_selection():
    return st.number_input(
        label="##### Success rate in the baseline group (%)",
        value=20.0,
        min_value=0.1,
        max_value=100.0,
        step=1.0,
    )

def baseline_mean_selection():
    return st.number_input(
        label="##### Mean response in the baseline group",
        value=5.0,
        min_value=0.0,
        step=1.0,
    )

def baseline_std_selection():
    return st.number_input(
        label="##### Standard deviation in the baseline group",
        value=8.0,
        min_value=0.0,
        step=1.0,
    )

def sample_split_selection():
    default_traffic_data = pd.DataFrame(
            [
                {"Group Name": "Group 1", "Traffic Allocation (%)": 50},
                {"Group Name": "Group 2", "Traffic Allocation (%)": 50}
            ]
        )
    return st.data_editor(default_traffic_data, num_rows="dynamic", hide_index=True)

def effect_type_selection():
    return st.radio(
        label="##### Effect type to be used",
        options=["Absolute Effect", "Relative Effect"],
        index=0
    )

def mde_level_selection(
    effect_type:Literal["Absolute Effect", "Relative Effect"],
    outcome_type:Literal["binary", "normal"],
): 

    if effect_type == "Absolute Effect" and outcome_type == "normal":
        label = "##### Minimum Detectible Effect"
        default_value = 1.0
    else:
        label = "##### Minimum Detectible Effect (%)"
        default_value = 5.0

    return st.number_input(
        label=label,
        value=default_value,
        min_value=0.1,
        max_value=100.0,
        step=1.0,
    )

def sample_size_input():
    return st.number_input(
        label="##### Total Available Sample Size",
        value=10_000,
        min_value=100,
        step=1,
    )

def significance_level_selection():
    return st.number_input(
    label="##### Level of Significance (%)",
    value=5.0,
    min_value=0.1,
    max_value=100.0,
    step=1.0,
)

def power_level_selection():
    return st.number_input(
    label="##### Level of Power (%)",
    value=80,
    min_value=1,
    max_value=100,
    step=1,
)

def comparison_type_selection():
    return st.radio(
        label="##### Comparisons to estimate",
        options=["Compare to first", "Compare all pairs"],
        index=0
    )

def mtc_type_selection(): 

    options = ["Bonferroni", "None"]

    return st.radio(
        label="##### Multiple Comparisons Correction",
        options=options,
        index=0
    )

def format_sample_size_results(
    outcome_type:Literal["binary", "normal"],
    effect_type:Literal["Absolute Effect", "Relative Effect"],
    mde_level:int,
    baseline_mean:float,
    power_level:int,
    significance_level:int,
    total_samples_required:int,
    baseline_success:float,
):

    mde_type = "%"
    if outcome_type == "normal":

        formatted_mean = baseline_mean
        if effect_type == "Absolute Effect":
            mde_type = " unit"
            formatted_effect = ""
        else:
            formatted_effect = "relative "

    elif outcome_type == "binary":

        formatted_mean = baseline_success
        if effect_type == "Absolute Effect":
            formatted_effect = "absolute "
        else:
            formatted_effect = "relative "
    
    return f"Measuring a {mde_level}{mde_type} {formatted_effect}increase in a response rate of {formatted_mean}%, with {power_level}% power and a {significance_level}% significance level requires a **total sample size of {total_samples_required:,}** distributed across the treatments (in the given traffic proportions)."

def experiment_data_summary(outcome_type:Literal["binary", "normal"]):
    if outcome_type == "normal":
            default_results = pd.DataFrame(
                [
                    {"Group Name": "Group 1", "Sample Size": 1_000, "Mean": 4.0, "StdDev": 2.0},
                    {"Group Name": "Group 2", "Sample Size": 1_000, "Mean": 5.0, "StdDev": 2.0},
                ]
            )
    else:
        default_results = pd.DataFrame(
            [
                {"Group Name": "Group 1", "Sample Size": 1_000, "Num Successes": 40},
                {"Group Name": "Group 2", "Sample Size": 1_000, "Num Successes": 50},
            ]
        )
    return st.data_editor(default_results, num_rows="dynamic", hide_index=True)

def sequential_testing_selection():
    return st.radio(
        label="##### Sequential Testing Correction",
        options=["O'Brien-Fleming", "None"],
        index=1
    )

def experiment_duration_summary():
    default_data = pd.DataFrame(
        [
            {"Days Passed": 1, "Total Experiment Duration": 30},
        ]
    )
    return st.data_editor(default_data, hide_index=True)

def input_table_instructions():
    return (
        "To add additional groups click on the `+` button that appears in the bottom row."
        + " To remove a row click the checkbox that appears on the left, navigate to the "
        + "top right of the table, and click the trashcan icon."
        )

def outcome_distribution_summary(outcome_type:Literal["binary", "normal"],):
    if outcome_type == "binary":
        return (
            "Use this calculator when measuring outcomes that are binomially distributed."
            + " This includes measures where there can only be one of two outcomes for the" 
            + " unit of analysis. For example: true/false, yes/no, 1/0, etc."
        )
    else:
        return (
            "Use this calculator when measuring outcomes that follow a normal distribution" 
            + " or can be approximated by it (using the central limit theorem)."
            + " This applies to continuous measures or averages, such as revenue per user,"
            + " time on site, or button clicks per user."
        )
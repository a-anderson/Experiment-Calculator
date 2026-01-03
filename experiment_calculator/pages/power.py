from math import ceil
import streamlit as st
import numpy as np
import pandas as pd
from experiment_calculator.core import calculations, validation
from experiment_calculator.ui import plots
from experiment_calculator.ui import components

def show_power(outcome_type):

    st.header(f"Power Calculator - {outcome_type.title()} Outcome")
    st.markdown(
        f"""
        <div style="max-width: 800px;">
            {components.outcome_distribution_summary(outcome_type)}
        </div>
        <br>
        """,
        unsafe_allow_html=True,
    )

    # create two columns for the app layout
    column_1, spacer, column_2 = st.columns([1, 0.05, 2])

    with column_1:

        calculation_type = components.calculation_type_selection()

        if outcome_type == 'binary':
            baseline_success = components.baseline_success_selection()
            baseline_mean = baseline_success / 100
            baseline_stdev = None
        else: 
            baseline_success = None
            baseline_mean = components.baseline_mean_selection()
            baseline_stdev = components.baseline_std_selection()

        st.markdown("**Sample split across groups**")
        st.write(components.input_table_instructions())

        sample_split = components.sample_split_selection()
        traffic_allocation_is_valid = validation.valid_traffic_allocation(sample_split)

        effect_type = components.effect_type_selection()

        if calculation_type == "Minimum Sample Size":
            mde_level = components.mde_level_selection(effect_type, outcome_type)
            mde = calculations.minimum_detectable_effect(outcome_type, effect_type, mde_level)
            nobs1 = None

        else:
            available_sample_size = components.sample_size_input()
            mde_level = None
            mde = None

        significance_level = components.significance_level_selection()

        power_level = components.power_level_selection()
        power = power_level / 100

        comparison_type = components.comparison_type_selection()
        comparison_pairs = calculations.get_comparison_pairs(comparison_type, num_flights=sample_split.dropna().shape[0])
        num_comparisons = len(comparison_pairs)

        mtc_type = components.mtc_type_selection()

        alpha = calculations.adjusted_alpha(
            base_alpha=significance_level / 100,
            num_comparisons=num_comparisons,
            multiple_comparisons=mtc_type,
        )

    with column_2:

        if traffic_allocation_is_valid:
            
            # find the ratio that all other calculations will be dependent on
            if comparison_type == "Compare to first":
                calculation_ratios = sample_split["Traffic Allocation (%)"].dropna() / sample_split["Traffic Allocation (%)"][0]
                ratio = calculations.design_ratio(calculation_ratios)
            else:
                total_sample_allocation = sample_split["Traffic Allocation (%)"].sum()
                largest_traffic_allocation = sample_split["Traffic Allocation (%)"].max()
                smallest_traffic_allocation = sample_split["Traffic Allocation (%)"].min()

                # the limiting ratio for experiment calculations will be between the largest and smallest traffic allocations
                ratio = smallest_traffic_allocation / (largest_traffic_allocation + smallest_traffic_allocation)

                calculation_ratios = sample_split["Traffic Allocation (%)"].dropna() / largest_traffic_allocation

            if calculation_type == "Minimum Sample Size":
                mde_estimate = None
                
                effect_size = calculations.effect_size(
                    outcome_type=outcome_type, 
                    effect_type=effect_type, 
                    baseline_mean=baseline_mean, 
                    mde=mde, 
                    baseline_stdev=baseline_stdev,
                )

                group1_samples_required = calculations.n1_sample_size(
                    effect_size = effect_size,
                    alpha = alpha,
                    power = power,
                    ratio = ratio,
                )

                required_sample_df = sample_split.copy()
                required_sample_df["Minimum Samples Required"] = np.ceil(calculation_ratios * group1_samples_required)
                total_samples_required = int(required_sample_df["Minimum Samples Required"].sum())

                st.write("##### Calculation Results")

                results_summary = components.format_sample_size_results(
                    outcome_type=outcome_type,
                    effect_type=effect_type,
                    mde_level=mde_level,
                    baseline_mean=baseline_mean,
                    baseline_success=baseline_success,
                    power_level=power_level,
                    significance_level=significance_level,
                    total_samples_required=total_samples_required,
                )

                st.write(results_summary)

                st.dataframe(required_sample_df.dropna(), hide_index=True, width="content")
                st.write(f"##### Total Samples Required:  {total_samples_required:,}")
            else:
                effect_size = None
                total_samples_required = None

                nobs1 = available_sample_size / sum(calculation_ratios)

                mde_estimate = calculations.minimum_detectable_effect_size(
                    nobs1=nobs1,
                    power=power,
                    alpha=alpha,
                    ratio=ratio,
                )

                mde_type = "%"
                if outcome_type == "normal":

                    if effect_type == "Absolute Effect":
                        mde_type = " unit"

                    mde_estimate = calculations.convert_effect_size_for_normal_outcome(
                        effect_type=effect_type,
                        effect_size=mde_estimate,
                        baseline_mean=baseline_mean,
                        baseline_stdev=baseline_stdev,
                    )

                elif outcome_type == "binary":
                    mde_estimate = calculations.convert_effect_size_for_binary_outcome(
                        effect_type=effect_type,
                        effect_size=mde_estimate,
                        prop1=baseline_mean,
                    )

                st.write("##### Calculation Results")

                formatted_effect_type = "relative "
                if effect_type == "Absolute Effect":
                    formatted_effect_type = "absolute "
                st.write(
                    f"""
                    With a total sample size of {available_sample_size:,}, distributed across the flights in the given proportions, you will be able to estimate a **{mde_estimate}{mde_type} {formatted_effect_type}increase in the response rate** with {power_level}% power and {significance_level}% significance.
                    """
                )

                st.write(f"##### Minimum Detectable Effect:  {mde_estimate:,}{mde_type}")


            ## ---- Plot Calculation ---- ##

            # Power range from 1% to 99%
            power_range = np.linspace(0.1, 0.99, 90)
            power_percents = list(power_range * 100)

            # Calculate x-axis for the power curve plot
            plot_x_data = calculations.plot_x_data(
                calculation_type=calculation_type,
                power_range=power_range,
                nobs1=nobs1,
                effect_size=effect_size,
                alpha=alpha,
                limiting_ratio=ratio,
                flight_ratios=calculation_ratios,
                baseline_mean=baseline_mean,
                baseline_stdev=baseline_stdev,
                outcome_type=outcome_type,
                effect_type=effect_type,
                alternative='two-sided',
            )

            fig = plots.power_curve(
                calculation_type=calculation_type,
                x_data=plot_x_data,
                power_percents=power_percents,
                target_power_level=power_level,
                plot_type=effect_type,
                outcome_type=outcome_type,
            )

            # Display the plot in Streamlit
            st.plotly_chart(fig, width="stretch")
        
        # Handle cases where the traffic allocation is invalid
        else:
            st.write("#### :red[Sample Split Error:]")
            st.write(":red[Traffic allocation for each individual group must be between 1% and 100%.]")
            st.write(":red[Total traffic allocation must be 100% or less.]")
            st.write(":red[Please change the input to meet these specifications.]")

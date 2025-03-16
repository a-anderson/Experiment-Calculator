import pandas as pd
import streamlit as st
from typing import Union, Literal
from utils import ui, validation, calculation, plot

def show_significance(outcome_type:Literal["binary", "normal"]):
    st.header(f"Significance Calculator - {outcome_type.title()} Outcome")
    st.markdown(
        f"""
        <div style="max-width: 800px;">
            {ui.outcome_distribution_summary(outcome_type)}
        </div>
        <br>
        """,
        unsafe_allow_html=True,
    )

    # create two columns for the app layout
    column_1, spacer, column_2 = st.columns([1, 0.05, 2])

    with column_1:

        st.write("##### Summary data for each experiment group")
        st.write(ui.input_table_instructions())

        experiment_summary = ui.experiment_data_summary(outcome_type)
        summary_data_is_valid = validation.valid_summary_data(experiment_summary.dropna(), outcome_type)

        effect_type = ui.effect_type_selection()

        significance_level = ui.significance_level_selection()

        comparison_type = ui.comparison_type_selection()
        comparison_pairs = calculation.get_comparison_pairs(comparison_type=comparison_type, num_flights=experiment_summary.dropna().shape[0])
        num_comparisons = len(comparison_pairs)
        
        mtc_type = ui.mtc_type_selection()

        sequential_testing = ui.sequential_testing_selection()

        if sequential_testing != "None":
            st.write("##### Experiment Progress")
            st.write("Enter the number of days the experiment has been running and the total number of days the experiment is planned to run.")
            experiment_progress = ui.experiment_duration_summary()
            information_fraction = experiment_progress["Days Passed"][0] / experiment_progress["Total Experiment Duration"][0]
        else:
            information_fraction = None
        
        alpha = calculation.adjusted_alpha(
            base_alpha=significance_level / 100,
            num_comparisons=num_comparisons,
            multiple_comparisons=mtc_type,
            sequential_testing=sequential_testing,
            information_fraction=information_fraction,
        )

    with column_2:

        if summary_data_is_valid:
            st.write("##### Calculation Results")

            ## ---- Group Difference Calculations ---- ##
            difference_results = calculation.group_differences(
                experiment_data_summary=experiment_summary.dropna(),
                alpha=alpha,
                comparison_pairs=comparison_pairs,
                outcome_type=outcome_type,
                effect_type=effect_type
            )
            
            difference_results = calculation.format_outcomes_for_plots(difference_results, outcome_type, effect_type)
            
            for row_number in range(difference_results.shape[0]):
                row = difference_results.iloc[row_number,:]
                result = row["point_estimate"]
                ci_level = min(round((1 - alpha) * 100, 2), 99.999)
                ci_lower = row['ci_lower']
                ci_upper = row['ci_upper']

                result_type = " units"
                if outcome_type == "binary" or effect_type == "Relative Effect":
                    result_type = "%"
                
                significance = "<u>is significant</u>"
                if ci_lower <= 0 <= ci_upper:
                    significance = "is NOT significant"

                formatted_effect_type = "relative "
                if effect_type == "Absolute Effect":
                    formatted_effect_type = "absolute "

                st.write(
                    f"""
                    The difference between {row["group1_name"]} and {row["group2_name"]} **{significance}**, with a mean {formatted_effect_type}difference of **{result}{result_type}**, and a {ci_level}% confidence interval of ({ci_lower}{result_type}, {ci_upper}{result_type})
                    """,
                    unsafe_allow_html=True
                )

            ## ---- Group Difference Plot Generation ---- ##
            group_differences = plot.group_difference_forest(
                data=difference_results,
                outcome_type=outcome_type,
                effect_type=effect_type,
            )

            st.plotly_chart(group_differences, use_container_width=True)

            ## ---- Group Response Plot Generation ---- ##
            group_responses = calculation.group_responses(
                outcome_type=outcome_type,
                experiment_data_summary=experiment_summary.dropna(),
                alpha=alpha
            )

            group_responses = calculation.format_outcomes_for_plots(group_responses, outcome_type, effect_type)

            response_plot = plot.group_response_forest(
                data=group_responses,
                outcome_type=outcome_type,
            )

            st.plotly_chart(response_plot, use_container_width=True)

        else:
            st.write("#### :red[Experiment Summary Error:]")
            st.write(":red[All sample sizes must be great than 0 for each group.]")

            if outcome_type == "binary":
                st.write(":red[The number of successes must be greater than 0 for each group.]")
            else:
                st.write(":red[The mean must be greater than 0 for each group.]")
                st.write(":red[The standard deviation must be greater than 0 for each group.]")

            st.write(":red[Please change the input to meet these specifications.]")
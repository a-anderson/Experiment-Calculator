import streamlit as st
import pandas as pd
from pathlib import Path
from experiment_calculator.core import calculations, validation
from experiment_calculator.ui import components

def show_srm_test():
    st.header("Sample Ratio Mismatch Test")
    st.markdown("") # Extra space for formatting

    col1, spacer, col2 = st.columns([2, 0.2, 3])

    with col1:
        st.write("**Expected proportions and actual counts form each experiment group**")
        st.write(components.input_table_instructions())

        default_data = pd.DataFrame(
            [
                {"Sample Size": 1_000, "Expected Proportion (%)": 50},
                {"Sample Size": 1_000, "Expected Proportion (%)": 50}
            ]
        )

        sample_sizes = st.data_editor(default_data, num_rows="dynamic", hide_index=True)
        sample_sizes_are_valid = validation.valid_srm_data(sample_sizes.dropna())

        threshold = st.number_input(
            label="**P-value threshold for sample ratio mismatch**",
            value=0.001,
            min_value=0.001,
            max_value=1.000,
            step=0.001,
            format="%0.3f",
        )

    with col2:
        if sample_sizes_are_valid:
            sample_sizes["Expected Proportion"] = sample_sizes["Expected Proportion (%)"] / 100
            p_value = calculations.srm_pvalue(sample_sizes.dropna())
            
            if p_value < 0.00001:
                formatted_p_val = f"P value < 0.00001"
            else:
                formatted_p_val = f"P value = {round(p_value, 5):.5f}"

            root_dir = Path(__file__).parents[1]
            if p_value > threshold:
                image_path = str(root_dir / "ui" / "checked.png")
                result_text = (
                    "### :green[There is no sample ratio mismatch error]\n"
                    + f"#### {formatted_p_val}"
                )
            else:
                image_path = str(root_dir / "ui" / "cancel.png")
                result_text = (
                    "### :red[There is a sample ratio mismatch error]\n"
                    + f"#### {formatted_p_val}"
                )

            st.write(result_text)

            image_col1, image_col2, image_col3 = st.columns([1,3,1])

            with image_col2:
                st.image(image_path, width='content')
        
        else:
            st.write("#### :red[Sample Input Error:]")
            st.write(":red[Sample sizes for each individual group must be between 1% and 100%.]")
            st.write(":red[Total expected proportions must be 100% or less.]")
            st.write(":red[Please change the input to meet these specifications.]")


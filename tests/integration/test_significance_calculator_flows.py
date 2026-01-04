import pytest
import pandas as pd
from experiment_calculator.core import calculations, validation

class TestSignificanceCalculatorFlow:
    """Test complete significance testing workflow"""
    
    def test_binary_significance_complete_flow(self):
        """Test: experiment data → validation → group comparisons → CI"""
        # Experiment results
        experiment_data = pd.DataFrame({
            "Group Name": ["Control", "Treatment"],
            "Sample Size": [1000, 1000],
            "Num Successes": [100, 120]
        })
        
        # Validate data
        assert validation.valid_summary_data(experiment_data, "binary")
        
        # Get comparison pairs
        comparison_pairs = calculations.get_comparison_pairs(
            "Compare to first", num_flights=2
        )
        
        # Calculate differences
        differences = calculations.group_differences(
            experiment_data_summary=experiment_data,
            alpha=0.05,
            comparison_pairs=comparison_pairs,
            outcome_type="binary",
            effect_type="Absolute Effect"
        )
        
        # Verify results structure
        assert differences.shape[0] == 1  # One comparison
        assert "point_estimate" in differences.columns
        assert "ci_lower" in differences.columns
        assert "ci_upper" in differences.columns
        
        # Verify point estimate is reasonable
        expected_diff = (120/1000) - (100/1000)
        assert differences["point_estimate"].iloc[0] == pytest.approx(expected_diff, abs=0.001)
    
    def test_normal_significance_complete_flow(self):
        """Test significance calculation for normal outcomes"""
        experiment_data = pd.DataFrame({
            "Group Name": ["Control", "Treatment"],
            "Sample Size": [500, 500],
            "Mean": [100.0, 105.0],
            "StdDev": [15.0, 15.0]
        })
        
        assert validation.valid_summary_data(experiment_data, "normal")
        
        comparison_pairs = calculations.get_comparison_pairs(
            "Compare to first", num_flights=2
        )
        
        differences = calculations.group_differences(
            experiment_data_summary=experiment_data,
            alpha=0.05,
            comparison_pairs=comparison_pairs,
            outcome_type="normal",
            effect_type="Absolute Effect"
        )
        
        # CI should contain the true difference
        true_diff = 105.0 - 100.0
        assert differences["ci_lower"].iloc[0] < true_diff < differences["ci_upper"].iloc[0]
    
    def test_multi_group_all_pairs_comparison(self):
        """Test comparing all pairs with 3 groups"""
        experiment_data = pd.DataFrame({
            "Group Name": ["Control", "Treatment A", "Treatment B"],
            "Sample Size": [1000, 1000, 1000],
            "Num Successes": [100, 110, 120]
        })
        
        comparison_pairs = calculations.get_comparison_pairs(
            "Compare all pairs", num_flights=3
        )
        
        # Should have 3 comparisons: C-A, C-B, A-B
        assert len(comparison_pairs) == 3
        
        differences = calculations.group_differences(
            experiment_data_summary=experiment_data,
            alpha=0.05,
            comparison_pairs=comparison_pairs,
            outcome_type="binary",
            effect_type="Absolute Effect"
        )
        
        assert differences.shape[0] == 3
    
    def test_bonferroni_correction_integration(self):
        """Test that multiple testing correction reduces significance"""
        experiment_data = pd.DataFrame({
            "Group Name": ["Control", "Treatment A", "Treatment B"],
            "Sample Size": [1000, 1000, 1000],
            "Num Successes": [100, 110, 105]
        })
        
        comparison_pairs = calculations.get_comparison_pairs(
            "Compare all pairs", num_flights=3
        )
        
        # Without correction
        alpha_no_correction = calculations.adjusted_alpha(
            base_alpha=0.05,
            num_comparisons=3,
            multiple_comparisons="None"
        )
        
        # With Bonferroni
        alpha_bonferroni = calculations.adjusted_alpha(
            base_alpha=0.05,
            num_comparisons=3,
            multiple_comparisons="Bonferroni"
        )
        
        assert alpha_bonferroni < alpha_no_correction
        assert alpha_bonferroni == pytest.approx(0.05 / 3)
        
        # Calculate with both alphas
        diff_no_correction = calculations.group_differences(
            experiment_data, alpha_no_correction, comparison_pairs, "binary", "Absolute Effect"
        )
        diff_bonferroni = calculations.group_differences(
            experiment_data, alpha_bonferroni, comparison_pairs, "binary", "Absolute Effect"
        )
        
        # Bonferroni should produce wider CIs
        width_no_corr = (diff_no_correction["ci_upper"] - diff_no_correction["ci_lower"]).iloc[0]
        width_bonf = (diff_bonferroni["ci_upper"] - diff_bonferroni["ci_lower"]).iloc[0]
        assert width_bonf > width_no_corr
    
    def test_sequential_testing_correction_integration(self):
        """Test O'Brien-Fleming correction at different information fractions"""
        # Early look (25% of data)
        alpha_early = calculations.adjusted_alpha(
            base_alpha=0.05,
            num_comparisons=1,
            multiple_comparisons="None",
            sequential_testing="O'Brien-Fleming",
            information_fraction=0.25
        )
        
        # Final analysis (100% of data)
        alpha_final = calculations.adjusted_alpha(
            base_alpha=0.05,
            num_comparisons=1,
            multiple_comparisons="None",
            sequential_testing="O'Brien-Fleming",
            information_fraction=1.0
        )
        
        # Early stopping should have stricter threshold
        assert alpha_early < alpha_final
        assert alpha_early < 0.05
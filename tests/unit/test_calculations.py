import pytest
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import tt_ind_solve_power
from experiment_calculator.core.calculations import (
    adjusted_alpha, effect_size, n1_sample_size, 
    minimum_detectable_effect_size, binomial_confidence_interval,
    normal_confidence_interval, srm_pvalue
)

class TestAlphaAdjustments:
    def test_bonferroni_correction(self):
        """Bonferroni should divide alpha by number of comparisons"""
        alpha = adjusted_alpha(0.05, num_comparisons=3, multiple_comparisons="Bonferroni")
        assert alpha == pytest.approx(0.05 / 3)
    
    def test_no_correction(self):
        """No correction should return base alpha"""
        alpha = adjusted_alpha(0.05, num_comparisons=5, multiple_comparisons="None")
        assert alpha == 0.05
    
    def test_obrien_fleming_reduces_alpha(self):
        """O'Brien-Fleming should reduce alpha at early information fractions"""
        alpha_early = adjusted_alpha(
            0.05, 1, "None", "O'Brien-Fleming", information_fraction=0.25
        )
        assert alpha_early < 0.05

class TestEffectSizeCalculations:
    def test_binary_absolute_effect_size(self):
        """Binary absolute effect should match statsmodels"""
        from statsmodels.stats.proportion import proportion_effectsize
        
        baseline = 0.1
        mde = 0.02
        
        result = effect_size("binary", "Absolute Effect", baseline, mde)
        expected = proportion_effectsize(baseline, baseline + mde, method="normal")
        
        assert result == pytest.approx(expected, abs=1e-6)
    
    def test_binary_relative_effect_size(self):
        """Binary relative effect should match statsmodels"""
        from statsmodels.stats.proportion import proportion_effectsize
        
        baseline = 0.1
        mde = 0.2  # 20% relative increase
        
        result = effect_size("binary", "Relative Effect", baseline, mde)
        expected = proportion_effectsize(baseline, baseline * 1.2, method="normal")
        
        assert result == pytest.approx(expected, abs=1e-6)
    
    def test_normal_effect_size_cohens_d(self):
        """Normal effect size should be Cohen's d"""
        baseline_mean = 100
        baseline_std = 15
        mde = 5  # absolute
        
        result = effect_size("normal", "Absolute Effect", baseline_mean, mde, baseline_std)
        expected = 5 / 15  # Cohen's d
        
        assert result == pytest.approx(expected)
    
    def test_effect_size_increases_with_mde(self):
        """Larger MDE should produce larger effect size"""
        es_small = effect_size("binary", "Absolute Effect", 0.1, 0.01)
        es_large = effect_size("binary", "Absolute Effect", 0.1, 0.05)
        assert es_large > es_small # TODO: should this be abs(es_large) > abs(es_small)??

class TestSampleSizeCalculations:
    def test_sample_size_matches_statsmodels(self):
        """Sample size should match statsmodels exactly"""
        effect = 0.2
        alpha = 0.05
        power = 0.8
        ratio = 1.0
        
        result = n1_sample_size(effect, alpha, power, ratio)
        expected = tt_ind_solve_power(effect, None, alpha, power, ratio, "two-sided")
        
        assert result == pytest.approx(np.ceil(expected))
    
    def test_sample_size_increases_with_smaller_effect(self):
        """Smaller effects require larger samples"""
        n_small_effect = n1_sample_size(0.1, 0.05, 0.8, 1.0)
        n_large_effect = n1_sample_size(0.5, 0.05, 0.8, 1.0)
        assert n_small_effect > n_large_effect
    
    def test_sample_size_increases_with_higher_power(self):
        """Higher power requires larger samples"""
        n_low_power = n1_sample_size(0.2, 0.05, 0.5, 1.0)
        n_high_power = n1_sample_size(0.2, 0.05, 0.95, 1.0)
        assert n_high_power > n_low_power
    
    def test_unequal_allocation_increases_sample_size(self):
        """Unequal allocation requires larger samples in smaller group"""
        n_equal = n1_sample_size(0.2, 0.05, 0.8, 1.0)
        n_unequal = n1_sample_size(0.2, 0.05, 0.8, 0.5)  # 2:1 ratio
        assert n_unequal > n_equal

class TestConfidenceIntervals:
    def test_binomial_ci_contains_true_difference(self):
        """CI should contain true proportion difference"""
        # Simulate known difference
        prop1, n1 = 0.1, 1000
        prop2, n2 = 0.15, 1000
        true_diff = 0.05
        
        result = binomial_confidence_interval(prop1, n1, prop2, n2, 0.95, "Absolute Effect")
        
        assert result["ci_lower"][0] < true_diff < result["ci_upper"][0]
    
    def test_normal_ci_width_decreases_with_sample_size(self):
        """Larger samples should produce narrower CIs"""
        ci_small = normal_confidence_interval(100, 15, 100, 105, 15, 100, 0.95, "Absolute Effect")
        ci_large = normal_confidence_interval(100, 15, 10000, 105, 15, 10000, 0.95, "Absolute Effect")
        
        width_small = ci_small["ci_upper"][0] - ci_small["ci_lower"][0]
        width_large = ci_large["ci_upper"][0] - ci_large["ci_lower"][0]
        
        assert width_large < width_small
    
    def test_ci_excludes_zero_for_large_difference(self):
        """Large true difference should produce CI excluding zero"""
        result = binomial_confidence_interval(0.1, 1000, 0.2, 1000, 0.95, "Absolute Effect")
        assert result["ci_lower"][0] > 0

class TestSRMCalculations:
    def test_srm_no_mismatch_high_pvalue(self):
        """Matching proportions should give high p-value"""
        data = pd.DataFrame({
            "Sample Size": [500, 500],
            "Expected Proportion": [0.5, 0.5]
        })
        p_value = srm_pvalue(data)
        assert p_value > 0.05
    
    def test_srm_mismatch_low_pvalue(self):
        """Mismatched proportions should give low p-value"""
        data = pd.DataFrame({
            "Sample Size": [900, 100],  # 90:10 actual
            "Expected Proportion": [0.5, 0.5]  # 50:50 expected
        })
        p_value = srm_pvalue(data)
        assert p_value < 0.001
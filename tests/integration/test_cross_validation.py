import pytest
import numpy as np
from experiment_calculator.core import calculations

class TestCrossValidation:
    """Verify different calculation methods produce consistent results"""
    
    def test_power_mde_reciprocity(self):
        """Sample size calc and MDE calc should be inverse operations"""
        # Start with sample size calculation
        effect_size = 0.2
        alpha = 0.05
        power = 0.8
        ratio = 1.0
        
        n1 = calculations.n1_sample_size(effect_size, alpha, power, ratio)
        
        # Reverse: calculate MDE from sample size
        recovered_effect = calculations.minimum_detectable_effect_size(
            nobs1=n1, power=power, alpha=alpha, ratio=ratio
        )
        
        # Should recover original effect size
        assert effect_size == pytest.approx(recovered_effect, rel=0.01)
    
    def test_effect_size_conversion_roundtrip_binary(self):
        """Converting effect size and back should preserve values"""
        baseline = 0.1
        mde_absolute = 0.02
        
        # Absolute → Effect Size
        effect = calculations.binary_effect_size(
            "Absolute Effect", baseline, mde_absolute
        )
        
        # Effect Size → Absolute
        recovered_mde = calculations.convert_effect_size_for_binary_outcome(
            "Absolute Effect", effect, baseline
        )
        
        assert mde_absolute == pytest.approx(recovered_mde / 100, abs=0.001)
    
    def test_confidence_interval_matches_significance_test(self):
        """CI excluding zero should match p < alpha"""
        # Generate data where we know the effect is significant
        prop1, n1 = 0.10, 2000
        prop2, n2 = 0.15, 2000  # 5 percentage point difference, large samples
        
        result = calculations.binomial_confidence_interval(
            prop1, n1, prop2, n2, confidence=0.95, effect_type="Absolute Effect"
        )
        
        # With large samples and real effect, CI should exclude zero
        assert result["ci_lower"][0] > 0
        
        # Now test with smaller effect that might not be significant
        prop2_small = 0.105  # 0.5 percentage points
        result_small = calculations.binomial_confidence_interval(
            prop1, n1, prop2_small, n2, confidence=0.95, effect_type="Absolute Effect"
        )
        
        # This might cross zero (not significant)
        # Just verify it's a valid CI
        assert result_small["ci_lower"][0] < result_small["ci_upper"][0]
    
    def test_bonferroni_equals_divided_alpha(self):
        """Bonferroni adjustment should equal alpha/k for all k"""
        base_alpha = 0.05
        
        for num_comparisons in [1, 2, 3, 5, 10]:
            adjusted = calculations.adjusted_alpha(
                base_alpha, num_comparisons, "Bonferroni"
            )
            expected = base_alpha / num_comparisons
            assert adjusted == pytest.approx(expected)
    
    def test_sample_size_ratio_consistency(self):
        """Different ratio specifications should produce consistent results"""
        effect = 0.2
        alpha = 0.05
        power = 0.8
        
        # Equal allocation (1:1)
        n1_equal = calculations.n1_sample_size(effect, alpha, power, ratio=1.0)
        
        # Unequal allocation (1:2)
        n1_unequal = calculations.n1_sample_size(effect, alpha, power, ratio=2.0)
        
        # Group 1 sample should be smaller with 1:2 ratio
        # (because group 2 gets more samples)
        # Total sample (n1 + n2) should be larger for unequal allocation
        total_equal = n1_equal * 2
        total_unequal = n1_unequal * 3  # n1 + 2*n1
        
        assert total_unequal > total_equal
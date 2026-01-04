import pytest
import numpy as np
from experiment_calculator.core import calculations

class TestNumericalStability:
    """Test calculations remain stable at extremes"""
    
    def test_very_small_effect_sizes(self):
        """Tiny effects should not cause overflow in sample size"""
        effect = 0.01  # Very small
        n1 = calculations.n1_sample_size(effect, 0.05, 0.8, 1.0)
        
        assert np.isfinite(n1)
        assert n1 > 1000  # Should require large sample
    
    def test_very_large_sample_sizes(self):
        """Large samples should not cause numerical issues in MDE calc"""
        nobs1 = 1_000_000
        mde = calculations.minimum_detectable_effect_size(
            nobs1, power=0.8, alpha=0.05, ratio=1.0
        )
        
        assert np.isfinite(mde)
        assert mde > 0
        assert mde < 1  # Should be very small with huge sample
    
    def test_extreme_power_levels(self):
        """Power close to 0 or 1 should be handled"""
        effect = 0.2
        
        # Low power
        n_low = calculations.n1_sample_size(effect, 0.05, 0.5, 1.0)
        
        # Very high power
        n_high = calculations.n1_sample_size(effect, 0.05, 0.99, 1.0)
        
        assert np.isfinite(n_low)
        assert np.isfinite(n_high)
        assert n_high > n_low
    
    def test_extreme_alpha_levels(self):
        """Very small alpha should not break calculations"""
        effect = 0.2
        
        n = calculations.n1_sample_size(effect, alpha=0.001, power=0.8, ratio=1.0)
        
        assert np.isfinite(n)
        assert n > 0
    
    def test_baseline_rates_near_boundaries(self):
        """Baseline rates close to 0% or 100% should work"""
        # Near 0%
        effect_low = calculations.effect_size(
            "binary", "Absolute Effect", 
            baseline_mean=0.01, mde=0.005
        )
        assert np.isfinite(effect_low)
        
        # Near 100% (relative effect can't exceed 100%)
        effect_high = calculations.effect_size(
            "binary", "Absolute Effect",
            baseline_mean=0.95, mde=0.04
        )
        assert np.isfinite(effect_high)
    
    def test_unequal_variance_normal_ci(self):
        """Welch-Satterthwaite should handle very different variances"""
        result = calculations.normal_confidence_interval(
            mean1=100, stdev1=5, n1=100,
            mean2=105, stdev2=50, n2=100,  # 10x variance
            confidence=0.95,
            effect_type="Absolute Effect"
        )
        
        assert np.isfinite(result["ci_lower"][0])
        assert np.isfinite(result["ci_upper"][0])
        assert result["ci_lower"][0] < result["ci_upper"][0]
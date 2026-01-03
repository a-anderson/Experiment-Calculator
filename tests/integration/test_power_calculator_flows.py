import pytest
import pandas as pd
import numpy as np
from experiment_calculator.core import calculations, validation

class TestPowerCalculatorBinaryFlow:
    """Test complete power calculation workflow for binary outcomes"""
    
    def test_minimum_sample_size_flow_binary_absolute(self):
        """Test full calculation: inputs → sample size → verification"""
        # User inputs
        baseline_mean = 0.10
        mde = 0.02
        alpha = 0.05
        power = 0.8
        ratio = 1.0
        
        # Calculate effect size
        effect = calculations.effect_size(
            outcome_type="binary",
            effect_type="Absolute Effect",
            baseline_mean=baseline_mean,
            mde=mde,
        )
        
        # Calculate required sample size
        n1 = calculations.n1_sample_size(effect, alpha, power, ratio)
        
        # Verify: reverse calculation should recover original power
        recovered_effect = calculations.minimum_detectable_effect_size(
            nobs1=n1, power=power, alpha=alpha, ratio=ratio
        )
        
        assert effect == pytest.approx(recovered_effect, rel=0.01)
        assert n1 > 0
    
    def test_minimum_detectable_effect_flow_binary_relative(self):
        """Test full calculation: sample size → MDE → verification"""
        # User inputs
        baseline_mean = 0.10
        available_sample = 10000
        alpha = 0.05
        power = 0.8
        ratio = 1.0
        
        # Calculate MDE
        nobs1 = available_sample / 2
        effect_size = calculations.minimum_detectable_effect_size(
            nobs1=nobs1, power=power, alpha=alpha, ratio=ratio
        )
        
        # Convert to relative effect
        mde = calculations.convert_effect_size_for_binary_outcome(
            effect_type="Relative Effect",
            effect_size=effect_size,
            prop1=baseline_mean,
        )
        
        # Verify: should be able to detect this effect with given sample
        reverse_n = calculations.n1_sample_size(effect_size, alpha, power, ratio)
        
        assert reverse_n == pytest.approx(nobs1, rel=0.01)
        assert mde > 0
    
    def test_multi_group_power_calculation(self):
        """Test power calculation with 3+ groups"""
        sample_split = pd.DataFrame({
            "Group Name": ["Control", "Treatment A", "Treatment B"],
            "Traffic Allocation (%)": [40, 30, 30]
        })
        
        # Validate inputs
        assert validation.valid_traffic_allocation(sample_split)
        
        # Calculate ratios
        calculation_ratios = sample_split["Traffic Allocation (%)"] / 40
        ratio = calculations.design_ratio(calculation_ratios)
        
        # Calculate sample size
        effect = 0.2
        n1 = calculations.n1_sample_size(effect, 0.05, 0.8, ratio)
        
        # Total sample should be sum of all groups
        total_sample = n1 * sum(calculation_ratios)
        
        assert total_sample > n1  # Multi-group requires more samples
        assert ratio < 1  # Limiting ratio for unequal allocation

class TestPowerCalculatorNormalFlow:
    """Test complete power calculation workflow for normal outcomes"""
    
    def test_minimum_sample_size_flow_normal_absolute(self):
        """Test full calculation for normal outcome with absolute effect"""
        baseline_mean = 100
        baseline_std = 15
        mde = 5  # absolute units
        
        effect = calculations.effect_size(
            outcome_type="normal",
            effect_type="Absolute Effect",
            baseline_mean=baseline_mean,
            mde=mde,
            baseline_stdev=baseline_std,
        )
        
        n1 = calculations.n1_sample_size(effect, 0.05, 0.8, 1.0)
        
        # Verify Cohen's d calculation
        expected_cohens_d = mde / baseline_std
        assert effect == pytest.approx(expected_cohens_d)
        assert n1 > 0
    
    def test_power_curve_generation(self):
        """Test that power curve data can be generated correctly"""
        effect_size = 0.2
        power_range = np.linspace(0.1, 0.99, 90)
        alpha = 0.05
        ratio = 1.0
        flight_ratios = pd.Series([1.0, 1.0])
        
        # Generate sample size list for power curve
        sample_sizes = calculations.sample_size_list(
            effect_size=effect_size,
            power_range=power_range,
            alpha=alpha,
            limiting_ratio=ratio,
            flight_ratios=flight_ratios,
        )
        
        # Verify properties
        assert len(sample_sizes) == len(power_range)
        assert all(n > 0 for n in sample_sizes)
        # Higher power requires larger samples
        assert sample_sizes[0] < sample_sizes[-1]
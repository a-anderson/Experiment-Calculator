import pytest
import pandas as pd
from experiment_calculator.core import calculations, validation

class TestSRMFlow:
    """Test complete SRM workflow"""
    
    def test_srm_complete_flow_no_mismatch(self):
        """Test SRM detection when proportions match"""
        data = pd.DataFrame({
            "Sample Size": [5000, 5000],
            "Expected Proportion (%)": [50, 50]
        })
        
        # Validate
        assert validation.valid_srm_data(data)
        
        # Convert percentages
        data["Expected Proportion"] = data["Expected Proportion (%)"] / 100
        
        # Calculate p-value
        p_value = calculations.srm_pvalue(data)
        
        # Should not detect mismatch
        assert p_value > 0.05
    
    def test_srm_complete_flow_with_mismatch(self):
        """Test SRM detection when proportions don't match"""
        data = pd.DataFrame({
            "Sample Size": [9000, 1000],  # 90:10 split
            "Expected Proportion (%)": [50, 50]  # Expected 50:50
        })
        
        assert validation.valid_srm_data(data)
        
        data["Expected Proportion"] = data["Expected Proportion (%)"] / 100
        p_value = calculations.srm_pvalue(data)
        
        # Should detect strong mismatch
        assert p_value < 0.001
    
    def test_srm_three_way_split(self):
        """Test SRM with 3 groups"""
        data = pd.DataFrame({
            "Sample Size": [3333, 3333, 3334],  # Roughly equal
            "Expected Proportion (%)": [33.33, 33.33, 33.34]
        })
        
        data["Expected Proportion"] = data["Expected Proportion (%)"] / 100
        p_value = calculations.srm_pvalue(data)
        
        # Should not detect mismatch
        assert p_value > 0.05
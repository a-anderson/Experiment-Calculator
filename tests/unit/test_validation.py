import pytest
import pandas as pd
from experiment_calculator.core.validation import (
    valid_traffic_allocation, valid_summary_data, valid_srm_data
)

class TestTrafficValidation:
    def test_valid_50_50_split(self):
        data = pd.DataFrame({"Traffic Allocation (%)": [50, 50]})
        assert valid_traffic_allocation(data) is True
    
    def test_invalid_over_100_percent(self):
        data = pd.DataFrame({"Traffic Allocation (%)": [60, 60]})
        assert valid_traffic_allocation(data) is False
    
    def test_invalid_negative_allocation(self):
        data = pd.DataFrame({"Traffic Allocation (%)": [-10, 110]})
        assert valid_traffic_allocation(data) is False
    
    def test_invalid_zero_allocation(self):
        data = pd.DataFrame({"Traffic Allocation (%)": [0, 100]})
        assert valid_traffic_allocation(data) is False
    
    def test_valid_unequal_split(self):
        data = pd.DataFrame({"Traffic Allocation (%)": [30, 70]})
        assert valid_traffic_allocation(data) is True

class TestSummaryDataValidation:
    def test_valid_binary_data(self):
        data = pd.DataFrame({
            "Sample Size": [100, 100],
            "Num Successes": [10, 15]
        })
        assert valid_summary_data(data, "binary") is True
    
    def test_invalid_binary_zero_samples(self):
        data = pd.DataFrame({
            "Sample Size": [0, 100],
            "Num Successes": [0, 15]
        })
        assert valid_summary_data(data, "binary") is False
    
    def test_valid_normal_data(self):
        data = pd.DataFrame({
            "Sample Size": [100, 100],
            "Mean": [5.0, 6.0],
            "StdDev": [2.0, 2.5]
        })
        assert valid_summary_data(data, "normal") is True
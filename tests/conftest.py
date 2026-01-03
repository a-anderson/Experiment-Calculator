import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def binary_baseline():
    return {"baseline_rate": 0.1, "mde": 0.02, "alpha": 0.05, "power": 0.8}

@pytest.fixture
def normal_baseline():
    return {"baseline_mean": 100, "baseline_std": 15, "mde": 5, "alpha": 0.05, "power": 0.8}

@pytest.fixture
def sample_experiment_data_binary():
    return pd.DataFrame({
        "Group Name": ["Control", "Treatment"],
        "Sample Size": [1000, 1000],
        "Num Successes": [100, 120]
    })

@pytest.fixture
def sample_experiment_data_normal():
    return pd.DataFrame({
        "Group Name": ["Control", "Treatment"],
        "Sample Size": [1000, 1000],
        "Mean": [100.0, 105.0],
        "StdDev": [15.0, 16.0]
    })
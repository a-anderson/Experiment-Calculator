# Experiment Calculator

## About

The goal of Experiment Calculator is to provide a simple calculator to plan, analyse and diagnose simple experiments. This a python streamlit version of the [Experiment Calculator](https://github.com/sabush/ExperimentCalculator) app designed by [Stephen Bush](https://github.com/sabush).

## Usage

There are three calculators in this app.

1. A [power calculator](calculator_types/power_calculator.md) for experiment design.
    - Available for binary or normally distributed outcomes.
2. A [significance calculator](calculator_types/significance_calculator.md) for experiment result analysis.
    - Available for binary or normally distributed outcomes.
3. A [sample ratio mismatch calculator](calculator_types/srm_calculator.md) to identify statistically significant deviations from the expected sample proportions.

## Power calculator example

Please click on the links above for examples of all calculator types and explanations of their contents.

<img src="calculator_types/images/power_binary.png" alt="example image for the binary power calculator usage"/>

## Installation

#### Option 1

1. Clone this repository.
2. Install the required packages:
    - Install Python ≥ 3.11
    - Install [Poetry](https://python-poetry.org/docs/)
    - Move to the Experiment Calculator folder and run `poetry install`
3. Run the Experiment Calculator app

    `poetry run streamlit run experiment_calculator/streamlit_main.py`

#### Option 2

1. Clone this repository.
2. Install the required packages:

    - Install Python ≥ 3.11
    - Move to the Experiment Calculator folder, create and activate a virtual environment, and install the required packages from `requirements.txt`.

    ```bash
    python3 -m venv venv
    source venv/bin/activte
    python -m pip install -r requirements.txt
    ```

3. Run the Experiment Calculator app

    `python -m streamlit run experiment_calculator/streamlit_main.py`

## License

This project is licensed under the [MIT License](LICENSE).

### Credits

The check mark and cross mark icons used in this app were made by Iconjam from www.flaticon.com

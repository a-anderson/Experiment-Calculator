# Experiment Calculator

## About

The goal of Experiment Calculator is to provide a simple calculator to plan, analyse and diagnose simple experiments. This a python steamlit version of the [Experiment Calculator](https://github.com/sabush/ExperimentCalculator) app designed by [Stephen Bush](https://github.com/sabush).

## Usage

There are three calculators in this app.

1. A [power calculator](calculator_types/power_calculator.md) for experiment design.
    - Available for binary or normally distributed outcomes.
2. A [significance calculator](calculator_types/significance_calculator.md) for experiment result analysis.
    - Available for binary or normally distributed outcomes.
3. A [sample ratio mismatch calculator](calculator_types/srm_calculator.md) to identify statistically significant deviations from the expected sample proportions.

## Power calculator example

Please click on the links above for examples for all calculator types and explanations of their contents.

<img src="calculator_types/images/power_binary.png" alt="example image for the binary power calculator usage"/>

### Installation

1. Clone this repository.
2. Install the required packages:
    - Install Python ≥ 3.11
    - Install Poetry
    - Move to the Experiment Calculator folder and run `poetry init`
3. Run the Experiment Calculator app

    `poetry run streamlit run experiment_calculator/streamlit_main.py`

## License

This project is licensed under the [MIT License](LICENSE).

#### Credits

The check mark and cross mark icons used in this app were made by Iconjam from www.flaticon.com

# ChileCensusDP

This document describes important things to consider when using the implementation of the TopDown algorithm for the 2017 Chilean Census, adapted from the implementation used in the 2020 United States Census. The system transforms raw census microdata into synthetic microdata protected by differential privacy, preserving statistical utility through sophisticated optimization techniques and processing data hierarchically through hierarchical divisions.

## Usage

To use the TopDown algorithm, you need to have the correct Python environment set up. Also you need to set the parameters according to your needs. In the next section, we will explain how to configure the algorithm and run it.

Create a Python virtual environment and install the required dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows just use `venv\Scripts\activate`
pip install -r requirements.txt
```

Run the algorithm using the provided `main.py` script:

```bash
python main.py
```

An important disclaimer is that the algorithm used Gurobi as the optimization solver, which requires a valid license. If you do not have a Gurobi license, you can use the `gurobipy` package in a limited mode, but this may affect the performance and results of the algorithm. For more information on how to obtain a Gurobi license, visit [Gurobi's official website](https://www.gurobi.com/).

## Parameter Configuration

The system is configured programmatically through setter methods provided by the `TopDown` class. An example of how to configure and run the algorithm can be found in the [`main.py`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/main.py) file.

The main parameters that must be configured include:

- **Geographic hierarchy**: Defined using `set_geo_columns()`, which accepts a list of geographic levels to process (e.g., `['REGION', 'PROVINCIA', 'COMUNA']`).
- **Privacy parameters**: Differential privacy budgets are specified using `set_privacy_parameters()`, often computed exponentially as in the example. The noise mechanism is selected with `set_mechanism()`, supporting `'discrete_gauss'` and `'discrete_laplace'`.
- **Data paths**: The input data is loaded via `read_data(path)`, and the output location is configured with `set_output_path()`. Optionally, previously processed data can be loaded using `read_processed_data(path)`.
- **Query definition**: The demographic variables to analyze are defined using `set_queries()`, e.g., `['P08', 'P09']` for sex and age.
- **Constraints**:
  - `set_geo_constraints()` allows defining consistency constraints for each geographic level.
  - `set_root_constraints()` applies global constraints, such as total population counts.

Additional optional configuration includes:

- **Distance metric**: Set via `set_distance_metric()`, which can be `'manhattan'`, `'euclidean'`, `'cosine'`, or `None` if not used. This is helpful for validation or benchmarking.

Once configured, the algorithm is executed via `topdown.run()`, which handles all stages: preprocessing, measurement, estimation, and synthetic data generation.

## Initialization

When the algorithms starts, the initialization is performed through the [`init_routine()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L59) method of the [`TopDown`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L14) class. This process includes:

- **Permutation generation**: The [`compute_permutation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L41) method generates all possible combinations of demographic values. This creates a permutation matrix representing every possible query combination to construct contingency vectors.
- **Root node creation**: The root node is initialized with its contingency vector representing the full demographic distribution of the dataset.
**Geographic tree construction**: The hierarchical structure is built using the [`GeographicTree`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/geographic_tree.py#L8) class, which handles contingency vector construction and noise application.

## Measurement Phase

The [`measurement phase`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L106) applies differential privacy mechanisms to the contingency vectors:

**Mechanism selection**: The [`set_mechanism()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L249) method sets the privacy mechanism based on configuration.

**Noise application**: The [`apply_noise()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L260) method traverses the geographic tree and applies the selected noise mechanism with level-specific privacy budgets.

**Noise generation**: Discrete noise is generated using [`sample_dgauss()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/discretegauss.py#L125) and [`sample_dlaplace()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/discretegauss.py#L88) implementations from the `discretegauss.py` module according to the selected mechanism.

## Estimation Phase

The [`estimation phase`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L106) uses optimization to estimate consistent contingency vectors that preserves defined constraints defined by the user, for example, that the value of the population in a state is the real value instead of the noisy value.:

**Root estimation**: Begins with root node optimization using [`root_estimation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L129).

**Recursive estimation**: The [`recursive_estimation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L135) method processes nodes level-by-level using queue-based traversal.

**Two-phase optimization**:
1. Non-negative real estimation using [`non_negative_real_estimation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/optimizer.py#L12)  
2. Integer rounding using [`rounding_estimation()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/optimizer.py#L49)

Both phases use the Gurobi mathematical optimization solver via the [`OptimizationModel`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/optimizer.py#L6) class to maintain parent-child consistency across the geographic hierarchy.

## Microdata Generation

Final generation of synthetic microdata is performed via the [`construct_microdata()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L188) method:

**Recursive construction**: The [`recursive_construct_microdata()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L211) method traverses leaf nodes and creates individual records.

**Individual sampling**: For each permutation combination, demographic values are [`replicated`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L229) according to the counts in the contingency vector.

**Data output**: The [`result`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L205) is a CSV file containing synthetic records that maintain statistical properties while protecting individual privacy.

## Resume Functionality

The system includes resume capabilities for interrupted processes via:

- [`load_state()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L359): Recovers previous processing state  
- [`extend_tree()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L367): Adds new geographic levels to the existing tree  
- [`resume_measurement_phase()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L379): Applies noise to new nodes  
- [`resume_estimation_phase()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L396): Optimizes new geographic levels  

The [`resume_run()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L409) method allows continuation from where processing was stopped.

## Quality Validation

The system includes correctness validation to ensure data consistency:

- [`check_correctness()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L270): Verifies parent-child sum consistency  
- [`check_correctness_node()`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/top_down.py#L281): Validates consistency of individual nodes  
- [`Distance metrics`](https://github.com/Yiruzz/ChileCensusDP/blob/afeb2a05323d2c622327d3b35c62ea22edf9d67d/utils.py#L3): Measure the privacy-utility trade-off

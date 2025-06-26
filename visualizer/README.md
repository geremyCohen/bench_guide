# Benchmark Visualizer

A tool for running benchmarks on remote VMs and visualizing the results.

## Features

- Run benchmarks on multiple cloud VMs (AWS, GCP, Azure)
- Collect and parse benchmark results
- Generate HTML reports with interactive charts
- Extensible architecture for adding new benchmark types

## Requirements

- Python 3.6+
- AWS CLI configured with appropriate credentials
- SSH access to target VMs

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/geremyCohen/bench_guide.git
   cd bench_guide/visualizer
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the visualizer:

```
python visualizer.py
```

Follow the interactive prompts to:
1. Select cloud provider (currently only AWS is supported)
2. Choose target VMs to run benchmarks on
3. Select which benchmarks to run

The tool will:
1. SSH into each selected VM
2. Clone the benchmark repository
3. Run the selected benchmarks
4. Collect and parse the results
5. Generate an HTML report with visualizations

## Architecture

The visualizer follows a modular architecture:

- `cloud_providers/`: Modules for interacting with different cloud providers
- `parsers/`: Modules for parsing benchmark outputs into a common format
- `visualizers/`: Modules for generating visualizations from the common format

## Adding New Benchmarks

To add support for a new benchmark:

1. Create a benchmark directory in the main repository
2. Include a `benchmark.sh` script that runs the benchmark
3. Include a `setup.sh` script for installing dependencies
4. Optionally add an `outputs_info.txt` file listing output files to collect

## Adding New Cloud Providers

To add support for a new cloud provider:

1. Create a new module in `cloud_providers/`
2. Implement the `get_instances()` function that returns a list of instances

## License

[MIT License](LICENSE)
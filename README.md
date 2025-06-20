# Arm vs x86 Benchmarking Guide

This repository contains benchmark scripts and code examples to accompany the Arm Learning Path on benchmarking and performance comparison between Arm and x86 architectures.

## Repository Structure

- `cpu_utilization/`: Scripts for measuring CPU utilization
  - `cpu_benchmark.sh`: Measures CPU utilization under different loads

## Usage

Each directory contains scripts for specific benchmarking scenarios. Follow the instructions in the corresponding learning path module to use these scripts effectively.

### CPU Utilization

```bash
cd cpu_utilization
./cpu_benchmark.sh | tee cpu_benchmark_results.txt
```

## Requirements

- Ubuntu Linux (works on both x86_64 and aarch64)
- Required packages: sysstat, stress-ng

## License

MIT
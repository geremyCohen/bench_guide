# CPU Utilization Benchmarks

This directory contains scripts for measuring and comparing CPU utilization across Intel/AMD (x86_64) and Arm (aarch64) architectures.

## Scripts

- `setup.sh`: Installs required dependencies
- `cpu_benchmark.sh`: Measures CPU utilization under different loads (full, half, and single core)

## Setup

First, run the setup script to install required dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

This will install the necessary packages (sysstat, stress-ng).

## Usage

After running setup.sh, execute the benchmark:

```bash
./cpu_benchmark.sh | tee cpu_benchmark_results.txt
```

## Output

The script provides:
- System information (architecture, CPU model, core count)
- Average CPU utilization across all cores
- Per-core utilization statistics
- Results for three different load scenarios:
  1. Full load (all cores)
  2. Half load (half of available cores)
  3. Single core load

## Analysis

When comparing results between architectures, focus on:
1. Overall CPU utilization
2. Per-core distribution
3. Scaling behavior as load increases

## Example Results

### x86_64 (Intel/AMD)
```
=== System Information ===
Architecture: Intel/AMD (x86_64)
CPU Model: Intel(R) Xeon(R) CPU @ 2.80GHz
CPU Cores: 4

=== CPU Utilization Results ===
Average CPU utilization (all cores): 99.75%
```

### aarch64 (Arm)
```
=== System Information ===
Architecture: Arm (aarch64)
CPU Model: Neoverse-N1
CPU Cores: 4

=== CPU Utilization Results ===
Average CPU utilization (all cores): 99.82%
```
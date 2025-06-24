# Arm vs x86 Benchmarking Guide

This repository contains benchmark scripts and code examples to accompany the Arm Learning Path on benchmarking and performance comparison between Arm and x86 architectures.

## Repository Structure

Each directory contains scripts for specific benchmarking scenarios:

- `cpu_utilization/`: CPU utilization benchmarks
- `memory_bandwidth/`: Memory bandwidth benchmarks using STREAM
- `branch_prediction/`: Branch prediction and speculative execution benchmarks
- `cache_performance/`: Cache performance benchmarks
- `io_performance/`: I/O performance benchmarks
- `network_performance/`: Network performance benchmarks
- `system_latency/`: System latency and jitter benchmarks
- `power_efficiency/`: Power efficiency benchmarks
- `floating_point/`: Floating-point performance benchmarks
- `context_switching/`: Context switching benchmarks
- `virtualization/`: Virtualization performance benchmarks
- `page_size_tlb/`: Page size and TLB performance benchmarks
- `simd_vector/`: SIMD and vector performance benchmarks
- `atomic_operations/`: Atomic operations benchmarks
- `instruction_latency/`: Instruction latency benchmarks
- `microarchitectural/`: Microarchitectural features benchmarks
- `energy_efficiency/`: Energy efficiency workloads
- `mixed_workload/`: Mixed workload performance benchmarks
- `security_impact/`: Security feature impact benchmarks
- `crypto_extensions/`: Arm cryptography extensions benchmarks
- `memory_tagging/`: Arm memory tagging extension benchmarks
- `numa_aware/`: NUMA-aware scheduling benchmarks
- `memory_prefetch/`: Memory prefetch optimizations benchmarks
- `cache_management/`: Cache management instructions benchmarks
- `pointer_authentication/`: Pointer authentication benchmarks
- `dsp_instructions/`: DSP instructions benchmarks

## Usage

Each directory contains:
1. A `setup.sh` script to install required dependencies
2. Benchmark scripts and source code
3. A README with specific instructions

Follow these general steps:
1. Run `setup.sh` to install dependencies
2. Run the benchmark scripts
3. Compare results between Arm and x86 systems

## Requirements

- Ubuntu Linux (works on both x86_64 and aarch64)
- Required packages are installed by the setup scripts

## License

MIT
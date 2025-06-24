# Memory Bandwidth Benchmarks

This directory contains scripts for measuring and comparing memory bandwidth across Intel/AMD (x86_64) and Arm (aarch64) architectures using the STREAM benchmark.

## Scripts

- `setup.sh`: Installs required dependencies and downloads/compiles the STREAM benchmark
- `memory_benchmark.sh`: Script to run the memory bandwidth benchmark with multiple iterations and thread counts

## Setup

First, run the setup script to install required dependencies and download/compile the STREAM benchmark:

```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. Install necessary packages (build-essential, git, time)
2. Download the STREAM benchmark from GitHub
3. Compile the benchmark with optimizations

## Running the Benchmark

After setup is complete, run the benchmark script:

```bash
chmod +x memory_benchmark.sh
./memory_benchmark.sh | tee memory_benchmark_results.txt
```

## Benchmark Details

The STREAM benchmark measures memory bandwidth through four vector operations:
1. **Copy**: a(i) = b(i)
2. **Scale**: a(i) = q*b(i)
3. **Add**: a(i) = b(i) + c(i)
4. **Triad**: a(i) = b(i) + q*c(i)

The script runs each operation:
- 5 times with the maximum number of threads
- Once each with 1, 2, 4, and max threads to test scaling

## Output

The benchmark produces output showing:
- System information (architecture, CPU model, memory)
- Memory bandwidth for each operation in MB/s
- Scaling behavior with different thread counts

## Analysis

When comparing results between architectures, focus on:
1. **Peak Memory Bandwidth**: Compare the maximum bandwidth achieved on each architecture
2. **Scaling Behavior**: How does bandwidth scale with increasing thread count?
3. **Operation Differences**: Are there differences between Copy, Scale, Add, and Triad operations?

## Example Results

### x86_64 (Intel/AMD)
```
Copy: 24576.0 MB/s
Scale: 16384.0 MB/s
Add: 18432.0 MB/s
Triad: 18432.0 MB/s
```

### aarch64 (Arm)
```
Copy: 22528.0 MB/s
Scale: 15360.0 MB/s
Add: 17408.0 MB/s
Triad: 17408.0 MB/s
```
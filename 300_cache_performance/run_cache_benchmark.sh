#!/bin/bash

# Get architecture
arch=$(uname -m)
echo "Architecture: $arch"
echo "CPU: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)"

# Compile the benchmark
gcc -O2 cache_benchmark.c -o cache_benchmark

# Run sequential access benchmark
echo "Running sequential access benchmark..."
./cache_benchmark 0 > sequential_access.csv

# Run random access benchmark
echo "Running random access benchmark..."
./cache_benchmark 1 > random_access.csv

# Run strided access benchmark with different strides
echo "Running strided access benchmark..."
for stride in 1 2 4 8 16 32 64 128; do
    echo "  Stride: $stride"
    ./cache_benchmark 2 $stride > strided_access_${stride}.csv
done

echo "Benchmark complete. Results saved to CSV files."
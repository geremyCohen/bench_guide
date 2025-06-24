#!/bin/bash

# Function to get architecture
get_arch() {
  arch=$(uname -m)
  if [[ "$arch" == "x86_64" ]]; then
    echo "Intel/AMD (x86_64)"
  elif [[ "$arch" == "aarch64" ]]; then
    echo "Arm (aarch64)"
  else
    echo "Unknown architecture: $arch"
  fi
}

# Display system information
echo "=== System Information ==="
echo "Architecture: $(get_arch)"
echo "CPU Model:"
lscpu | grep "Model name"
echo ""

# Compile benchmarks
echo "Compiling atomic operation benchmarks..."
gcc -O3 -march=native -pthread lse_benchmark.c -o lse_benchmark
gcc -O3 -march=native -pthread lockfree_queue_benchmark.c -o lockfree_queue_benchmark

# Run LSE benchmark
echo "Running LSE atomic operations benchmark..."
./lse_benchmark

echo ""

# Run lock-free queue benchmark
echo "Running lock-free queue benchmark..."
./lockfree_queue_benchmark

echo "Atomic operations benchmark complete!"


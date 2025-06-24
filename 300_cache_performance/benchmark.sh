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
echo "Compiling cache benchmarks..."
gcc -O3 -march=native cache_benchmark.c -o cache_benchmark
gcc -O3 -march=native arm_prefetch.c -o arm_prefetch
gcc -O3 -march=native arm_cache_management.c -o arm_cache_management

# Run main benchmark
echo "Running cache performance benchmark..."
./run_cache_benchmark.sh

# Run ARM-specific optimizations if on ARM
if [ "$(uname -m)" = "aarch64" ]; then
    echo "Running ARM prefetch optimizations..."
    ./arm_prefetch
    echo "Running ARM cache management optimizations..."
    ./arm_cache_management
fi

# Generate plots
echo "Generating visualization plots..."
python3 plot_cache_results.py

echo "Cache performance benchmark complete!"


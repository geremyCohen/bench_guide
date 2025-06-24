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

# Compile and run page_size_tlb benchmark
echo "Compiling page_size_tlb benchmark..."
gcc -O2 benchmark_main.c -o benchmark_main
echo "Running page_size_tlb benchmark..."
./benchmark_main

echo "Page Size Tlb benchmark complete!"


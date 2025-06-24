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
echo "Memory Information:"
free -h
echo ""

# Set environment variables for OpenMP
export OMP_NUM_THREADS=$(nproc)

# Check if we're in the STREAM directory
if [ ! -f "./stream" ]; then
  if [ -f "../STREAM/stream" ]; then
    cd ../STREAM
  elif [ -f "./STREAM/stream" ]; then
    cd ./STREAM
  else
    echo "Error: STREAM benchmark not found. Please run setup.sh first."
    exit 1
  fi
fi

# Run STREAM benchmark
echo "=== Running STREAM Memory Bandwidth Benchmark ==="
echo "Using $(nproc) threads"

# Run the benchmark multiple times and calculate average
echo "Running 5 iterations..."
for i in {1..5}; do
  echo "Iteration $i:"
  ./stream | grep -E "Copy:|Scale:|Add:|Triad:"
  echo ""
  sleep 2
done

# Run with different thread counts to test scaling
echo "=== Testing Memory Bandwidth Scaling ==="
for threads in 1 2 4 $(nproc); do
  if [ $threads -le $(nproc) ]; then
    echo "Running with $threads threads:"
    export OMP_NUM_THREADS=$threads
    ./stream | grep -E "Copy:|Scale:|Add:|Triad:"
    echo ""
    sleep 2
  fi
done
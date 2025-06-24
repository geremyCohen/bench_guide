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

# Compile network benchmark
echo "Compiling network benchmark..."
gcc -O2 network_benchmark.c -o network_benchmark

# Run network benchmark
echo "Starting network benchmark..."
echo "Starting server in background..."
./network_benchmark server &
SERVER_PID=$!

sleep 2

echo "Starting client..."
./network_benchmark client

# Clean up
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo "Network performance benchmark complete!"
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
echo "CPU Cores: $(nproc)"
echo ""

# Function to run test and measure CPU utilization
run_test() {
  local load=$1
  local duration=$2
  
  echo "=== Running CPU test with $load load for $duration seconds ==="
  
  # Start mpstat in background
  mpstat -P ALL 1 $duration > mpstat_output.txt &
  mpstat_pid=$!
  
  # Run stress-ng
  stress-ng --cpu $load --timeout $duration
  
  # Wait for mpstat to finish
  wait $mpstat_pid
  
  # Calculate average CPU utilization
  echo "=== CPU Utilization Results ==="
  echo "Average CPU utilization (all cores):"
  awk '/Average:/ && $2 ~ /all/ {print 100 - $NF "%"}' mpstat_output.txt
  
  echo "Per-core utilization:"
  awk '/Average:/ && $2 ~ /^[0-9]/ {print "Core " $2 ": " 100 - $NF "%"}' mpstat_output.txt
  
  echo ""
}

# Run tests with different loads
run_test $(nproc) 30  # Full load (all cores)
run_test $(($(nproc) / 2)) 30  # Half load
run_test 1 30  # Single core load
#!/bin/bash

# Configuration parameters
TEST_DURATION=300  # Duration in seconds for each test run

echo "CPU Benchmark Script v2.0 - $(date)"

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
  local run_name=$3
  
  echo "=== Running CPU test with $load load for $duration seconds (Run: $run_name) ==="
  
  # Create output files with run name
  local mpstat_file="mpstat_${run_name}.txt"
  local results_file="results_${run_name}.txt"
  
  # Start mpstat in background (run for duration + 1 to ensure we capture the entire stress period)
  mpstat -P ALL 1 $(($duration + 1)) > "$mpstat_file" &
  mpstat_pid=$!
  
  # Run stress-ng
  stress-ng --cpu $load --timeout $duration
  
  # Wait for mpstat to finish
  wait $mpstat_pid
  
  # Calculate average CPU utilization and save to results file
  echo "=== CPU Utilization Results (Run: $run_name) ===" | tee -a "$results_file"
  echo "Run: $run_name" | tee -a "$results_file"
  echo "Load: $load cores" | tee -a "$results_file"
  echo "Duration: $duration seconds" | tee -a "$results_file"
  
  echo "Average CPU utilization (all cores):" | tee -a "$results_file"
  avg_util=$(awk '/Average:/ && $2 ~ /all/ {print 100 - $NF}' "$mpstat_file")
  echo "$avg_util%" | tee -a "$results_file"
  
  echo "Per-core utilization:" | tee -a "$results_file"
  awk '/Average:/ && $2 ~ /^[0-9]/ {print "Core " $2 ": " 100 - $NF "%"}' "$mpstat_file" | tee -a "$results_file"
  
  # Create a metadata file for this run
  echo "Creating metadata file for $run_name"
  echo "run_name=$run_name" > "metadata_${run_name}.txt"
  echo "load=$load" >> "metadata_${run_name}.txt"
  echo "duration=$duration" >> "metadata_${run_name}.txt"
  echo "avg_utilization=$avg_util" >> "metadata_${run_name}.txt"
  
  echo ""
}

# Run tests with different loads
run_test $(nproc) $TEST_DURATION "full_load"  # Full load (all cores)
run_test $(($(nproc) / 2)) $TEST_DURATION "half_load"  # Half load
run_test 1 $TEST_DURATION "single_core"  # Single core load

# Create a manifest file listing all runs
echo "Creating runs manifest file"
echo "full_load half_load single_core" > runs_manifest.txt

# Create a simple consolidated results file with actual data
echo "Creating consolidated results file"
{
  echo "Architecture: $(get_arch)"
  echo "Model name: $(lscpu | grep "Model name" | cut -d: -f2 | xargs)"
  echo "CPU Cores: $(nproc)"
  echo ""
  
  # Add results from each run
  for run in full_load half_load single_core; do
    if [ -f "metadata_${run}.txt" ]; then
      echo "Run: $run"
      cat "metadata_${run}.txt"
      echo ""
    fi
  done
} > cpu_benchmark_results.txt

# List all files created for debugging
echo "Files created in current directory:"
ls -la *.txt 2>/dev/null || echo "No .txt files found"

# Create outputs_info.txt for the visualizer
echo "Creating outputs_info.txt for the visualizer"
cat > outputs_info.txt << EOF
cpu_benchmark_results.txt
runs_manifest.txt
metadata_full_load.txt
metadata_half_load.txt
metadata_single_core.txt
mpstat_full_load.txt
mpstat_half_load.txt
mpstat_single_core.txt
results_full_load.txt
results_half_load.txt
results_single_core.txt
EOF

echo "Benchmark script completed successfully"
#!/bin/bash

# Get architecture
arch=$(uname -m)
echo "Architecture: $arch"
echo "CPU: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)"

# Initialize results file
echo "pattern,time,branches_per_second" > branch_results.csv

# Run benchmarks for different patterns
for pattern in 0 1 2 3 4; do
    echo "Running pattern $pattern..."
    
    # Run with perf if available
    if command -v perf &> /dev/null; then
        echo "Measuring branch mispredictions..."
        perf stat -e branches,branch-misses ./branch_benchmark $pattern 2>&1 | tee pattern_${pattern}_perf.txt
    fi
    
    # Run normal benchmark
    ./branch_benchmark $pattern | tee pattern_${pattern}.txt
    
    # Extract results
    time=$(grep "Time:" pattern_${pattern}.txt | awk '{print $2}')
    branches=$(grep "Branches per second:" pattern_${pattern}.txt | awk '{print $4}')
    
    # Save to CSV
    echo "$pattern,$time,$branches" >> branch_results.csv
done

echo "Benchmark complete. Results saved to branch_results.csv"
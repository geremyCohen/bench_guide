#!/bin/bash

# Check if running on Arm
arch=$(uname -m)
if [[ "$arch" != "aarch64" ]]; then
    echo "This script is designed for Arm architectures only."
    exit 1
fi

echo "Architecture: $arch"
echo "CPU: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)"

# Initialize results file
echo "pattern,test_type,time,operations_per_second" > arm_optimized_results.csv

# Run benchmarks for different patterns
for pattern in 0 1 2 3 4; do
    echo "Running pattern $pattern..."
    
    # Run with branch hints
    echo "  With branch hints..."
    ./branch_benchmark_arm_optimized $pattern 0 | tee pattern_${pattern}_hints.txt
    
    # Run branchless version
    echo "  With branchless code..."
    ./branch_benchmark_arm_optimized $pattern 1 | tee pattern_${pattern}_branchless.txt
    
    # Extract results for branch hints
    time_hints=$(grep "Time:" pattern_${pattern}_hints.txt | awk '{print $2}')
    ops_hints=$(grep "Operations per second:" pattern_${pattern}_hints.txt | awk '{print $4}')
    
    # Extract results for branchless
    time_branchless=$(grep "Time:" pattern_${pattern}_branchless.txt | awk '{print $2}')
    ops_branchless=$(grep "Operations per second:" pattern_${pattern}_branchless.txt | awk '{print $4}')
    
    # Save to CSV
    echo "$pattern,hints,$time_hints,$ops_hints" >> arm_optimized_results.csv
    echo "$pattern,branchless,$time_branchless,$ops_branchless" >> arm_optimized_results.csv
done

echo "Benchmark complete. Results saved to arm_optimized_results.csv"

# Compare with original benchmark
if [ -f branch_results.csv ]; then
    echo "Comparing with original benchmark..."
    echo "pattern,original_time,optimized_time,improvement_percent" > comparison_results.csv
    
    for pattern in 0 1 2 3 4; do
        orig_time=$(grep "^$pattern," branch_results.csv | cut -d, -f2)
        
        # Use the better of the two optimized approaches
        hint_time=$(grep "^$pattern,hints" arm_optimized_results.csv | cut -d, -f3)
        branchless_time=$(grep "^$pattern,branchless" arm_optimized_results.csv | cut -d, -f3)
        
        if (( $(echo "$hint_time < $branchless_time" | bc -l) )); then
            opt_time=$hint_time
            approach="hints"
        else
            opt_time=$branchless_time
            approach="branchless"
        fi
        
        improvement=$(echo "scale=2; ($orig_time - $opt_time) * 100 / $orig_time" | bc)
        
        echo "$pattern,$orig_time,$opt_time,$improvement" >> comparison_results.csv
        echo "Pattern $pattern: Original: $orig_time s, Optimized ($approach): $opt_time s, Improvement: $improvement%"
    done
fi
#!/bin/bash

# List of all benchmark directories
DIRS=(
    "cache_performance"
    "io_performance"
    "network_performance"
    "system_latency"
    "power_efficiency"
    "floating_point"
    "context_switching"
    "virtualization"
    "page_size_tlb"
    "simd_vector"
    "atomic_operations"
    "instruction_latency"
    "microarchitectural"
    "energy_efficiency"
    "mixed_workload"
    "security_impact"
    "crypto_extensions"
    "memory_tagging"
    "numa_aware"
    "memory_prefetch"
    "cache_management"
    "pointer_authentication"
    "dsp_instructions"
)

# Copy template files to each directory
for dir in "${DIRS[@]}"; do
    echo "Initializing $dir..."
    cp template_setup.sh "$dir/setup.sh"
    chmod +x "$dir/setup.sh"
    
    # Create a README based on the template
    sed "s/Benchmark Name/${dir//_/ }/g" template_README.md > "$dir/README.md"
    
    # Create an empty benchmark script
    cat > "$dir/benchmark.sh" << 'EOF'
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

# Add benchmark-specific code here

EOF
    chmod +x "$dir/benchmark.sh"
done

echo "All directories initialized with template files."
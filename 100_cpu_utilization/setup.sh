#!/bin/bash

# Check if packages are already installed (check in home directory for persistence)
if [ -f "$HOME/.bench_packages_installed" ]; then
    echo "Packages already installed, skipping apt commands"
else
    # Install required packages for CPU utilization benchmarking
    echo "Installing required packages..."
    sudo apt update
    sudo apt install -y sysstat stress-ng
    
    # Create marker file to indicate packages are installed
    touch "$HOME/.bench_packages_installed"
fi

echo "Setup complete. You can now run ./cpu_benchmark.sh"
#!/bin/bash

# Install required packages for CPU utilization benchmarking
echo "Installing required packages..."
sudo apt update
sudo apt install -y sysstat stress-ng

echo "Setup complete. You can now run ./cpu_benchmark.sh"
#!/bin/bash

# Install required packages for benchmarking
echo "Installing required packages..."
sudo apt update
sudo apt install -y build-essential

# Add benchmark-specific installations here

echo "Setup complete. You can now run the benchmarks."
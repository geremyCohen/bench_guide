#!/bin/bash

# Install required packages for branch prediction benchmarking
echo "Installing required packages..."
sudo apt update
sudo apt install -y build-essential linux-tools-common linux-tools-generic

echo "Setup complete. You can now run the branch prediction benchmarks."
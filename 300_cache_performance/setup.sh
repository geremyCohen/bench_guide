#!/bin/bash

# Install required packages for benchmarking
echo "Installing required packages..."
sudo apt update
sudo apt install -y build-essential python3-matplotlib

echo "Setup complete. You can now run the cache performance benchmarks."
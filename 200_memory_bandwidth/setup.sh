#!/bin/bash

# Install required packages for memory bandwidth benchmarking
echo "Installing required packages..."
sudo apt update
sudo apt install -y build-essential git time

# Download STREAM benchmark
echo "Downloading STREAM benchmark..."
git clone https://github.com/jeffhammond/STREAM.git
cd STREAM

# Compile with optimizations
echo "Compiling STREAM benchmark..."
gcc -O3 -fopenmp -DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=10 stream.c -o stream

echo "Setup complete. You can now run the memory bandwidth benchmark."
import matplotlib.pyplot as plt
import numpy as np
import csv
import os

def read_csv(filename):
    sizes = []
    times = []
    
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            sizes.append(int(row[0]))
            times.append(float(row[1]))
    
    return np.array(sizes), np.array(times)

# Plot sequential vs random access
plt.figure(figsize=(10, 6))

if os.path.exists('sequential_access.csv'):
    seq_sizes, seq_times = read_csv('sequential_access.csv')
    plt.plot(seq_sizes, seq_times, 'b-', label='Sequential Access')

if os.path.exists('random_access.csv'):
    rand_sizes, rand_times = read_csv('random_access.csv')
    plt.plot(rand_sizes, rand_times, 'r-', label='Random Access')

plt.xscale('log')
plt.yscale('log')
plt.xlabel('Array Size (bytes)')
plt.ylabel('Access Time (ns)')
plt.title('Cache Performance: Sequential vs Random Access')
plt.legend()
plt.grid(True)
plt.savefig('cache_sequential_vs_random.png')

# Plot strided access
plt.figure(figsize=(10, 6))

strides = [1, 2, 4, 8, 16, 32, 64, 128]
for stride in strides:
    filename = f'strided_access_{stride}.csv'
    if os.path.exists(filename):
        sizes, times = read_csv(filename)
        plt.plot(sizes, times, label=f'Stride {stride}')

plt.xscale('log')
plt.yscale('log')
plt.xlabel('Array Size (bytes)')
plt.ylabel('Access Time (ns)')
plt.title('Cache Performance: Strided Access')
plt.legend()
plt.grid(True)
plt.savefig('cache_strided_access.png')

print("Plots saved as cache_sequential_vs_random.png and cache_strided_access.png")
#!/usr/bin/env python3
"""
Benchmark Visualizer Tool

This tool runs benchmarks on remote VMs and visualizes the results.
"""

import os
import sys
import json
import argparse
import subprocess
import threading
import tempfile
from pathlib import Path
import boto3
import concurrent.futures
from datetime import datetime
from termcolor import colored

# Local imports
from cloud_providers import aws_provider
from parsers import parse_benchmark_output
from visualizers import generate_html_report

# Constants
REPO_URL = "https://github.com/geremyCohen/bench_guide"
RESULTS_DIR = Path(__file__).parent / "results"

# Ensure results directory exists
RESULTS_DIR.mkdir(exist_ok=True)

# Set AWS_DEFAULT_PROFILE to "arm" by default if not already set
if not os.environ.get("AWS_DEFAULT_PROFILE"):
    os.environ["AWS_DEFAULT_PROFILE"] = "arm"
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] Using AWS profile: arm (default)")
else:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] Using AWS profile: {os.environ['AWS_DEFAULT_PROFILE']}")

# Set default SSH key path
DEFAULT_SSH_KEY = os.path.expanduser("~/.ssh/gcohen1.pem")
if os.path.exists(DEFAULT_SSH_KEY):
    # Fix permissions on the key file (SSH requires this)
    try:
        os.chmod(DEFAULT_SSH_KEY, 0o600)  # Set to read/write for owner only
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] Warning: Could not set permissions on key file: {e}")
    
    os.environ["SSH_KEY_PATH"] = DEFAULT_SSH_KEY
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] Using SSH key: {DEFAULT_SSH_KEY}")
else:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] Warning: Default SSH key {DEFAULT_SSH_KEY} not found")

# Define colors for different instances
INSTANCE_COLORS = ['green', 'yellow', 'blue', 'magenta', 'cyan']


def get_timestamp():
    """Get current timestamp in H:M:S.ms format."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def run_ssh_command(instance, command, capture_output=False):
    """Run command on remote instance using system SSH."""
    color_idx = hash(instance['name']) % len(INSTANCE_COLORS)
    color = INSTANCE_COLORS[color_idx]
    prefix = f"[{instance['name']}] "
    
    ssh_cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=accept-new",  # Accept new hosts automatically
        "-o", "ConnectTimeout=10",  # Timeout after 10 seconds
    ]
    
    # Add identity file if specified
    ssh_key = os.environ.get("SSH_KEY_PATH")
    if ssh_key:
        ssh_cmd.extend(["-i", ssh_key])
    
    # Add target and command
    ssh_cmd.extend([
        f"{instance['username']}@{instance['ip']}",
        command
    ])
    
    if capture_output:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    else:
        # Real-time output with colored prefix
        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        def print_output(pipe, is_stderr=False):
            prefix_text = prefix
            if is_stderr:
                prefix_text = f"[{instance['name']}-ERR] "
            for line in pipe:
                if line.strip():
                    timestamp = get_timestamp()
                    print(f"[{timestamp}] " + colored(prefix_text, color) + line.strip())
        
        # Start threads to handle stdout and stderr
        stdout_thread = threading.Thread(target=print_output, args=(process.stdout,))
        stderr_thread = threading.Thread(target=print_output, args=(process.stderr, True))
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for process to complete
        exit_code = process.wait()
        
        # Wait for threads to finish
        stdout_thread.join()
        stderr_thread.join()
        
        return exit_code


def get_benchmarks():
    """Get list of available benchmarks from the repo structure."""
    benchmarks = []
    base_dir = Path(__file__).parent.parent
    
    for item in base_dir.iterdir():
        if item.is_dir() and item.name[0].isdigit() and "_" in item.name:
            # Extract number and name
            parts = item.name.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit():
                number = parts[0]
                name = parts[1]
                benchmarks.append({
                    "number": number,
                    "name": name,
                    "path": item.name
                })
    
    # Sort by benchmark number
    benchmarks.sort(key=lambda x: int(x["number"]))
    return benchmarks


def select_cloud_provider():
    """Select cloud provider (currently only AWS is supported)."""
    timestamp = get_timestamp()
    print(f"[{timestamp}] Select cloud provider:")
    print(f"[{timestamp}] 1. AWS (default)")
    print(f"[{timestamp}] 2. GCP (not yet supported)")
    print(f"[{timestamp}] 3. Azure (not yet supported)")
    
    choice = input(f"[{get_timestamp()}] Enter choice [1]: ").strip() or "1"
    
    if choice == "1":
        return "aws"
    else:
        timestamp = get_timestamp()
        print(f"[{timestamp}] Only AWS is currently supported. Using AWS.")
        return "aws"


def select_benchmarks():
    """Let user select benchmarks to run."""
    benchmarks = get_benchmarks()
    
    timestamp = get_timestamp()
    print(f"\n[{timestamp}] Available benchmarks:")
    for i, benchmark in enumerate(benchmarks, 1):
        print(f"[{get_timestamp()}] {i}. {benchmark['path']} - {benchmark['name']}")
    
    # Find the index of 100_cpu_utilization for default selection
    default_benchmark_idx = 0
    for i, benchmark in enumerate(benchmarks):
        if benchmark['path'] == '100_cpu_utilization':
            default_benchmark_idx = i
            break
    
    timestamp = get_timestamp()
    print(f"\n[{timestamp}] Enter benchmark numbers to run (comma-separated, or 'all') [100_cpu_utilization]:")
    selection = input(f"[{get_timestamp()}] > ").strip()
    
    if selection.lower() == "all":
        return benchmarks
    elif not selection:  # Default to 100_cpu_utilization if no input
        return [benchmarks[default_benchmark_idx]] if default_benchmark_idx < len(benchmarks) else []
    
    selected_indices = [int(idx.strip()) - 1 for idx in selection.split(",") if idx.strip().isdigit()]
    return [benchmarks[idx] for idx in selected_indices if 0 <= idx < len(benchmarks)]


def run_single_benchmark(instance, benchmark, benchmark_output_dir, temp_dir):
    """Run a single benchmark and collect results."""
    benchmark_dir = benchmark["path"]
    color_idx = hash(instance['name']) % len(INSTANCE_COLORS)
    color = INSTANCE_COLORS[color_idx]
    
    # Check which benchmark script exists
    exit_code, stdout, stderr = run_ssh_command(
        instance,
        f"cd ~/benchmarks/{temp_dir}/bench_guide/{benchmark_dir} && ls -la *.sh",
        capture_output=True
    )
    
    if "cpu_benchmark.sh" in stdout:
        benchmark_script = "cpu_benchmark.sh"
    elif "benchmark.sh" in stdout:
        benchmark_script = "benchmark.sh"
    else:
        # Find any .sh file
        benchmark_script = "benchmark.sh"  # Default fallback
        for line in stdout.splitlines():
            if line.endswith(".sh"):
                parts = line.split()
                if len(parts) > 0:
                    benchmark_script = parts[-1]
                    break
    
    # Run benchmark script
    timestamp = get_timestamp()
    print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + f" Running {benchmark_script} in {benchmark_dir}...")
    exit_code, stdout, stderr = run_ssh_command(
        instance,
        f"cd ~/benchmarks/{temp_dir}/bench_guide/{benchmark_dir} && chmod +x {benchmark_script} && ./{benchmark_script}",
        capture_output=True
    )
    if exit_code != 0:
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Benchmark script failed with exit code {exit_code}")
    
    # Save raw output for debugging
    raw_output_path = benchmark_output_dir / f"{instance['name']}__raw_output.txt"
    with open(raw_output_path, 'w') as f:
        f.write(f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")
    timestamp = get_timestamp()
    print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + f" Saved raw output to {raw_output_path}")
    
    # Check for outputs_info.txt
    exit_code, stdout, stderr = run_ssh_command(
        instance,
        f"cat ~/benchmarks/{temp_dir}/bench_guide/{benchmark_dir}/outputs_info.txt 2>/dev/null || echo ''",
        capture_output=True
    )
    
    if stdout.strip():
        output_files = [line.strip() for line in stdout.splitlines() if line.strip()]
    else:
        # Default to common output files if outputs_info.txt doesn't exist
        if benchmark_dir == "100_cpu_utilization":
            output_files = ["cpu_benchmark_results.txt", "mpstat_full_load.txt", "metadata_full_load.txt"]
        else:
            output_files = ["benchmark_results.txt"]
    
    # Download output files
    parsed_data = None
    downloaded_files = []
    
    for output_file in output_files:
        local_path = benchmark_output_dir / f"{instance['name']}__{output_file}"
        
        # Use scp to download the file
        scp_cmd = [
            "scp",
            "-o", "StrictHostKeyChecking=accept-new",
        ]
        
        # Add identity file if specified
        ssh_key = os.environ.get("SSH_KEY_PATH")
        if ssh_key:
            scp_cmd.extend(["-i", ssh_key])
        
        scp_cmd.extend([
            f"{instance['username']}@{instance['ip']}:~/benchmarks/{temp_dir}/bench_guide/{benchmark_dir}/{output_file}",
            str(local_path)
        ])
        
        result = subprocess.run(scp_cmd, capture_output=True)
        
        if result.returncode == 0:
            timestamp = get_timestamp()
            print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + f" Downloaded {output_file}")
            downloaded_files.append(local_path)
        else:
            timestamp = get_timestamp()
            print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Failed to download {output_file}")
    
    # If we have downloaded files, parse them
    if downloaded_files:
        # First, check if we have a manifest file
        manifest_file = None
        metadata_files = []
        result_files = []
        
        for file_path in downloaded_files:
            if "manifest" in str(file_path).lower():
                manifest_file = file_path
            elif "metadata" in str(file_path).lower():
                metadata_files.append(file_path)
            elif "result" in str(file_path).lower() or "output" in str(file_path).lower():
                result_files.append(file_path)
        
        # Initialize parsed data with system info
        parsed_data = {
            "benchmark_type": benchmark_dir,
            "system_info": {},
            "metrics": {},
            "raw_data": {}
        }
        
        # Parse metadata files first
        for file_path in metadata_files:
            try:
                run_data = parse_benchmark_output.parse_file(
                    str(file_path), 
                    benchmark_dir
                )
                if run_data and "metrics" in run_data:
                    # Merge metrics
                    for key, value in run_data["metrics"].items():
                        if key not in parsed_data["metrics"]:
                            parsed_data["metrics"][key] = value
                        elif key == "runs" and isinstance(value, dict):
                            if "runs" not in parsed_data["metrics"]:
                                parsed_data["metrics"]["runs"] = {}
                            parsed_data["metrics"]["runs"].update(value)
                    
                    # Merge system info
                    if "system_info" in run_data:
                        parsed_data["system_info"].update(run_data["system_info"])
            except Exception as e:
                timestamp = get_timestamp()
                print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Failed to parse {file_path}: {e}")
        
        # Parse result files
        for file_path in result_files:
            try:
                run_data = parse_benchmark_output.parse_file(
                    str(file_path), 
                    benchmark_dir
                )
                if run_data and "metrics" in run_data:
                    # Merge metrics
                    for key, value in run_data["metrics"].items():
                        if key not in parsed_data["metrics"]:
                            parsed_data["metrics"][key] = value
                        elif key == "runs" and isinstance(value, dict):
                            if "runs" not in parsed_data["metrics"]:
                                parsed_data["metrics"]["runs"] = {}
                            parsed_data["metrics"]["runs"].update(value)
                    
                    # Merge system info
                    if "system_info" in run_data:
                        parsed_data["system_info"].update(run_data["system_info"])
            except Exception as e:
                timestamp = get_timestamp()
                print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Failed to parse {file_path}: {e}")
    
    # If no files were downloaded or parsing failed, use the raw output
    if not parsed_data:
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " Using raw output for benchmark results")
        try:
            parsed_data = parse_benchmark_output.parse_file(
                str(raw_output_path),
                benchmark_dir
            )
        except Exception as e:
            timestamp = get_timestamp()
            print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Failed to parse raw output: {e}")
    
    # Add system information to the parsed data
    if parsed_data and 'system_info' in instance and instance['system_info']:
        parsed_data["system_info"].update(instance['system_info'])
    
    return parsed_data


def run_benchmark(instance, benchmark, instance_dir, temp_dir):
    """Run a single benchmark on an instance."""
    benchmark_dir = benchmark["path"]
    color_idx = hash(instance['name']) % len(INSTANCE_COLORS)
    color = INSTANCE_COLORS[color_idx]
    
    try:
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + f" Running {benchmark_dir}...")
        
        # Run setup script
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + f" Running setup script for {benchmark_dir}...")
        exit_code = run_ssh_command(
            instance,
            f"cd ~/benchmarks/{temp_dir}/bench_guide/{benchmark_dir} && chmod +x setup.sh && ./setup.sh"
        )
        if exit_code != 0:
            timestamp = get_timestamp()
            print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Setup script failed with exit code {exit_code}")
        
        # Create benchmark directory
        benchmark_output_dir = instance_dir / benchmark_dir
        benchmark_output_dir.mkdir(exist_ok=True)
        
        return run_single_benchmark(instance, benchmark, benchmark_output_dir, temp_dir)
    
    except Exception as e:
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Error running {benchmark_dir}: {str(e)}")
        return None


def collect_system_info(instance):
    """Collect system information from an instance."""
    system_info = {}
    color_idx = hash(instance['name']) % len(INSTANCE_COLORS)
    color = INSTANCE_COLORS[color_idx]
    
    # Get architecture
    timestamp = get_timestamp()
    print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " Getting architecture...")
    exit_code, stdout, stderr = run_ssh_command(
        instance,
        "uname -m",
        capture_output=True
    )
    if exit_code == 0 and stdout.strip():
        arch = stdout.strip()
        if "aarch64" in arch or "arm64" in arch:
            system_info["architecture"] = "ARM64"
        elif "x86_64" in arch:
            system_info["architecture"] = "x86_64"
        else:
            system_info["architecture"] = arch
    
    # Get CPU model
    timestamp = get_timestamp()
    print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " Getting CPU model...")
    exit_code, stdout, stderr = run_ssh_command(
        instance,
        "cat /proc/cpuinfo | grep 'model name' | head -1 || lscpu | grep 'Model name'",
        capture_output=True
    )
    if exit_code == 0 and stdout.strip():
        for line in stdout.splitlines():
            if ':' in line:
                cpu_model = line.split(':', 1)[1].strip()
                system_info["cpu_model"] = cpu_model
                break
    
    # Get CPU cores
    timestamp = get_timestamp()
    print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " Getting CPU cores...")
    exit_code, stdout, stderr = run_ssh_command(
        instance,
        "nproc",
        capture_output=True
    )
    if exit_code == 0 and stdout.strip():
        try:
            system_info["cpu_cores"] = int(stdout.strip())
        except ValueError:
            pass
    
    return system_info


def run_benchmarks_on_instance(instance, benchmarks, run_dir):
    """Run benchmarks on a single instance."""
    instance_results = {}
    instance_dir = run_dir / instance["name"]
    instance_dir.mkdir(exist_ok=True)
    color_idx = hash(instance['name']) % len(INSTANCE_COLORS)
    color = INSTANCE_COLORS[color_idx]
    
    try:
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + f" Connecting to {instance['ip']}...")
        
        # Test SSH connection
        exit_code = run_ssh_command(instance, "echo 'SSH connection successful'")
        if exit_code != 0:
            raise Exception("Failed to establish SSH connection")
            
        # Collect system information
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " Collecting system information...")
        instance['system_info'] = collect_system_info(instance)
        
        # Install required packages
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " Installing required packages...")
        exit_code = run_ssh_command(
            instance,
            "sudo apt-get update -y && sudo apt-get install git build-essential -y"
        )
        if exit_code != 0:
            timestamp = get_timestamp()
            print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Package installation failed with exit code {exit_code}")
        
        # Create a unique temporary directory
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = f"bench_{timestamp_str}_{os.getpid()}"
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + f" Creating temporary directory {unique_id}...")
        exit_code, stdout, stderr = run_ssh_command(
            instance,
            f"mkdir -p ~/benchmarks/{unique_id}",
            capture_output=True
        )
        if exit_code != 0:
            raise Exception(f"Failed to create temporary directory: {stderr.strip()}")
        
        # Clone repo into the temporary directory
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " Cloning repository...")
        exit_code = run_ssh_command(
            instance,
            f"cd ~/benchmarks/{unique_id} && git clone {REPO_URL}"
        )
        if exit_code != 0:
            raise Exception(f"Failed to clone repository with exit code {exit_code}")
        
        # Run benchmarks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(benchmarks)) as executor:
            future_to_benchmark = {
                executor.submit(run_benchmark, instance, benchmark, instance_dir, unique_id): benchmark
                for benchmark in benchmarks
            }
            
            for future in concurrent.futures.as_completed(future_to_benchmark):
                benchmark = future_to_benchmark[future]
                try:
                    benchmark_result = future.result()
                    if benchmark_result:
                        instance_results[benchmark["path"]] = benchmark_result
                except Exception as e:
                    timestamp = get_timestamp()
                    print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" Error running benchmark {benchmark['path']}: {e}")
        
        # Clean up temporary directory
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " Cleaning up temporary directory...")
        run_ssh_command(
            instance,
            f"rm -rf ~/benchmarks/{unique_id}"
        )
        
        return instance_results
        
    except Exception as e:
        timestamp = get_timestamp()
        print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" {str(e)}")
        raise


def run_benchmarks_on_instances(provider, instances, selected_benchmarks):
    """Run selected benchmarks on all target instances."""
    results = {}
    
    # Create timestamp for this run
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RESULTS_DIR / timestamp_str
    run_dir.mkdir(exist_ok=True)
    
    timestamp = get_timestamp()
    print(f"\n[{timestamp}] Running benchmarks on {len(instances)} instances...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(instances)) as executor:
        future_to_instance = {
            executor.submit(
                run_benchmarks_on_instance, 
                instance, 
                selected_benchmarks,
                run_dir
            ): instance for instance in instances
        }
        
        for future in concurrent.futures.as_completed(future_to_instance):
            instance = future_to_instance[future]
            try:
                instance_results = future.result()
                results[instance["name"]] = instance_results
                color_idx = hash(instance['name']) % len(INSTANCE_COLORS)
                color = INSTANCE_COLORS[color_idx]
                timestamp = get_timestamp()
                print(f"[{timestamp}] " + colored(f"[{instance['name']}]", color) + " ✓ Completed benchmarks")
            except Exception as e:
                color_idx = hash(instance['name']) % len(INSTANCE_COLORS)
                color = INSTANCE_COLORS[color_idx]
                timestamp = get_timestamp()
                print(f"[{timestamp}] " + colored(f"[{instance['name']}-ERR]", color) + f" ✗ Error running benchmarks: {e}")
    
    return results, run_dir


def main():
    """Main function."""
    timestamp = get_timestamp()
    print(f"[{timestamp}] Benchmark Visualization Tool")
    print(f"[{timestamp}] ===========================\n")
    
    # Select cloud provider
    provider_name = select_cloud_provider()
    
    # Get provider module
    if provider_name == "aws":
        provider = aws_provider
    else:
        timestamp = get_timestamp()
        print(f"[{timestamp}] Provider {provider_name} not supported")
        sys.exit(1)
    
    # Get instances
    timestamp = get_timestamp()
    print(f"\n[{timestamp}] Fetching available instances...")
    instances = provider.get_instances()
    
    if not instances:
        timestamp = get_timestamp()
        print(f"[{timestamp}] No instances found. Please ensure you have proper credentials configured.")
        sys.exit(1)
    
    # Sort instances by launch time (newest first)
    instances.sort(key=lambda x: x.get('launch_time', ''), reverse=True)
    
    timestamp = get_timestamp()
    print(f"[{timestamp}] Found {len(instances)} instances:")
    for i, instance in enumerate(instances, 1):
        timestamp = get_timestamp()
        print(f"[{timestamp}] {i}. {instance['name']} ({instance['ip']})")
    
    # Select instances
    timestamp = get_timestamp()
    print(f"\n[{timestamp}] Enter instance numbers to use (comma-separated, or 'all') [1,2]:")
    selection = input(f"[{get_timestamp()}] > ").strip()
    
    if selection.lower() == "all":
        selected_instances = instances
    elif not selection:  # Default to first two instances if no input
        default_indices = [0, 1]  # 0-based indices for instances 1 and 2
        selected_instances = [instances[idx] for idx in default_indices if 0 <= idx < len(instances)]
    else:
        selected_indices = [int(idx.strip()) - 1 for idx in selection.split(",") if idx.strip().isdigit()]
        selected_instances = [instances[idx] for idx in selected_indices if 0 <= idx < len(instances)]
    
    if not selected_instances:
        timestamp = get_timestamp()
        print(f"[{timestamp}] No instances selected. Exiting.")
        sys.exit(1)
    
    # Select benchmarks
    selected_benchmarks = select_benchmarks()
    
    if not selected_benchmarks:
        timestamp = get_timestamp()
        print(f"[{timestamp}] No benchmarks selected. Exiting.")
        sys.exit(1)
    
    # Run benchmarks
    results, run_dir = run_benchmarks_on_instances(provider, selected_instances, selected_benchmarks)
    
    # Generate report
    timestamp = get_timestamp()
    print(f"[{timestamp}] Generating report...")
    report_path = generate_html_report.create_report(results, run_dir)
    
    timestamp = get_timestamp()
    print(f"\n[{timestamp}] Benchmark complete! Report available at: {report_path}")


if __name__ == "__main__":
    main()
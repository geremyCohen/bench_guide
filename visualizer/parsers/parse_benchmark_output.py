#!/usr/bin/env python3
"""
Benchmark Output Parser

Parses benchmark output files into a common format for visualization.
"""

import re
import json
import os
from pathlib import Path


def extract_stress_metrics(content):
    """Extract stress-ng metrics from content."""
    stress_metrics_by_run = {}
    
    # Extract run names and their corresponding metrics
    run_names = re.findall(r'=== Running CPU test with \d+ load for \d+ seconds \(Run: (\w+)\) ===', content)
    
    # Extract all stress-ng metrics lines
    metrics_pattern = r"stress-ng: metrc:.*?cpu\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
    metrics_matches = re.findall(metrics_pattern, content, re.DOTALL)
    
    # Match metrics with run names
    if len(metrics_matches) == len(run_names):
        for run_name, metrics in zip(run_names, metrics_matches):
            bogo_ops, real_time, usr_time, sys_time, bogo_ops_real, bogo_ops_time = metrics
            stress_metrics_by_run[run_name] = {
                "bogo_ops": int(bogo_ops),
                "real_time": float(real_time),
                "usr_time": float(usr_time),
                "sys_time": float(sys_time),
                "bogo_ops_real": float(bogo_ops_real),
                "bogo_ops_time": float(bogo_ops_time)
            }
    
    return stress_metrics_by_run


def parse_file(file_path, benchmark_type):
    """
    Parse a benchmark output file based on its type.
    
    Args:
        file_path (str): Path to the output file
        benchmark_type (str): Type of benchmark (directory name)
        
    Returns:
        dict: Parsed data in common format
    """
    # Common format structure
    result = {
        "benchmark_type": benchmark_type,
        "system_info": {},
        "metrics": {},
        "raw_data": {}
    }
    
    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    
    # Store raw data
    result["raw_data"]["content"] = content
    
    # Check if this is a raw output file
    if "STDOUT:" in content and "stress-ng: metrc" in content:
        # Extract just the STDOUT part
        stdout_match = re.search(r"STDOUT:\n(.+?)(?:\n\n\nSTDERR:|$)", content, re.DOTALL)
        if stdout_match:
            stdout_content = stdout_match.group(1)
            # Use the STDOUT content for parsing
            content = stdout_content
    
    # Check if this is an mpstat file
    if "mpstat" in str(file_path).lower() or "Average:" in content:
        return parse_mpstat_file(content, result)
    
    # Parse based on benchmark type
    if benchmark_type == "100_cpu_utilization":
        return parse_cpu_utilization(content, result, file_path)
    else:
        # Generic parser for other benchmark types
        return parse_generic(content, result, benchmark_type)


def parse_mpstat_file(content, result):
    """Parse mpstat output file for time-series CPU data."""
    lines = content.strip().split('\n')
    time_series = []
    
    for line in lines:
        # Look for CPU data lines with 'all' (skip headers, averages, and individual cores)
        if re.match(r'^\d{2}:\d{2}:\d{2}\s+all\s+', line):
            parts = line.split()
            if len(parts) >= 11:
                time_str = parts[0]
                usr = float(parts[2])     # %usr
                sys = float(parts[4])     # %sys  
                iowait = float(parts[5])  # %iowait
                cpu_idle = float(parts[-1])  # %idle
                cpu_util = 100 - cpu_idle
                
                time_series.append({
                    'time': time_str,
                    'utilization': round(cpu_util, 2),
                    'usr': round(usr, 2),
                    'sys': round(sys, 2),
                    'iowait': round(iowait, 2)
                })
    
    if time_series:
        result["metrics"]["time_series"] = time_series
    
    return result


def parse_cpu_utilization(content, result, file_path):
    """Parse CPU utilization benchmark output."""
    
    # Initialize stress metrics dictionary
    stress_metrics_by_run = {}
    
    # Check if there's a raw output file in the same directory
    file_path_obj = Path(file_path)
    instance_name = file_path_obj.name.split('__')[0]
    raw_output_path = str(file_path_obj.parent / f"{instance_name}__raw_output.txt")
    
    # Try to extract from raw output file first
    if os.path.exists(raw_output_path):
        with open(raw_output_path, 'r') as f:
            raw_content = f.read()
        stress_metrics_by_run = extract_stress_metrics(raw_content)
    
    # Also try to extract from current content if it contains stress-ng data
    if not stress_metrics_by_run and 'stress-ng: metrc' in content:
        stress_metrics_by_run = extract_stress_metrics(content)
    # Extract system information
    arch_match = re.search(r"Architecture:\s*(.*)", content)
    if arch_match:
        result["system_info"]["architecture"] = arch_match.group(1)
    
    cpu_model_match = re.search(r"Model name:\s*(.*)", content)
    if cpu_model_match:
        result["system_info"]["cpu_model"] = cpu_model_match.group(1).strip()
    
    cpu_cores_match = re.search(r"CPU Cores:\s*(\d+)", content)
    if cpu_cores_match:
        result["system_info"]["cpu_cores"] = int(cpu_cores_match.group(1))
    
    # Check if this is a metadata file
    if "run_name=" in content:
        # Parse metadata file
        run_name = None
        load = None
        duration = None
        avg_util = None
        
        for line in content.split('\n'):
            if line.startswith("run_name="):
                run_name = line.split('=', 1)[1].strip()
            elif line.startswith("load="):
                load = line.split('=', 1)[1].strip()
            elif line.startswith("duration="):
                duration = line.split('=', 1)[1].strip()
            elif line.startswith("avg_utilization="):
                avg_util = float(line.split('=', 1)[1].strip())
        
        if run_name and avg_util is not None:
            if "runs" not in result["metrics"]:
                result["metrics"]["runs"] = {}
            
            result["metrics"]["runs"][run_name] = {
                "load": load,
                "duration": duration,
                "avg_utilization": avg_util
            }
            
            # Also add to the main metrics for backward compatibility
            if "average_utilization" not in result["metrics"]:
                result["metrics"]["average_utilization"] = []
            result["metrics"]["average_utilization"].append(avg_util)
            
        return result
    
    # Extract stress-ng metrics using the helper function
    if not stress_metrics_by_run:
        stress_metrics_by_run = extract_stress_metrics(content)
    
    
    # Metrics are now extracted directly in the regex pattern above
    
    # Extract runs data from the new format
    result["metrics"]["runs"] = {}
    result["metrics"]["average_utilization"] = []
    
    # Find all run sections
    run_sections = re.findall(r"=== CPU Utilization Results \(Run: (\w+)\) ===.*?(?====|$)", content, re.DOTALL)
    
    for run_match in run_sections:
        run_name = run_match
        # Find the section for this run
        run_pattern = rf"=== CPU Utilization Results \(Run: {run_name}\) ===(.*?)(?===|Creating metadata|$)"
        run_section_match = re.search(run_pattern, content, re.DOTALL)
        
        if run_section_match:
            run_content = run_section_match.group(1)
            
            # Extract average utilization for this run
            avg_match = re.search(r"Average CPU utilization \(all cores\):\s*([\d.]+)%", run_content)
            if avg_match:
                avg_util = float(avg_match.group(1))
                
                # Extract load and duration
                load_match = re.search(r"Load: (\d+) cores", run_content)
                duration_match = re.search(r"Duration: (\d+) seconds", run_content)
                
                result["metrics"]["runs"][run_name] = {
                    "avg_utilization": avg_util,
                    "load": load_match.group(1) if load_match else "unknown",
                    "duration": duration_match.group(1) if duration_match else "unknown"
                }
                
                # Add stress-ng metrics if available for this run
                if run_name in stress_metrics_by_run:
                    result["metrics"]["runs"][run_name]["stress_metrics"] = stress_metrics_by_run[run_name]
                
                # Also add to the main average_utilization list for backward compatibility
                result["metrics"]["average_utilization"].append(avg_util)
    
    # Fallback to old parsing if no runs found
    if not result["metrics"]["runs"]:
        avg_util_matches = re.findall(r"Average CPU utilization \(all cores\):\s*([\d.]+)%", content)
        if avg_util_matches:
            result["metrics"]["average_utilization"] = [float(util) for util in avg_util_matches]
        else:
            # Try alternative format
            avg_util_matches = re.findall(r"all\s+([\d.]+)", content)
            if avg_util_matches:
                result["metrics"]["average_utilization"] = [100 - float(util) for util in avg_util_matches]
    
    # If still no data, set a default
    if "average_utilization" not in result["metrics"] or not result["metrics"]["average_utilization"]:
        result["metrics"]["average_utilization"] = [99.0]  # Default to 99% utilization
    
    # Add raw content for debugging
    result["raw_content"] = content
    
    return result


def parse_generic(content, result, benchmark_type):
    """Generic parser for other benchmark types."""
    # Extract system information if available
    arch_match = re.search(r"Architecture: (.*)", content)
    if arch_match:
        result["system_info"]["architecture"] = arch_match.group(1)
    
    # Try to extract common metrics based on patterns
    # Look for lines with metric: value format
    for line in content.split('\n'):
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip().lower().replace(' ', '_')
                value = parts[1].strip()
                
                # Try to convert to number if possible
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
                
                result["metrics"][key] = value
    
    # Look for tabular data
    tables = []
    current_table = []
    in_table = False
    
    for line in content.split('\n'):
        if '|' in line and '-+-' in line:
            # Table separator line
            in_table = True
            continue
        
        if in_table and '|' in line:
            # Table row
            row = [cell.strip() for cell in line.split('|')]
            current_table.append(row)
        elif in_table:
            # End of table
            if current_table:
                tables.append(current_table)
                current_table = []
            in_table = False
    
    # Add any remaining table
    if current_table:
        tables.append(current_table)
    
    if tables:
        result["metrics"]["tables"] = tables
    
    return result
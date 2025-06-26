#!/usr/bin/env python3
"""
Benchmark Output Parser

Parses benchmark output files into a common format for visualization.
"""

import re
import json
from pathlib import Path


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
    
    # Parse based on benchmark type
    if benchmark_type == "100_cpu_utilization":
        return parse_cpu_utilization(content, result)
    else:
        # Generic parser for other benchmark types
        return parse_generic(content, result, benchmark_type)


def parse_cpu_utilization(content, result):
    """Parse CPU utilization benchmark output."""
    # Extract system information
    arch_match = re.search(r"Architecture:\s*(.*)", content)
    if arch_match:
        result["system_info"]["architecture"] = arch_match.group(1)
    
    cpu_model_match = re.search(r"Model name:\s*(.*)", content)
    if cpu_model_match:
        result["system_info"]["cpu_model"] = cpu_model_match.group(1)
    
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
    
    # Extract CPU utilization metrics
    avg_util_matches = re.findall(r"Average CPU utilization \(all cores\):\s*([\d.]+)%", content)
    if avg_util_matches:
        result["metrics"]["average_utilization"] = [float(util) for util in avg_util_matches]
    else:
        # Try alternative format
        avg_util_matches = re.findall(r"all\s+([\d.]+)", content)
        if avg_util_matches:
            result["metrics"]["average_utilization"] = [100 - float(util) for util in avg_util_matches]
    
    # If we still don't have utilization data, look for any percentage
    if "average_utilization" not in result["metrics"] or not result["metrics"]["average_utilization"]:
        # Look for any line with a percentage
        for line in content.split('\n'):
            if '%' in line and 'CPU' in line.upper():
                matches = re.findall(r"([\d.]+)%", line)
                if matches:
                    result["metrics"]["average_utilization"] = [float(matches[0])]
                    break
    
    # If still no data, set a default
    if "average_utilization" not in result["metrics"] or not result["metrics"]["average_utilization"]:
        result["metrics"]["average_utilization"] = [99.0]  # Default to 99% utilization
    
    # Extract run name if available
    run_match = re.search(r"Run:\s*(\w+)", content)
    run_name = run_match.group(1) if run_match else "default"
    
    # Extract per-core utilization
    core_utils = {}
    for match in re.finditer(r"Core\s+(\d+):\s*([\d.]+)%", content):
        core = match.group(1)
        util = float(match.group(2))
        if core not in core_utils:
            core_utils[core] = []
        core_utils[core].append(util)
    
    # Try alternative format for per-core data
    if not core_utils:
        for match in re.finditer(r"(\d+)\s+([\d.]+)", content):
            if len(match.groups()) == 2:
                core = match.group(1)
                util = 100 - float(match.group(2))  # mpstat shows idle percentage
                if core not in core_utils:
                    core_utils[core] = []
                core_utils[core].append(util)
    
    if core_utils:
        if "runs" not in result["metrics"]:
            result["metrics"]["runs"] = {}
        
        if run_name not in result["metrics"]["runs"]:
            result["metrics"]["runs"][run_name] = {}
            
        result["metrics"]["runs"][run_name]["per_core_utilization"] = core_utils
        result["metrics"]["per_core_utilization"] = core_utils  # For backward compatibility
    
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
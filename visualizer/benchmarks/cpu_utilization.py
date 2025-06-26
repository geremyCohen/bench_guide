#!/usr/bin/env python3
"""CPU utilization benchmark implementation."""

import asyncio
from pathlib import Path
from typing import Dict, Any
from .base import Benchmark


class CPUUtilizationBenchmark(Benchmark):
    """CPU utilization benchmark implementation."""
    
    def __init__(self):
        super().__init__("CPU Utilization", "100_cpu_utilization")
    
    async def run(self, ssh_client, temp_dir: str, output_dir: Path) -> Dict[str, Any]:
        """Run CPU utilization benchmark."""
        # Get available scripts
        exit_code, stdout, stderr = ssh_client.run_command(
            f"cd ~/benchmarks/{temp_dir}/bench_guide/{self.path} && ls -la *.sh",
            capture_output=True
        )
        
        script_name = self.get_script_name(stdout.splitlines())
        
        # Run benchmark
        exit_code, stdout, stderr = ssh_client.run_command(
            f"cd ~/benchmarks/{temp_dir}/bench_guide/{self.path} && chmod +x {script_name} && ./{script_name}",
            capture_output=True
        )
        
        # Save raw output
        raw_output_path = output_dir / f"{ssh_client.instance['name']}__raw_output.txt"
        with open(raw_output_path, 'w') as f:
            f.write(f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")
        
        # Collect result files
        await self._collect_result_files(ssh_client, temp_dir, output_dir)
        
        return {"exit_code": exit_code, "raw_output_path": str(raw_output_path)}
    
    def get_script_name(self, available_scripts: list) -> str:
        """Determine which script to run."""
        for line in available_scripts:
            if "cpu_benchmark.sh" in line:
                return "cpu_benchmark.sh"
            elif "benchmark.sh" in line:
                return "benchmark.sh"
        return "benchmark.sh"  # fallback
    
    async def _collect_result_files(self, ssh_client, temp_dir: str, output_dir: Path):
        """Collect all result files from remote instance."""
        # Get list of output files
        exit_code, stdout, stderr = ssh_client.run_command(
            f"cd ~/benchmarks/{temp_dir}/bench_guide/{self.path} && ls -1 *.txt 2>/dev/null || true",
            capture_output=True
        )
        
        if stdout.strip():
            files = stdout.strip().split('\n')
            for file in files:
                if file.strip():
                    # Download each file
                    exit_code, content, stderr = ssh_client.run_command(
                        f"cat ~/benchmarks/{temp_dir}/bench_guide/{self.path}/{file.strip()}",
                        capture_output=True
                    )
                    
                    if exit_code == 0 and content:
                        local_path = output_dir / f"{ssh_client.instance['name']}__{file.strip()}"
                        with open(local_path, 'w') as f:
                            f.write(content)
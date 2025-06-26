#!/usr/bin/env python3
"""Main orchestrator for benchmark execution with error handling and async processing."""

import asyncio
import webbrowser
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .config import Config
from .session import BenchmarkSession
from benchmarks.cpu_utilization import CPUUtilizationBenchmark
from parsers import parse_benchmark_output
from visualizers import generate_html_report
from utils.data_processing import DataProcessor


class BenchmarkOrchestrator:
    """Orchestrates benchmark execution with proper error handling."""
    
    def __init__(self, config: Config):
        self.config = config
        self.benchmarks = {
            "100_cpu_utilization": CPUUtilizationBenchmark()
        }
        self.data_processor = DataProcessor()
    
    async def run_benchmarks(self, instances: List[Dict[str, Any]], 
                           benchmark_names: List[str]) -> str:
        """Run benchmarks on instances with proper error handling."""
        async with BenchmarkSession(self.config) as session:
            run_dir = session.create_run_directory()
            
            # Setup remote environment
            temp_dir = await self._setup_remote_environment(session, instances)
            
            # Run benchmarks in parallel with error handling
            results = await self._run_benchmarks_parallel(
                session, instances, benchmark_names, run_dir, temp_dir
            )
            
            # Generate report
            report_path = self._generate_report(results, run_dir)
            
            return report_path
    
    async def reprocess_results(self, results_dir: Path) -> str:
        """Reprocess existing results and regenerate report."""
        results = self._parse_existing_results(results_dir)
        report_path = self._generate_report(results, results_dir)
        return report_path
    
    async def _setup_remote_environment(self, session: BenchmarkSession, 
                                      instances: List[Dict[str, Any]]) -> str:
        """Setup benchmark environment on remote instances."""
        temp_dir = f"bench_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        setup_tasks = []
        for instance in instances:
            ssh_client = session.get_ssh_client(instance)
            task = self._setup_single_instance(ssh_client, temp_dir)
            setup_tasks.append(task)
        
        await asyncio.gather(*setup_tasks, return_exceptions=True)
        return temp_dir
    
    async def _setup_single_instance(self, ssh_client, temp_dir: str):
        """Setup benchmark environment on single instance."""
        commands = [
            f"mkdir -p ~/benchmarks/{temp_dir}",
            f"cd ~/benchmarks/{temp_dir} && git clone {self.config.benchmark.repo_url}",
        ]
        
        for cmd in commands:
            ssh_client.run_command(cmd, capture_output=True)
    
    async def _run_benchmarks_parallel(self, session: BenchmarkSession,
                                     instances: List[Dict[str, Any]],
                                     benchmark_names: List[str],
                                     run_dir: Path, temp_dir: str) -> Dict[str, Any]:
        """Run benchmarks in parallel with error handling."""
        semaphore = asyncio.Semaphore(3)  # Limit concurrent executions
        tasks = []
        
        for instance in instances:
            for benchmark_name in benchmark_names:
                task = self._run_single_benchmark_with_semaphore(
                    semaphore, session, instance, benchmark_name, run_dir, temp_dir
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._process_results(results, instances, benchmark_names)
    
    async def _run_single_benchmark_with_semaphore(self, semaphore: asyncio.Semaphore,
                                                 session: BenchmarkSession,
                                                 instance: Dict[str, Any],
                                                 benchmark_name: str,
                                                 run_dir: Path, temp_dir: str):
        """Run single benchmark with concurrency control."""
        async with semaphore:
            try:
                return await self._run_single_benchmark(
                    session, instance, benchmark_name, run_dir, temp_dir
                )
            except Exception as e:
                return {"error": str(e), "instance": instance['name'], "benchmark": benchmark_name}
    
    async def _run_single_benchmark(self, session: BenchmarkSession,
                                  instance: Dict[str, Any], benchmark_name: str,
                                  run_dir: Path, temp_dir: str):
        """Run single benchmark on instance."""
        ssh_client = session.get_ssh_client(instance)
        benchmark = self.benchmarks[benchmark_name]
        
        # Create output directory
        output_dir = run_dir / instance['name'] / benchmark_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run benchmark
        result = await benchmark.run(ssh_client, temp_dir, output_dir)
        
        return {
            "instance": instance['name'],
            "benchmark": benchmark_name,
            "result": result,
            "output_dir": output_dir
        }
    
    def _process_results(self, raw_results: List[Any], instances: List[Dict[str, Any]],
                        benchmark_names: List[str]) -> Dict[str, Any]:
        """Process raw results and handle errors."""
        processed = {}
        
        for result in raw_results:
            if isinstance(result, Exception):
                print(f"Error in benchmark execution: {result}")
                continue
            
            if "error" in result:
                print(f"Benchmark error: {result}")
                continue
            
            instance_name = result["instance"]
            benchmark_name = result["benchmark"]
            
            if instance_name not in processed:
                processed[instance_name] = {}
            
            processed[instance_name][benchmark_name] = result
        
        return processed
    
    def _parse_existing_results(self, results_dir: Path) -> Dict[str, Any]:
        """Parse existing result files using optimized data processor."""
        # Use optimized data processor for better performance
        processed_results = self.data_processor.process_directory(results_dir)
        
        # Convert to expected format and fallback to original parser if needed
        results = {}
        
        for instance_dir in results_dir.iterdir():
            if not instance_dir.is_dir() or instance_dir.name == "report.html":
                continue
            
            instance_name = instance_dir.name
            results[instance_name] = {}
            
            for benchmark_dir in instance_dir.iterdir():
                if not benchmark_dir.is_dir():
                    continue
                
                benchmark_name = benchmark_dir.name
                benchmark_results = {}
                
                for file_path in benchmark_dir.iterdir():
                    if file_path.is_file():
                        parsed = parse_benchmark_output.parse_file(str(file_path), benchmark_name)
                        if parsed:
                            # Merge parsed results
                            for key, value in parsed.items():
                                if key in benchmark_results:
                                    if isinstance(benchmark_results[key], dict) and isinstance(value, dict):
                                        benchmark_results[key].update(value)
                                else:
                                    benchmark_results[key] = value
                
                results[instance_name][benchmark_name] = benchmark_results
        
        return results
    
    def _generate_report(self, results: Dict[str, Any], run_dir: Path) -> str:
        """Generate HTML report from results."""
        report_path = generate_html_report.create_report(results, run_dir)
        return report_path
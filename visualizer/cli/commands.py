#!/usr/bin/env python3
"""CLI commands for the benchmark visualizer."""

import asyncio
import argparse
import webbrowser
from pathlib import Path
from typing import List, Dict, Any

from core.config import Config
from core.orchestrator import BenchmarkOrchestrator
from cloud.aws import AWSProvider


class CLI:
    """Command line interface for benchmark visualizer."""
    
    def __init__(self):
        self.config = Config.load()
        self.config.setup_environment()
        self.orchestrator = BenchmarkOrchestrator(self.config)
        self.cloud_provider = AWSProvider()
    
    def run(self):
        """Main CLI entry point."""
        parser = self._create_parser()
        args = parser.parse_args()
        
        if args.reprocess:
            asyncio.run(self._reprocess_command(args.reprocess))
        else:
            asyncio.run(self._run_benchmarks_command())
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(description="Benchmark Visualizer Tool")
        parser.add_argument(
            "--reprocess",
            type=str,
            help="Reprocess existing results directory"
        )
        return parser
    
    async def _reprocess_command(self, results_dir: str):
        """Handle reprocess command."""
        results_path = Path(results_dir)
        if not results_path.is_absolute():
            results_path = Path.cwd() / results_path
        
        if not results_path.exists():
            print(f"Results directory not found: {results_path}")
            return
        
        print("Reprocessing results...")
        report_path = await self.orchestrator.reprocess_results(results_path)
        print(f"Report regenerated: {report_path}")
        webbrowser.open(f"file://{report_path}")
    
    async def _run_benchmarks_command(self):
        """Handle run benchmarks command."""
        print("Benchmark Visualization Tool")
        print("===========================\n")
        
        # Get instances
        instances = self._get_instances()
        if not instances:
            print("No instances available.")
            return
        
        # Select benchmarks
        benchmarks = self._select_benchmarks()
        if not benchmarks:
            print("No benchmarks selected.")
            return
        
        benchmark_names = [b["path"] for b in benchmarks]
        
        # Run benchmarks
        print("Running benchmarks...")
        report_path = await self.orchestrator.run_benchmarks(instances, benchmark_names)
        
        print(f"Report generated: {report_path}")
        webbrowser.open(f"file://{report_path}")
    
    def _get_instances(self) -> List[Dict[str, Any]]:
        """Get available instances."""
        try:
            return self.cloud_provider.get_instances()
        except Exception as e:
            print(f"Error getting instances: {e}")
            return []
    
    def _select_benchmarks(self) -> List[Dict[str, Any]]:
        """Interactive benchmark selection."""
        benchmarks = self._get_available_benchmarks()
        
        print("Available benchmarks:")
        for i, benchmark in enumerate(benchmarks, 1):
            print(f"{i}. {benchmark['path']} - {benchmark['name']}")
        
        selection = input(f"Enter benchmark numbers (comma-separated) or 'all' [1]: ").strip()
        
        if selection.lower() == "all":
            return benchmarks
        elif not selection:
            return [benchmarks[0]] if benchmarks else []
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            return [benchmarks[i] for i in indices if 0 <= i < len(benchmarks)]
        except (ValueError, IndexError):
            print("Invalid selection, using default.")
            return [benchmarks[0]] if benchmarks else []
    
    def _get_available_benchmarks(self) -> List[Dict[str, Any]]:
        """Get list of available benchmarks."""
        benchmarks = []
        base_dir = Path(__file__).parent.parent.parent.parent
        
        for item in base_dir.iterdir():
            if item.is_dir() and item.name[0].isdigit() and "_" in item.name:
                parts = item.name.split("_", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    benchmarks.append({
                        "number": parts[0],
                        "name": parts[1],
                        "path": item.name
                    })
        
        benchmarks.sort(key=lambda x: int(x["number"]))
        return benchmarks
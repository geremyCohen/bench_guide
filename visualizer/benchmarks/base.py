#!/usr/bin/env python3
"""Base benchmark interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class Benchmark(ABC):
    """Abstract base class for benchmarks."""
    
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
    
    @abstractmethod
    async def run(self, ssh_client, temp_dir: str, output_dir: Path) -> Dict[str, Any]:
        """Run the benchmark and return results."""
        pass
    
    @abstractmethod
    def get_script_name(self, available_scripts: list) -> str:
        """Determine which script to run based on available scripts."""
        pass
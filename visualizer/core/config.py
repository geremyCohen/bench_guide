#!/usr/bin/env python3
"""Configuration management for the benchmark visualizer."""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class CloudConfig:
    default_profile: str = "arm"
    ssh_key_path: str = "~/.ssh/gcohen1.pem"
    timeout: int = 300


@dataclass
class BenchmarkConfig:
    repo_url: str = "https://github.com/geremyCohen/bench_guide"
    default_benchmark: str = "100_cpu_utilization"


@dataclass
class Config:
    cloud: CloudConfig
    benchmark: BenchmarkConfig
    results_dir: Path
    colors: List[str]

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration with defaults."""
        results_dir = Path(__file__).parent.parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        return cls(
            cloud=CloudConfig(),
            benchmark=BenchmarkConfig(),
            results_dir=results_dir,
            colors=['green', 'yellow', 'blue', 'magenta', 'cyan']
        )

    def setup_environment(self):
        """Setup environment variables and SSH key permissions."""
        # Set AWS profile
        if not os.environ.get("AWS_DEFAULT_PROFILE"):
            os.environ["AWS_DEFAULT_PROFILE"] = self.cloud.default_profile
        
        # Setup SSH key
        ssh_key_path = os.path.expanduser(self.cloud.ssh_key_path)
        if os.path.exists(ssh_key_path):
            try:
                os.chmod(ssh_key_path, 0o600)
                os.environ["SSH_KEY_PATH"] = ssh_key_path
            except Exception:
                pass
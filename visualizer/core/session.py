#!/usr/bin/env python3
"""Benchmark session management with proper resource cleanup."""

import tempfile
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from .config import Config
from utils.ssh import SSHClient
from cloud.aws import AWSProvider


class BenchmarkSession:
    """Manages benchmark execution session with proper resource cleanup."""
    
    def __init__(self, config: Config):
        self.config = config
        self.temp_dirs: List[str] = []
        self.ssh_clients: Dict[str, SSHClient] = {}
        self.cloud_provider = AWSProvider()
        self.created_instances: List[Dict[str, Any]] = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.cleanup()
    
    def get_ssh_client(self, instance: Dict[str, Any]) -> SSHClient:
        """Get or create SSH client for instance."""
        instance_name = instance['name']
        if instance_name not in self.ssh_clients:
            self.ssh_clients[instance_name] = SSHClient(instance, self.config.colors)
        return self.ssh_clients[instance_name]
    
    def create_temp_dir(self) -> str:
        """Create temporary directory and track for cleanup."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_run_directory(self) -> Path:
        """Create timestamped run directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.config.results_dir / timestamp
        run_dir.mkdir(exist_ok=True)
        return run_dir
    
    async def cleanup(self):
        """Clean up all session resources."""
        # Cleanup temporary directories
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        # Cleanup cloud instances if created
        if self.created_instances:
            try:
                self.cloud_provider.cleanup_instances(self.created_instances)
            except Exception:
                pass
        
        self.temp_dirs.clear()
        self.ssh_clients.clear()
        self.created_instances.clear()
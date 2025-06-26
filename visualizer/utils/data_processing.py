#!/usr/bin/env python3
"""Optimized data processing utilities with streaming and validation."""

import json
from pathlib import Path
from typing import Iterator, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Validated benchmark result data structure."""
    instance_name: str
    benchmark_type: str
    metrics: Dict[str, Any]
    timestamp: datetime
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not self.instance_name:
            raise ValueError("instance_name cannot be empty")
        if not self.benchmark_type:
            raise ValueError("benchmark_type cannot be empty")
        if not isinstance(self.metrics, dict):
            raise ValueError("metrics must be a dictionary")


class StreamingParser:
    """Memory-efficient streaming parser for large result files."""
    
    @staticmethod
    def parse_results_streaming(file_path: Path) -> Iterator[BenchmarkResult]:
        """Parse results file in streaming fashion to minimize memory usage."""
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r') as f:
                current_result = {}
                
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Try to parse as key-value pair
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            current_result[key.strip()] = value.strip()
                        
                        # Check if we have a complete result
                        if StreamingParser._is_complete_result(current_result):
                            result = StreamingParser._create_benchmark_result(current_result)
                            if result:
                                yield result
                            current_result = {}
                    
                    except Exception as e:
                        # Log parsing error but continue
                        print(f"Warning: Error parsing line {line_num} in {file_path}: {e}")
                        continue
                
                # Handle any remaining result
                if current_result and StreamingParser._is_complete_result(current_result):
                    result = StreamingParser._create_benchmark_result(current_result)
                    if result:
                        yield result
        
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    
    @staticmethod
    def _is_complete_result(result: Dict[str, Any]) -> bool:
        """Check if result has minimum required fields."""
        required_fields = ['instance_name', 'benchmark_type']
        return all(field in result for field in required_fields)
    
    @staticmethod
    def _create_benchmark_result(data: Dict[str, Any]) -> Optional[BenchmarkResult]:
        """Create BenchmarkResult from parsed data."""
        try:
            return BenchmarkResult(
                instance_name=data.get('instance_name', ''),
                benchmark_type=data.get('benchmark_type', ''),
                metrics=data.get('metrics', {}),
                timestamp=datetime.now()
            )
        except ValueError as e:
            print(f"Warning: Invalid result data: {e}")
            return None


class ResultCache:
    """Simple in-memory cache for parsed results."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result."""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any):
        """Cache result with LRU eviction."""
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Evict least recently used
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = value
        self.access_order.append(key)
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_order.clear()


class DataProcessor:
    """Optimized data processor with caching and streaming."""
    
    def __init__(self, cache_size: int = 1000):
        self.cache = ResultCache(cache_size)
        self.parser = StreamingParser()
    
    def process_file(self, file_path: Path, force_refresh: bool = False) -> Iterator[BenchmarkResult]:
        """Process file with caching."""
        cache_key = f"{file_path}:{file_path.stat().st_mtime}"
        
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                yield from cached
                return
        
        # Parse and cache results
        results = list(self.parser.parse_results_streaming(file_path))
        self.cache.put(cache_key, results)
        yield from results
    
    def process_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Process entire directory efficiently."""
        results = {}
        
        for file_path in dir_path.rglob("*.txt"):
            if file_path.is_file():
                file_results = list(self.process_file(file_path))
                if file_results:
                    # Group by instance and benchmark
                    for result in file_results:
                        instance_key = result.instance_name
                        benchmark_key = result.benchmark_type
                        
                        if instance_key not in results:
                            results[instance_key] = {}
                        if benchmark_key not in results[instance_key]:
                            results[instance_key][benchmark_key] = []
                        
                        results[instance_key][benchmark_key].append(result)
        
        return results
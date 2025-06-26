#!/usr/bin/env python3
"""Base cloud provider interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class CloudProvider(ABC):
    """Abstract base class for cloud providers."""
    
    @abstractmethod
    def get_instances(self) -> List[Dict[str, Any]]:
        """Get list of available instances."""
        pass
    
    @abstractmethod
    def create_instances(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create new instances based on configuration."""
        pass
    
    @abstractmethod
    def cleanup_instances(self, instances: List[Dict[str, Any]]) -> None:
        """Clean up created instances."""
        pass
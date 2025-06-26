#!/usr/bin/env python3
"""AWS cloud provider implementation."""

from typing import List, Dict, Any
from .base import CloudProvider
from cloud_providers import aws_provider


class AWSProvider(CloudProvider):
    """AWS cloud provider implementation."""
    
    def get_instances(self) -> List[Dict[str, Any]]:
        """Get list of available AWS instances."""
        return aws_provider.get_instances()
    
    def create_instances(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create new AWS instances."""
        return aws_provider.create_instances(config)
    
    def cleanup_instances(self, instances: List[Dict[str, Any]]) -> None:
        """Clean up AWS instances."""
        aws_provider.cleanup_instances(instances)
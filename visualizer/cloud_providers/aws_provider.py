#!/usr/bin/env python3
"""
AWS Provider Module

Handles interaction with AWS EC2 instances.
"""

import os
import boto3
from pathlib import Path


def get_instances():
    """
    Get list of running EC2 instances.
    
    Returns:
        list: List of instance dictionaries with name, ip, username, and key_path
    """
    try:
        # Get AWS credentials from environment
        region = os.environ.get('AWS_REGION', 'us-west-2')
        profile = os.environ.get('AWS_DEFAULT_PROFILE')
        
        # Initialize boto3 client
        session = boto3.Session(profile_name=profile, region_name=region)
        ec2 = session.resource('ec2')
        
        # Get running instances
        instances = []
        for instance in ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]):
            # Get instance name from tags
            name = "unnamed"
            for tag in instance.tags or []:
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            # Get IP address
            ip = instance.public_ip_address or instance.private_ip_address
            if not ip:
                continue
            
            # Determine username based on platform
            username = "ubuntu"  # Default to ubuntu
            if instance.platform == "windows":
                continue  # Skip Windows instances
            
            # Try to determine username based on image ID
            image_id = instance.image_id.lower() if instance.image_id else ""
            if "amazon" in image_id:
                username = "ec2-user"
            elif "debian" in image_id:
                username = "admin"
            elif "centos" in image_id:
                username = "centos"
            
            # Get SSH key path
            key_name = instance.key_name
            key_path = os.path.expanduser(f"~/.ssh/{key_name}.pem")
            
            # If key doesn't exist at default location, try to find it
            if not os.path.exists(key_path):
                # Try common locations
                for path in [
                    os.path.expanduser(f"~/.ssh/id_rsa"),
                    os.path.expanduser(f"~/.ssh/id_ed25519"),
                ]:
                    if os.path.exists(path):
                        key_path = path
                        break
            
            instances.append({
                "name": name,
                "ip": ip,
                "username": username,
                "key_path": key_path,
                "instance_id": instance.id,
                "instance_type": instance.instance_type,
                "launch_time": instance.launch_time
            })
        
        return instances
    
    except Exception as e:
        print(f"Error fetching AWS instances: {str(e)}")
        return []
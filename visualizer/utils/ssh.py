#!/usr/bin/env python3
"""SSH utilities for remote command execution."""

import os
import subprocess
import threading
from typing import Tuple, Optional
from termcolor import colored
from datetime import datetime


class SSHClient:
    """SSH client for executing commands on remote instances."""
    
    def __init__(self, instance: dict, colors: list):
        self.instance = instance
        self.color = colors[hash(instance['name']) % len(colors)]
        self.prefix = f"[{instance['name']}] "
    
    def run_command(self, command: str, capture_output: bool = False) -> Tuple[int, str, str]:
        """Execute SSH command on remote instance."""
        ssh_cmd = self._build_ssh_command(command)
        
        if capture_output:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        else:
            return self._run_with_output(ssh_cmd)
    
    def _build_ssh_command(self, command: str) -> list:
        """Build SSH command with proper options."""
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=10",
        ]
        
        ssh_key = os.environ.get("SSH_KEY_PATH")
        if ssh_key:
            ssh_cmd.extend(["-i", ssh_key])
        
        ssh_cmd.extend([
            f"{self.instance['username']}@{self.instance['ip']}",
            command
        ])
        
        return ssh_cmd
    
    def _run_with_output(self, ssh_cmd: list) -> int:
        """Run command with real-time colored output."""
        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        def print_output(pipe, is_stderr=False):
            prefix = f"[{self.instance['name']}-ERR] " if is_stderr else self.prefix
            for line in pipe:
                if line.strip():
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[{timestamp}] " + colored(prefix, self.color) + line.strip())
        
        stdout_thread = threading.Thread(target=print_output, args=(process.stdout,))
        stderr_thread = threading.Thread(target=print_output, args=(process.stderr, True))
        
        stdout_thread.start()
        stderr_thread.start()
        
        exit_code = process.wait()
        
        stdout_thread.join()
        stderr_thread.join()
        
        return exit_code
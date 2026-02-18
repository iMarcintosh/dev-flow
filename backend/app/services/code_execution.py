"""
Docker Code Execution Service

Allows secure code execution in isolated Docker containers.
Supports Python, JavaScript/Node, and Bash.
"""
import docker
import tempfile
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CodeExecutionService:
    """Service for executing code in Docker containers"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
    
    def execute_python(
        self,
        code: str,
        timeout: int = 30,
        memory_limit: str = "128m"
    ) -> Dict[str, any]:
        """
        Execute Python code in isolated container
        
        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (default 30)
            memory_limit: Memory limit (default 128m)
            
        Returns:
            Dict with stdout, stderr, exit_code, error
        """
        return self._execute_code(
            code=code,
            language="python",
            image="python:3.11-alpine",
            command=["python", "-c"],
            timeout=timeout,
            memory_limit=memory_limit
        )
    
    def execute_javascript(
        self,
        code: str,
        timeout: int = 30,
        memory_limit: str = "128m"
    ) -> Dict[str, any]:
        """
        Execute JavaScript code in isolated container
        
        Args:
            code: JavaScript code to execute
            timeout: Execution timeout in seconds (default 30)
            memory_limit: Memory limit (default 128m)
            
        Returns:
            Dict with stdout, stderr, exit_code, error
        """
        return self._execute_code(
            code=code,
            language="javascript",
            image="node:20-alpine",
            command=["node", "-e"],
            timeout=timeout,
            memory_limit=memory_limit
        )
    
    def execute_bash(
        self,
        code: str,
        timeout: int = 30,
        memory_limit: str = "128m"
    ) -> Dict[str, any]:
        """
        Execute Bash script in isolated container
        
        Args:
            code: Bash script to execute
            timeout: Execution timeout in seconds (default 30)
            memory_limit: Memory limit (default 128m)
            
        Returns:
            Dict with stdout, stderr, exit_code, error
        """
        return self._execute_code(
            code=code,
            language="bash",
            image="alpine:latest",
            command=["sh", "-c"],
            timeout=timeout,
            memory_limit=memory_limit
        )
    
    def _execute_code(
        self,
        code: str,
        language: str,
        image: str,
        command: list,
        timeout: int,
        memory_limit: str
    ) -> Dict[str, any]:
        """
        Internal method to execute code in Docker container
        
        Args:
            code: Code to execute
            language: Language name (for logging)
            image: Docker image to use
            command: Command to run (e.g., ["python", "-c"])
            timeout: Execution timeout in seconds
            memory_limit: Memory limit
            
        Returns:
            Dict with execution results
        """
        if not self.client:
            return {
                "stdout": "",
                "stderr": "Docker not available",
                "exit_code": 1,
                "error": "Docker client not initialized",
                "timed_out": False
            }
        
        try:
            # Pull image if not exists
            try:
                self.client.images.get(image)
            except docker.errors.ImageNotFound:
                logger.info(f"Pulling Docker image: {image}")
                self.client.images.pull(image)
            
            # Prepare command
            full_command = command + [code]
            
            # Run container with security restrictions
            logger.info(f"Executing {language} code in Docker container")
            container = self.client.containers.run(
                image=image,
                command=full_command,
                detach=True,
                network_disabled=True,  # No network access
                mem_limit=memory_limit,
                memswap_limit=memory_limit,  # No swap
                cpu_quota=50000,  # 50% of one CPU
                pids_limit=100,  # Limit processes
                remove=False,  # Keep container for logs
                read_only=True,  # Read-only filesystem
                security_opt=["no-new-privileges"],  # Security
            )
            
            # Wait for completion with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get('StatusCode', 1)
                timed_out = False
            except Exception as e:
                logger.warning(f"Container timed out: {e}")
                container.kill()
                exit_code = 124  # Standard timeout exit code
                timed_out = True
            
            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            
            # Cleanup
            container.remove(force=True)
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "error": None,
                "timed_out": timed_out
            }
            
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "error": str(e),
                "timed_out": False
            }


# Global instance
code_executor = CodeExecutionService()

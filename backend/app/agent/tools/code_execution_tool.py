"""
Code Execution Tool for Custom Agents

Allows agents to execute Python, JavaScript, and Bash code
in isolated Docker containers.
"""
from langchain_core.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
from app.services.code_execution import code_executor


class CodeExecutionInput(BaseModel):
    """Input schema for code execution tool"""
    code: str = Field(description="The code to execute")
    language: str = Field(
        description="Programming language: 'python', 'javascript', or 'bash'",
        default="python"
    )
    timeout: int = Field(
        description="Execution timeout in seconds (max 60)",
        default=30,
        ge=1,
        le=60
    )


class CodeExecutionTool(BaseTool):
    """Tool for executing code in Docker containers"""
    
    name: str = "execute_code"
    description: str = """
    Execute code in a secure isolated Docker container.
    Supports Python, JavaScript (Node.js), and Bash.
    Use this to run code, test algorithms, or perform calculations.
    
    Examples:
    - Python: Calculate fibonacci, data analysis, algorithm testing
    - JavaScript: JSON manipulation, async operations, string processing
    - Bash: File operations, text processing, system commands
    
    Security: Code runs in isolated container with no network access,
    limited memory (128MB), and execution timeout.
    """
    args_schema: Type[BaseModel] = CodeExecutionInput
    
    def _run(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30
    ) -> str:
        """Execute code and return results"""
        
        # Validate language
        language = language.lower()
        if language not in ["python", "javascript", "bash"]:
            return f"Error: Unsupported language '{language}'. Use 'python', 'javascript', or 'bash'."
        
        # Execute code
        if language == "python":
            result = code_executor.execute_python(code, timeout=timeout)
        elif language == "javascript":
            result = code_executor.execute_javascript(code, timeout=timeout)
        else:  # bash
            result = code_executor.execute_bash(code, timeout=timeout)
        
        # Format output
        output_parts = []
        
        if result.get("timed_out"):
            output_parts.append(f"⏱️ Execution timed out after {timeout} seconds")
        
        if result.get("stdout"):
            output_parts.append(f"📤 Output:\n{result['stdout']}")
        
        if result.get("stderr"):
            output_parts.append(f"⚠️ Errors:\n{result['stderr']}")
        
        if result.get("error"):
            output_parts.append(f"❌ Execution Error: {result['error']}")
        
        exit_code = result.get("exit_code", 1)
        if exit_code == 0:
            output_parts.append("✅ Exit code: 0 (Success)")
        else:
            output_parts.append(f"❌ Exit code: {exit_code} (Failed)")
        
        if not output_parts:
            return "No output (code executed successfully with no output)"
        
        return "\n\n".join(output_parts)
    
    async def _arun(self, *args, **kwargs):
        """Async version - not implemented, falls back to sync"""
        return self._run(*args, **kwargs)


# Create tool instance
code_execution_tool = CodeExecutionTool()

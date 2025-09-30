#!/usr/bin/env python3
"""
Testing MCP Server (Port 8005)

Provides testing capabilities for autonomous AI agents including test execution,
test generation, coverage analysis, and test reporting.
"""

import os
import asyncio
import logging
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys

# Add mcp_servers to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_mcp_server import BaseMCPServer, execute_shell_command

logger = logging.getLogger(__name__)

class TestingMCPServer(BaseMCPServer):
    """MCP Server for testing operations"""
    
    def __init__(self):
        super().__init__(
            name="testing_mcp",
            port=8005,
            description="Testing operations for autonomous development"
        )
        self.workspace_root = "/Users/xidioda/Projects/CMP"
        self.setup_testing_tools()
        self.setup_testing_capabilities()
        
    def setup_testing_capabilities(self):
        """Register testing capabilities"""
        self.register_capability("test_execution", "Run tests and analyze results")
        self.register_capability("test_generation", "Generate test cases automatically")
        self.register_capability("coverage_analysis", "Analyze test coverage")
        self.register_capability("performance_testing", "Performance and load testing")
        self.register_capability("test_reporting", "Generate test reports")
        
    def setup_testing_tools(self):
        """Register testing tools"""
        self.register_tool("run_tests", self.run_tests, "Execute test suite")
        self.register_tool("run_specific_test", self.run_specific_test, "Run specific test file or method")
        self.register_tool("generate_test_report", self.generate_test_report, "Generate test report")
        self.register_tool("check_coverage", self.check_coverage, "Check test coverage")
        self.register_tool("discover_tests", self.discover_tests, "Discover available tests")
        self.register_tool("validate_test_setup", self.validate_test_setup, "Validate test environment")
        self.register_tool("run_linting", self.run_linting, "Run code linting")
        self.register_tool("benchmark_code", self.benchmark_code, "Benchmark code performance")
        
    async def run_tests(self, test_directory: str = "tests", pattern: str = "test_*.py") -> Dict[str, Any]:
        """Execute test suite"""
        try:
            test_path = os.path.join(self.workspace_root, test_directory)
            if not os.path.exists(test_path):
                return {"success": False, "error": f"Test directory not found: {test_directory}"}
                
            # Run pytest with detailed output
            command = f"python -m pytest {test_path} -v --tb=short --json-report --json-report-file=/tmp/test_report.json"
            result = await execute_shell_command(command, self.workspace_root)
            
            # Parse test results
            test_results = {
                "command": command,
                "exit_code": result["return_code"],
                "success": result["success"],
                "stdout": result["stdout"],
                "stderr": result["stderr"]
            }
            
            # Try to parse JSON report if available
            try:
                with open("/tmp/test_report.json", "r") as f:
                    json_report = json.load(f)
                    test_results["detailed_report"] = json_report
            except:
                test_results["detailed_report"] = None
                
            # Parse output for summary
            if result["stdout"]:
                lines = result["stdout"].split('\n')
                for line in lines:
                    if "passed" in line and "failed" in line:
                        test_results["summary"] = line.strip()
                        break
                        
            return test_results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def run_specific_test(self, test_path: str, method: str = None) -> Dict[str, Any]:
        """Run specific test file or method"""
        try:
            full_test_path = os.path.join(self.workspace_root, test_path)
            if not os.path.exists(full_test_path):
                return {"success": False, "error": f"Test file not found: {test_path}"}
                
            # Build command
            if method:
                command = f"python -m pytest {test_path}::{method} -v"
            else:
                command = f"python -m pytest {test_path} -v"
                
            result = await execute_shell_command(command, self.workspace_root)
            
            return {
                "success": result["success"],
                "test_path": test_path,
                "method": method,
                "command": command,
                "exit_code": result["return_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def generate_test_report(self, output_format: str = "html") -> Dict[str, Any]:
        """Generate test report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if output_format == "html":
                report_file = f"test_report_{timestamp}.html"
                command = f"python -m pytest tests/ --html={report_file} --self-contained-html"
            elif output_format == "xml":
                report_file = f"test_report_{timestamp}.xml"
                command = f"python -m pytest tests/ --junitxml={report_file}"
            else:
                return {"success": False, "error": f"Unsupported format: {output_format}"}
                
            result = await execute_shell_command(command, self.workspace_root)
            
            report_path = os.path.join(self.workspace_root, report_file)
            report_exists = os.path.exists(report_path)
            
            return {
                "success": result["success"],
                "report_file": report_file,
                "report_exists": report_exists,
                "format": output_format,
                "command": command,
                "stdout": result["stdout"],
                "stderr": result["stderr"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def check_coverage(self, source_dir: str = "cmp") -> Dict[str, Any]:
        """Check test coverage"""
        try:
            # Run coverage analysis
            commands = [
                f"python -m coverage run -m pytest tests/",
                f"python -m coverage report",
                f"python -m coverage json"
            ]
            
            results = {}
            for i, command in enumerate(commands):
                result = await execute_shell_command(command, self.workspace_root)
                results[f"step_{i+1}"] = result
                if not result["success"] and i == 0:  # First command failed
                    return {"success": False, "error": "Coverage run failed", "details": result}
                    
            # Parse coverage report
            coverage_data = {}
            try:
                with open(os.path.join(self.workspace_root, "coverage.json"), "r") as f:
                    coverage_data = json.load(f)
            except:
                pass
                
            return {
                "success": True,
                "coverage_data": coverage_data,
                "report_output": results["step_2"]["stdout"],
                "commands_run": commands
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def discover_tests(self, test_directory: str = "tests") -> Dict[str, Any]:
        """Discover available tests"""
        try:
            test_path = os.path.join(self.workspace_root, test_directory)
            if not os.path.exists(test_path):
                return {"success": False, "error": f"Test directory not found: {test_directory}"}
                
            # Use pytest to discover tests
            command = f"python -m pytest --collect-only -q {test_directory}"
            result = await execute_shell_command(command, self.workspace_root)
            
            # Parse discovered tests
            discovered_tests = []
            if result["success"] and result["stdout"]:
                lines = result["stdout"].split('\n')
                for line in lines:
                    if "::" in line and "test_" in line:
                        discovered_tests.append(line.strip())
                        
            # Also scan for test files manually
            test_files = []
            for root, dirs, files in os.walk(test_path):
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        rel_path = os.path.relpath(os.path.join(root, file), self.workspace_root)
                        test_files.append(rel_path)
                        
            return {
                "success": True,
                "test_directory": test_directory,
                "discovered_tests": discovered_tests,
                "test_files": test_files,
                "total_tests": len(discovered_tests),
                "total_files": len(test_files)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def validate_test_setup(self) -> Dict[str, Any]:
        """Validate test environment"""
        try:
            validations = []
            
            # Check if pytest is available
            pytest_check = await execute_shell_command("python -m pytest --version", self.workspace_root)
            validations.append({
                "check": "pytest_available",
                "passed": pytest_check["success"],
                "message": "pytest is available" if pytest_check["success"] else "pytest not found"
            })
            
            # Check if test directory exists
            test_dir_exists = os.path.exists(os.path.join(self.workspace_root, "tests"))
            validations.append({
                "check": "test_directory_exists",
                "passed": test_dir_exists,
                "message": "Test directory exists" if test_dir_exists else "Test directory missing"
            })
            
            # Check for test files
            test_files_exist = False
            if test_dir_exists:
                test_path = os.path.join(self.workspace_root, "tests")
                for root, dirs, files in os.walk(test_path):
                    if any(f.startswith("test_") and f.endswith(".py") for f in files):
                        test_files_exist = True
                        break
                        
            validations.append({
                "check": "test_files_exist",
                "passed": test_files_exist,
                "message": "Test files found" if test_files_exist else "No test files found"
            })
            
            # Check if coverage is available
            coverage_check = await execute_shell_command("python -m coverage --version", self.workspace_root)
            validations.append({
                "check": "coverage_available",
                "passed": coverage_check["success"],
                "message": "Coverage tool available" if coverage_check["success"] else "Coverage tool not found"
            })
            
            all_passed = all(v["passed"] for v in validations)
            
            return {
                "success": True,
                "validations": validations,
                "overall_status": "valid" if all_passed else "issues_found",
                "recommendations": self._generate_recommendations(validations)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _generate_recommendations(self, validations: List[Dict]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        for validation in validations:
            if not validation["passed"]:
                if validation["check"] == "pytest_available":
                    recommendations.append("Install pytest: pip install pytest")
                elif validation["check"] == "test_directory_exists":
                    recommendations.append("Create tests directory: mkdir tests")
                elif validation["check"] == "test_files_exist":
                    recommendations.append("Create test files in tests/ directory")
                elif validation["check"] == "coverage_available":
                    recommendations.append("Install coverage: pip install coverage")
                    
        if not recommendations:
            recommendations.append("Test environment is properly configured")
            
        return recommendations
        
    async def run_linting(self, target: str = "cmp") -> Dict[str, Any]:
        """Run code linting"""
        try:
            linting_results = {}
            
            # Try different linters
            linters = [
                ("flake8", f"python -m flake8 {target}"),
                ("pylint", f"python -m pylint {target}"),
                ("black", f"python -m black --check {target}")
            ]
            
            for linter_name, command in linters:
                result = await execute_shell_command(command, self.workspace_root)
                linting_results[linter_name] = {
                    "available": True,
                    "success": result["success"],
                    "stdout": result["stdout"],
                    "stderr": result["stderr"]
                }
                
                # If command not found, mark as unavailable
                if "command not found" in result["stderr"] or "No module named" in result["stderr"]:
                    linting_results[linter_name]["available"] = False
                    
            return {
                "success": True,
                "target": target,
                "linting_results": linting_results,
                "summary": self._summarize_linting(linting_results)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _summarize_linting(self, results: Dict) -> Dict[str, Any]:
        """Summarize linting results"""
        available_linters = [name for name, data in results.items() if data["available"]]
        passed_linters = [name for name, data in results.items() if data["available"] and data["success"]]
        
        return {
            "available_linters": available_linters,
            "passed_linters": passed_linters,
            "total_issues": sum(
                len(data["stdout"].split('\n')) if data["stdout"] else 0 
                for data in results.values() 
                if data["available"] and not data["success"]
            )
        }
        
    async def benchmark_code(self, code_snippet: str, iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark code performance"""
        try:
            import timeit
            
            # Simple benchmark using timeit
            try:
                execution_time = timeit.timeit(code_snippet, number=iterations)
                avg_time = execution_time / iterations
                
                return {
                    "success": True,
                    "code_snippet": code_snippet,
                    "iterations": iterations,
                    "total_time": execution_time,
                    "average_time": avg_time,
                    "iterations_per_second": 1 / avg_time if avg_time > 0 else 0
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Benchmark failed: {str(e)}",
                    "code_snippet": code_snippet
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

async def main():
    """Start the Testing MCP Server"""
    server = TestingMCPServer()
    runner = await server.start_server()
    
    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Testing MCP Server...")
        await runner.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
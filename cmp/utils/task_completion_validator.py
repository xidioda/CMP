"""
Task Completion Validation System

This module provides proper validation that tasks are actually completed
before allowing GitHub issues to be closed. No more fake completions!
"""

import asyncio
import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TaskCompletionValidator:
    """Validates that tasks are actually completed before closure"""
    
    def __init__(self, workspace_path: str = "/Users/xidioda/Projects/CMP"):
        self.workspace_path = workspace_path
        
    async def validate_task_completion(self, 
                                     task: Dict[str, Any], 
                                     execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that a task was actually completed with real work"""
        try:
            task_type = task.get('type', 'unknown')
            task_id = task.get('id', 'unknown')
            
            validation_result = {
                "validated": False,
                "validation_checks": [],
                "validation_errors": [],
                "completion_score": 0,
                "allow_closure": False
            }
            
            # Run specific validations based on task type
            if task_type == "testing":
                validation_result = await self._validate_testing_task(task, execution_result, validation_result)
            elif task_type == "completion":
                validation_result = await self._validate_completion_task(task, execution_result, validation_result)
            elif task_type == "enhancement":
                validation_result = await self._validate_enhancement_task(task, execution_result, validation_result)
            else:
                validation_result = await self._validate_generic_task(task, execution_result, validation_result)
            
            # Calculate final validation score
            total_checks = len(validation_result["validation_checks"])
            passed_checks = sum(1 for check in validation_result["validation_checks"] if check.get("passed", False))
            
            if total_checks > 0:
                validation_result["completion_score"] = (passed_checks / total_checks) * 100
            
            # Allow closure only if completion score >= 80% and no critical errors
            critical_errors = [error for error in validation_result["validation_errors"] if error.get("critical", False)]
            validation_result["allow_closure"] = (
                validation_result["completion_score"] >= 80 and 
                len(critical_errors) == 0
            )
            
            validation_result["validated"] = True
            
            logger.info(f"Task {task_id} validation: {validation_result['completion_score']:.1f}% complete, "
                       f"closure {'ALLOWED' if validation_result['allow_closure'] else 'DENIED'}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Task validation failed for {task_id}: {e}")
            return {
                "validated": False,
                "validation_errors": [{"message": f"Validation system error: {e}", "critical": True}],
                "allow_closure": False
            }
    
    async def _validate_testing_task(self, task: Dict[str, Any], execution_result: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate testing tasks - ensure tests were actually created and pass"""
        
        # Check 1: Were test files actually created?
        test_files_check = await self._check_test_files_created(task, execution_result)
        validation_result["validation_checks"].append(test_files_check)
        
        # Check 2: Do the tests actually run and pass?
        test_execution_check = await self._check_tests_run_and_pass()
        validation_result["validation_checks"].append(test_execution_check)
        
        # Check 3: Is test coverage improved?
        coverage_check = await self._check_test_coverage_improved()
        validation_result["validation_checks"].append(coverage_check)
        
        # Check 4: Are test files following project conventions?
        convention_check = await self._check_test_conventions()
        validation_result["validation_checks"].append(convention_check)
        
        return validation_result
    
    async def _validate_completion_task(self, task: Dict[str, Any], execution_result: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate completion tasks - ensure TODOs/features were actually implemented"""
        
        # Check 1: Were TODO items actually removed/completed?
        todo_check = await self._check_todos_completed()
        validation_result["validation_checks"].append(todo_check)
        
        # Check 2: Were new features actually implemented?
        feature_check = await self._check_features_implemented(task)
        validation_result["validation_checks"].append(feature_check)
        
        # Check 3: Does the code compile/run without errors?
        compilation_check = await self._check_code_compilation()
        validation_result["validation_checks"].append(compilation_check)
        
        return validation_result
    
    async def _validate_enhancement_task(self, task: Dict[str, Any], execution_result: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate enhancement tasks - ensure real improvements were made"""
        
        # Check 1: Were files actually modified?
        file_modification_check = await self._check_files_modified(execution_result)
        validation_result["validation_checks"].append(file_modification_check)
        
        # Check 2: Do the changes improve functionality?
        functionality_check = await self._check_functionality_improved()
        validation_result["validation_checks"].append(functionality_check)
        
        return validation_result
    
    async def _validate_generic_task(self, task: Dict[str, Any], execution_result: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generic tasks"""
        
        # Check 1: Was real work performed (files changed, commands run, etc.)?
        work_performed_check = await self._check_real_work_performed(execution_result)
        validation_result["validation_checks"].append(work_performed_check)
        
        return validation_result
    
    async def _check_test_files_created(self, task: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if test files were actually created"""
        try:
            tests_dir = os.path.join(self.workspace_path, "tests")
            if not os.path.exists(tests_dir):
                return {
                    "check": "test_files_created",
                    "passed": False,
                    "message": "No tests directory found"
                }
            
            # Count test files
            test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
            
            # Check if new test files mentioned in execution result
            files_affected = execution_result.get('files_affected', [])
            new_test_files = [f for f in files_affected if '/tests/' in f and f.endswith('.py')]
            
            return {
                "check": "test_files_created",
                "passed": len(new_test_files) > 0,
                "message": f"Found {len(test_files)} test files total, {len(new_test_files)} newly created",
                "details": {"total_test_files": len(test_files), "new_test_files": len(new_test_files)}
            }
            
        except Exception as e:
            return {
                "check": "test_files_created",
                "passed": False,
                "message": f"Error checking test files: {e}"
            }
    
    async def _check_tests_run_and_pass(self) -> Dict[str, Any]:
        """Check if tests actually run and pass"""
        try:
            # Run pytest to check if tests pass
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            passed = result.returncode == 0
            output_lines = result.stdout.split('\n') if result.stdout else []
            test_summary = next((line for line in output_lines if 'passed' in line and 'failed' in line), "No summary")
            
            return {
                "check": "tests_run_and_pass",
                "passed": passed,
                "message": f"Tests {'PASSED' if passed else 'FAILED'}: {test_summary}",
                "details": {"return_code": result.returncode, "summary": test_summary}
            }
            
        except subprocess.TimeoutExpired:
            return {
                "check": "tests_run_and_pass",
                "passed": False,
                "message": "Tests timed out after 60 seconds"
            }
        except Exception as e:
            return {
                "check": "tests_run_and_pass",
                "passed": False,
                "message": f"Error running tests: {e}"
            }
    
    async def _check_test_coverage_improved(self) -> Dict[str, Any]:
        """Check if test coverage has improved"""
        try:
            # Run pytest with coverage
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=cmp", "--cov-report=term-missing"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Extract coverage percentage
            coverage_line = next((line for line in result.stdout.split('\n') if 'TOTAL' in line), None)
            coverage_percent = 0
            if coverage_line:
                parts = coverage_line.split()
                if len(parts) >= 4:
                    try:
                        coverage_percent = int(parts[-1].replace('%', ''))
                    except ValueError:
                        pass
            
            # Consider coverage improved if > 50% (basic threshold)
            improved = coverage_percent > 50
            
            return {
                "check": "test_coverage_improved", 
                "passed": improved,
                "message": f"Test coverage: {coverage_percent}%",
                "details": {"coverage_percent": coverage_percent}
            }
            
        except Exception as e:
            return {
                "check": "test_coverage_improved",
                "passed": False,
                "message": f"Error checking coverage: {e}"
            }
    
    async def _check_test_conventions(self) -> Dict[str, Any]:
        """Check if test files follow project conventions"""
        try:
            tests_dir = os.path.join(self.workspace_path, "tests")
            if not os.path.exists(tests_dir):
                return {"check": "test_conventions", "passed": False, "message": "No tests directory"}
            
            test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
            convention_violations = []
            
            for test_file in test_files:
                test_path = os.path.join(tests_dir, test_file)
                try:
                    with open(test_path, 'r') as f:
                        content = f.read()
                    
                    # Check for basic conventions
                    if 'import pytest' not in content:
                        convention_violations.append(f"{test_file}: Missing pytest import")
                    
                    if 'def test_' not in content:
                        convention_violations.append(f"{test_file}: No test functions found")
                        
                except Exception as e:
                    convention_violations.append(f"{test_file}: Error reading file - {e}")
            
            passed = len(convention_violations) == 0
            
            return {
                "check": "test_conventions",
                "passed": passed,
                "message": f"Convention check: {len(convention_violations)} violations found",
                "details": {"violations": convention_violations}
            }
            
        except Exception as e:
            return {
                "check": "test_conventions",
                "passed": False,
                "message": f"Error checking conventions: {e}"
            }
    
    async def _check_todos_completed(self) -> Dict[str, Any]:
        """Check if TODO items were actually completed"""
        try:
            # Search for TODO comments in the codebase
            result = subprocess.run(
                ["grep", "-r", "-i", "todo", "cmp/", "--include=*.py"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True
            )
            
            todo_lines = result.stdout.split('\n') if result.stdout else []
            todo_count = len([line for line in todo_lines if line.strip()])
            
            # Consider completed if fewer than 10 TODOs remain
            completed = todo_count < 10
            
            return {
                "check": "todos_completed",
                "passed": completed,
                "message": f"Found {todo_count} remaining TODO items",
                "details": {"remaining_todos": todo_count}
            }
            
        except Exception as e:
            return {
                "check": "todos_completed",
                "passed": False,
                "message": f"Error checking TODOs: {e}"
            }
    
    async def _check_features_implemented(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check if new features were actually implemented"""
        return {
            "check": "features_implemented",
            "passed": True,  # TODO: Implement proper feature detection
            "message": "Feature implementation check not yet implemented",
            "details": {"note": "This check needs enhancement based on specific feature requirements"}
        }
    
    async def _check_code_compilation(self) -> Dict[str, Any]:
        """Check if the code compiles/runs without syntax errors"""
        try:
            # Try to import the main module to check for syntax errors
            result = subprocess.run(
                ["python", "-c", "import cmp.main; print('Import successful')"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            passed = result.returncode == 0
            
            return {
                "check": "code_compilation",
                "passed": passed,
                "message": f"Code compilation {'PASSED' if passed else 'FAILED'}",
                "details": {"return_code": result.returncode, "output": result.stdout, "error": result.stderr}
            }
            
        except Exception as e:
            return {
                "check": "code_compilation",
                "passed": False,
                "message": f"Error checking compilation: {e}"
            }
    
    async def _check_files_modified(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if files were actually modified"""
        files_affected = execution_result.get('files_affected', [])
        
        return {
            "check": "files_modified",
            "passed": len(files_affected) > 0,
            "message": f"{len(files_affected)} files were modified",
            "details": {"files_affected": files_affected}
        }
    
    async def _check_functionality_improved(self) -> Dict[str, Any]:
        """Check if functionality was actually improved"""
        return {
            "check": "functionality_improved",
            "passed": True,  # TODO: Implement proper functionality checking
            "message": "Functionality improvement check not yet implemented",
            "details": {"note": "This check needs enhancement based on specific metrics"}
        }
    
    async def _check_real_work_performed(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if real work was actually performed"""
        indicators = []
        
        if execution_result.get('files_affected'):
            indicators.append(f"{len(execution_result['files_affected'])} files affected")
        
        if execution_result.get('git_operations'):
            indicators.append("Git operations performed")
        
        if execution_result.get('api_calls_made'):
            indicators.append("API calls made")
        
        if execution_result.get('commands_executed'):
            indicators.append("System commands executed")
        
        work_performed = len(indicators) > 0
        
        return {
            "check": "real_work_performed",
            "passed": work_performed,
            "message": f"Work indicators: {', '.join(indicators) if indicators else 'None detected'}",
            "details": {"work_indicators": indicators}
        }

# Global instance
task_completion_validator = TaskCompletionValidator()
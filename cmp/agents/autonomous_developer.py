"""
Autonomous Developer Agent - Enhanced with N8N and MCP Integration

This agent analyzes the project, identifies development needs, and executes real work
through N8N workflows and MCP servers instead of just creating GitHub issues.
"""

import asyncio
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ..utils.github_project_manager import github_project_manager
from ..utils.enhanced_task_execution_engine import enhanced_task_engine
from ..integrations.n8n_workflow_integration import n8n_integration
from ..integrations.mcp_server_integration import mcp_integration

logger = logging.getLogger(__name__)

class AutonomousDeveloperAgent:
    """
    Enhanced autonomous developer that performs real work through N8N and MCP integration
    """
    
    def __init__(self):
        self.workspace_path = "/Users/xidioda/Projects/CMP"
        self.analysis_cache = {}
        self.last_analysis = None
        # Set up task execution engine
        enhanced_task_engine.set_github_manager(github_project_manager)
        
    async def analyze_development_needs(self) -> Dict[str, Any]:
        """
        Analyze the entire project to determine what features/improvements need development
        This is the core intelligence that decides what should be built
        """
        try:
            logger.info("🧠 Autonomous Developer analyzing project development needs...")
            
            development_needs = {
                "urgent_features": [],
                "enhancement_opportunities": [],
                "technical_debt": [],
                "missing_functionality": [],
                "copilot_instructions": []
            }
            
            # 1. Analyze documentation to understand project goals
            docs_analysis = await self._analyze_documentation()
            development_needs.update(docs_analysis)
            
            # 2. Analyze GitHub issues to see what users/stakeholders want
            github_analysis = await self._analyze_github_issues()
            development_needs.update(github_analysis)
            
            # 3. Analyze codebase to identify missing features
            codebase_analysis = await self._analyze_codebase_gaps()
            development_needs.update(codebase_analysis)
            
            # 4. Generate specific Copilot instructions for development
            copilot_instructions = await self._generate_copilot_instructions(development_needs)
            development_needs["copilot_instructions"] = copilot_instructions
            
            # 5. Create GitHub issues with @-mentions to instruct Copilot
            if copilot_instructions:
                await self._create_copilot_instruction_issues(copilot_instructions)
            
            self.last_analysis = datetime.now()
            return {
                "success": True,
                "analysis_timestamp": datetime.now().isoformat(),
                "development_needs": development_needs,
                "total_instructions_created": len(copilot_instructions)
            }
            
        except Exception as e:
            logger.error(f"Error in development needs analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_documentation(self) -> Dict[str, Any]:
        """Analyze project documentation to understand what should be built"""
        try:
            docs_findings = {
                "documented_features": [],
                "missing_implementations": []
            }
            
            docs_dir = os.path.join(self.workspace_path, "docs")
            if os.path.exists(docs_dir):
                for doc_file in os.listdir(docs_dir):
                    if doc_file.endswith('.md'):
                        doc_path = os.path.join(docs_dir, doc_file)
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for documented features that might not be implemented
                        if 'TODO' in content.upper() or 'PLANNED' in content.upper():
                            docs_findings["missing_implementations"].append({
                                "file": doc_file,
                                "feature": f"Planned feature mentioned in {doc_file}"
                            })
                        
                        # Look for API endpoints or features mentioned in docs
                        if '/api/' in content or 'endpoint' in content.lower():
                            docs_findings["documented_features"].append({
                                "file": doc_file,
                                "type": "API documentation"
                            })
            
            return docs_findings
            
        except Exception as e:
            logger.error(f"Error analyzing documentation: {e}")
            return {"documented_features": [], "missing_implementations": []}
    
    async def _analyze_github_issues(self) -> Dict[str, Any]:
        """Analyze GitHub issues to understand what stakeholders want developed"""
        try:
            github_findings = {
                "open_feature_requests": [],
                "bug_reports": [],
                "enhancement_requests": []
            }
            
            if not github_project_manager.repo:
                return github_findings
            
            # Get recent open issues
            issues = github_project_manager.repo.get_issues(state='open')
            
            for issue in list(issues)[:20]:  # Analyze last 20 issues
                labels = [label.name for label in issue.labels]
                
                if any('feature' in label.lower() for label in labels):
                    github_findings["open_feature_requests"].append({
                        "number": issue.number,
                        "title": issue.title,
                        "priority": "high" if any('urgent' in label.lower() for label in labels) else "medium"
                    })
                
                elif any('bug' in label.lower() for label in labels):
                    github_findings["bug_reports"].append({
                        "number": issue.number,
                        "title": issue.title,
                        "priority": "high" if any('critical' in label.lower() for label in labels) else "medium"
                    })
                
                elif any('enhancement' in label.lower() for label in labels):
                    github_findings["enhancement_requests"].append({
                        "number": issue.number,
                        "title": issue.title
                    })
            
            return github_findings
            
        except Exception as e:
            logger.error(f"Error analyzing GitHub issues: {e}")
            return {"open_feature_requests": [], "bug_reports": [], "enhancement_requests": []}
    
    async def _analyze_codebase_gaps(self) -> Dict[str, Any]:
        """Analyze codebase to identify missing functionality"""
        try:
            codebase_findings = {
                "missing_tests": [],
                "incomplete_features": [],
                "architecture_gaps": []
            }
            
            # Check for missing test files
            src_files = []
            test_files = []
            
            for root, dirs, files in os.walk(self.workspace_path):
                if any(skip in root for skip in ['__pycache__', '.git', 'node_modules', '.venv']):
                    continue
                    
                for file in files:
                    if file.endswith('.py'):
                        if 'test' in file.lower() or 'tests' in root.lower():
                            test_files.append(file)
                        else:
                            src_files.append(file)
            
            # Identify source files without corresponding tests
            tested_modules = {f.replace('test_', '').replace('_test', '') for f in test_files}
            
            for src_file in src_files:
                module_name = src_file.replace('.py', '')
                if module_name not in tested_modules and not module_name.startswith('__'):
                    codebase_findings["missing_tests"].append({
                        "file": src_file,
                        "type": "missing_unit_tests"
                    })
            
            # Check for incomplete features (files with TODO/FIXME)
            for root, dirs, files in os.walk(self.workspace_path):
                if any(skip in root for skip in ['__pycache__', '.git', 'node_modules', '.venv']):
                    continue
                    
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            if 'TODO' in content or 'FIXME' in content:
                                codebase_findings["incomplete_features"].append({
                                    "file": file,
                                    "type": "has_todo_comments"
                                })
                        except:
                            continue
            
            return codebase_findings
            
        except Exception as e:
            logger.error(f"Error analyzing codebase gaps: {e}")
            return {"missing_tests": [], "incomplete_features": [], "architecture_gaps": []}
    
    async def _generate_copilot_instructions(self, development_needs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific instructions for GitHub Copilot to implement features"""
        try:
            instructions = []
            
            # Instructions for missing tests
            missing_tests = development_needs.get("missing_tests", [])
            if missing_tests:
                instructions.append({
                    "id": f"tests_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    "title": "🧪 Create comprehensive unit tests for untested modules",
                    "priority": "high",
                    "type": "testing",
                    "copilot_instruction": f"""
## 🤖 Instruction for GitHub Copilot

Please create comprehensive unit tests for the following modules that currently lack test coverage:

**Files needing tests:**
{chr(10).join(f'• {test["file"]}' for test in missing_tests[:10])}

**Requirements:**
1. Create test files in the appropriate `tests/` directory
2. Use pytest framework (already used in the project)
3. Aim for 80%+ code coverage
4. Include both positive and negative test cases
5. Mock external dependencies appropriately
6. Follow existing test patterns in the codebase

**Acceptance Criteria:**
- [ ] Test files created for all listed modules
- [ ] Tests pass when run with `pytest`
- [ ] Code coverage increases significantly
- [ ] Tests follow project conventions

@github-copilot Please implement comprehensive unit tests for these modules.
                    """,
                    "estimated_effort": "2-4 hours",
                    "files_affected": [test["file"] for test in missing_tests[:10]]
                })
            
            # Instructions for feature requests from GitHub issues
            feature_requests = development_needs.get("open_feature_requests", [])
            if feature_requests:
                high_priority_features = [f for f in feature_requests if f.get("priority") == "high"]
                
                if high_priority_features:
                    instructions.append({
                        "id": f"features_{datetime.now().strftime('%Y%m%d_%H%M')}",
                        "title": "🚀 Implement high-priority feature requests",
                        "priority": "urgent",
                        "type": "feature_development",
                        "copilot_instruction": f"""
## 🤖 Instruction for GitHub Copilot

Please implement the following high-priority features requested by stakeholders:

**Feature Requests:**
{chr(10).join(f'• Issue #{fr["number"]}: {fr["title"]}' for fr in high_priority_features[:5])}

**Implementation Guidelines:**
1. Analyze each GitHub issue for detailed requirements
2. Follow existing code patterns and architecture
3. Implement with proper error handling
4. Add appropriate logging
5. Update documentation if needed
6. Create unit tests for new functionality

**Acceptance Criteria:**
- [ ] All listed features implemented and working
- [ ] Code follows project conventions
- [ ] Tests added for new functionality
- [ ] GitHub issues can be closed upon completion

@github-copilot Please implement these requested features following the project's existing patterns.
                        """,
                        "estimated_effort": "4-8 hours",
                        "github_issues": [f["number"] for f in high_priority_features[:5]]
                    })
            
            # Instructions for bug fixes
            bug_reports = development_needs.get("bug_reports", [])
            if bug_reports:
                high_priority_bugs = [b for b in bug_reports if b.get("priority") == "high"]
                
                if high_priority_bugs:
                    instructions.append({
                        "id": f"bugs_{datetime.now().strftime('%Y%m%d_%H%M')}",
                        "title": "🐛 Fix high-priority bugs",
                        "priority": "urgent",
                        "type": "bug_fixes",
                        "copilot_instruction": f"""
## 🤖 Instruction for GitHub Copilot

Please investigate and fix the following high-priority bugs:

**Bug Reports:**
{chr(10).join(f'• Issue #{bug["number"]}: {bug["title"]}' for bug in high_priority_bugs[:5])}

**Fix Guidelines:**
1. Analyze each GitHub issue for reproduction steps
2. Identify root cause of the bug
3. Implement minimal, targeted fix
4. Add regression tests to prevent recurrence
5. Verify fix doesn't break existing functionality

**Acceptance Criteria:**
- [ ] All bugs investigated and fixed
- [ ] Regression tests added
- [ ] No new bugs introduced
- [ ] GitHub issues can be closed upon completion

@github-copilot Please fix these bugs and add appropriate tests to prevent regression.
                        """,
                        "estimated_effort": "2-6 hours",
                        "github_issues": [b["number"] for b in high_priority_bugs[:5]]
                    })
            
            # Instructions for incomplete features
            incomplete_features = development_needs.get("incomplete_features", [])
            if incomplete_features:
                instructions.append({
                    "id": f"incomplete_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    "title": "🔧 Complete TODO items and incomplete features",
                    "priority": "medium",
                    "type": "completion",
                    "copilot_instruction": f"""
## 🤖 Instruction for GitHub Copilot

Please complete the TODO items and incomplete features in the codebase:

**Files with TODOs:**
{chr(10).join(f'• {feature["file"]}' for feature in incomplete_features[:10])}

**Completion Guidelines:**
1. Review each TODO/FIXME comment
2. Implement the missing functionality
3. Remove TODO comments once implemented
4. Ensure implementations follow project patterns
5. Add tests for new functionality

**Acceptance Criteria:**
- [ ] All TODO items addressed
- [ ] Functionality implemented and tested
- [ ] Code quality maintained
- [ ] Documentation updated if needed

@github-copilot Please complete these outstanding TODO items and implement the missing functionality.
                    """,
                    "estimated_effort": "3-6 hours",
                    "files_affected": [f["file"] for f in incomplete_features[:10]]
                })
            
            return instructions
            
        except Exception as e:
            logger.error(f"Error generating Copilot instructions: {e}")
            return []
    
    async def _create_copilot_instruction_issues(self, instructions: List[Dict[str, Any]]) -> None:
        """Create GitHub issues with Copilot instructions (with duplicate prevention)"""
        try:
            # First, get existing open issues to prevent duplicates
            existing_issues = await self._get_existing_open_issues()
            existing_titles = {issue.get('title', '').lower() for issue in existing_issues}
            
            for instruction in instructions:
                # Check if an issue with this title already exists
                instruction_title_lower = instruction["title"].lower()
                
                if instruction_title_lower in existing_titles:
                    logger.info(f"⚠️ Skipping duplicate issue: {instruction['title']} (already exists)")
                    continue
                
                # Check if this type of instruction was recently created (last 24 hours)
                recent_similar = self._find_recent_similar_issues(existing_issues, instruction)
                if recent_similar:
                    logger.info(f"⚠️ Skipping recent similar issue: {instruction['title']} (similar issue #{recent_similar} exists)")
                    continue
                
                # Create GitHub issue with @github-copilot mention
                issue_result = await github_project_manager.create_agent_task_issue(
                    agent_id="autonomous-developer",
                    task_type=instruction["type"],
                    title=instruction["title"],
                    description=instruction["copilot_instruction"],
                    priority=instruction["priority"],
                    labels=["copilot-instruction", "autonomous-development", instruction["type"], "requires-validation"]
                )
                
                if issue_result.get("success"):
                    logger.info(f"✅ Created NEW Copilot instruction issue #{issue_result['issue_number']}: {instruction['title']}")
                else:
                    logger.error(f"❌ Failed to create Copilot instruction issue: {issue_result.get('error')}")
                    
        except Exception as e:
            logger.error(f"Error creating Copilot instruction issues: {e}")
    
    async def _get_existing_open_issues(self) -> List[Dict[str, Any]]:
        """Get all existing open issues to prevent duplicates"""
        try:
            from github import Github
            import os
            
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                return []
            
            gh = Github(github_token)
            repo = gh.get_repo("xidioda/CMP")
            
            issues = []
            for issue in repo.get_issues(state='open'):
                issues.append({
                    'number': issue.number,
                    'title': issue.title,
                    'created_at': issue.created_at,
                    'labels': [label.name for label in issue.labels],
                    'body': issue.body
                })
            
            return issues
            
        except Exception as e:
            logger.error(f"Error getting existing issues: {e}")
            return []
    
    def _find_recent_similar_issues(self, existing_issues: List[Dict[str, Any]], instruction: Dict[str, Any]) -> Optional[int]:
        """Find recent similar issues to prevent duplicates"""
        from datetime import datetime, timezone, timedelta
        
        instruction_type = instruction.get("type", "")
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        for issue in existing_issues:
            # Check if issue is recent (within 24 hours)
            created_at = issue.get('created_at')
            if isinstance(created_at, datetime) and created_at > cutoff_time:
                # Check if it's the same type of issue
                issue_labels = issue.get('labels', [])
                if instruction_type in issue_labels or f"type-{instruction_type}" in issue_labels:
                    return issue.get('number')
        
        return None
    
    async def execute_autonomous_development_cycle(self) -> Dict[str, Any]:
        """Execute a complete autonomous development cycle"""
        try:
            logger.info("🚀 Starting autonomous development cycle - analyzing what to build...")
            
            # Analyze what needs to be developed
            analysis_result = await self.analyze_development_needs()
            
            if not analysis_result.get("success"):
                return {"success": False, "error": "Development analysis failed"}
            
            development_needs = analysis_result.get("development_needs", {})
            instructions_created = analysis_result.get("total_instructions_created", 0)
            
            # Generate summary
            summary = {
                "missing_tests": len(development_needs.get("missing_tests", [])),
                "feature_requests": len(development_needs.get("open_feature_requests", [])),
                "bug_reports": len(development_needs.get("bug_reports", [])),
                "incomplete_features": len(development_needs.get("incomplete_features", [])),
                "copilot_instructions_created": instructions_created
            }
            
            logger.info(f"🧠 Development analysis complete: {summary}")
            
            return {
                "success": True,
                "cycle_timestamp": datetime.now().isoformat(),
                "analysis_summary": summary,
                "copilot_instructions_created": instructions_created,
                "next_analysis": (datetime.now() + timedelta(hours=4)).isoformat(),
                "autonomous_development": True
            }
            
        except Exception as e:
            logger.error(f"Error in autonomous development cycle: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_real_development_work(self) -> Dict[str, Any]:
        """Execute real development work using N8N workflows and MCP servers"""
        try:
            logger.info("🚀 Executing real autonomous development work...")
            
            # Check integration status first
            integration_status = await enhanced_task_engine.check_integrations_status()
            logger.info(f"📊 Integration status: {integration_status.get('overall_status')}")
            
            if integration_status.get('overall_status') == 'error':
                logger.warning("⚠️ No integrations available - falling back to analysis mode")
                return await self.execute_autonomous_development_cycle()
            
            # Analyze current development needs
            development_needs = await self.analyze_development_needs()
            
            # Execute real tasks based on development needs
            execution_results = []
            
            # 1. Run comprehensive tests first
            if development_needs.get("missing_tests"):
                logger.info("🧪 Executing testing workflow...")
                test_task = {
                    "id": f"testing_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    "type": "testing",
                    "modules": ["cmp"],
                    "generate_coverage": True
                }
                
                test_result = await enhanced_task_engine.execute_task_with_real_work(test_task)
                execution_results.append({
                    "task": "testing",
                    "result": test_result,
                    "success": test_result.get('status') == 'completed'
                })
            
            # 2. Complete TODO items and incomplete features
            if development_needs.get("incomplete_features"):
                logger.info("🔧 Executing completion workflow...")
                completion_task = {
                    "id": f"completion_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    "type": "completion",
                    "todo_items": [f["file"] for f in development_needs["incomplete_features"][:5]],
                    "features_to_complete": development_needs.get("missing_functionality", [])[:3]
                }
                
                completion_result = await enhanced_task_engine.execute_task_with_real_work(completion_task)
                execution_results.append({
                    "task": "completion",
                    "result": completion_result,
                    "success": completion_result.get('status') == 'completed'
                })
            
            # 3. Enhance code using MCP Copilot server
            logger.info("🤖 Executing code enhancement via MCP...")
            enhancement_result = await mcp_integration.enhance_code_with_copilot(
                file_path="cmp/main.py",
                enhancement_type="optimization"
            )
            
            execution_results.append({
                "task": "code_enhancement",
                "result": enhancement_result,
                "success": enhancement_result.get('success', False)
            })
            
            # 4. Generate comprehensive tests via MCP
            if development_needs.get("missing_tests"):
                logger.info("📝 Generating tests via MCP server...")
                test_generation_result = await mcp_integration.generate_tests_via_mcp(
                    module_path="cmp/",
                    test_types=["unit", "integration"]
                )
                
                execution_results.append({
                    "task": "test_generation", 
                    "result": test_generation_result,
                    "success": test_generation_result.get('success', False)
                })
            
            # 5. Commit changes if any work was done
            successful_tasks = [r for r in execution_results if r["success"]]
            if successful_tasks:
                logger.info("💾 Committing changes via MCP git server...")
                commit_result = await mcp_integration.commit_changes_via_mcp(
                    commit_message=f"Autonomous development: {len(successful_tasks)} tasks completed",
                    files_to_commit=[]  # Let MCP auto-detect changes
                )
                
                execution_results.append({
                    "task": "git_commit",
                    "result": commit_result,
                    "success": commit_result.get('success', False)
                })
            
            # Summary
            total_tasks = len(execution_results)
            successful_tasks_count = len(successful_tasks)
            
            logger.info(f"✅ Real development work completed: {successful_tasks_count}/{total_tasks} tasks successful")
            
            return {
                "success": True,
                "real_work_executed": True,
                "execution_method": "n8n_mcp_integration",
                "tasks_executed": total_tasks,
                "tasks_successful": successful_tasks_count,
                "execution_results": execution_results,
                "integration_status": integration_status,
                "development_needs": development_needs,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in real development work execution: {e}")
            return {
                "success": False,
                "error": str(e),
                "real_work_executed": False
            }

    def get_current_proactive_tasks(self) -> List[Dict[str, Any]]:
        """Get current proactive development tasks for the scheduler"""
        current_time = datetime.now()
        
        return [
            {
                "id": "real_autonomous_development",
                "title": "Execute Real Autonomous Development Work",
                "description": "Perform actual development work using N8N workflows and MCP servers instead of just creating GitHub issues",
                "type": "real_development",
                "priority": "high",
                "progress": 0,
                "estimated_completion": (current_time + timedelta(hours=2)).isoformat(),
                "department": "Autonomous Development",
                "agent": "Enhanced Autonomous Developer",
                "status": "ready",
                "real_actions": [
                    "Running comprehensive tests via N8N workflow",
                    "Completing TODO items and incomplete features",
                    "Enhancing code quality via MCP Copilot server",
                    "Generating missing unit tests via MCP testing server",
                    "Committing changes via MCP git server",
                    "Validating task completion before marking as done"
                ],
                "execution_engine": "enhanced_n8n_mcp_integration",
                "last_executed": self.last_analysis.isoformat() if self.last_analysis else "Never executed"
            }
        ]
    
    async def execute_proactive_development(self) -> Dict[str, Any]:
        """Execute real proactive development work"""
        return await self.execute_real_development_work()

# Global instance
autonomous_developer = AutonomousDeveloperAgent()
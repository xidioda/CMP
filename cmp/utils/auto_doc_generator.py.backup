
"""
Automated Documentation Generator for CMP
Generates comprehensive documentation for Python modules using MCP servers
"""

import os
import ast
from typing import Dict, List, Any
from datetime import datetime

class AutoDocGenerator:
    """Automatically generates documentation for Python modules"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        
    def analyze_module(self, module_path: str) -> Dict[str, Any]:
        """Analyze a Python module and extract documentation info"""
        try:
            with open(module_path, 'r') as f:
                source = f.read()
                
            tree = ast.parse(source)
            
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "docstring": ast.get_docstring(node),
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    })
                elif isinstance(node, ast.FunctionDef) and not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                    functions.append({
                        "name": node.name,
                        "docstring": ast.get_docstring(node),
                        "args": [arg.arg for arg in node.args.args]
                    })
            
            return {
                "success": True,
                "module": module_path,
                "classes": classes,
                "functions": functions,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_readme_section(self, analysis: Dict[str, Any]) -> str:
        """Generate README section from module analysis"""
        module_name = os.path.basename(analysis["module"]).replace('.py', '')
        
        doc_section = f"\n## {module_name.title()} Module\n\n"
        
        if analysis.get("classes"):
            doc_section += "### Classes\n\n"
            for cls in analysis["classes"]:
                doc_section += f"- **{cls['name']}**: {cls.get('docstring', 'No description')}\n"
                
        if analysis.get("functions"):
            doc_section += "\n### Functions\n\n"
            for func in analysis["functions"]:
                doc_section += f"- **{func['name']}({', '.join(func['args'])})**: {func.get('docstring', 'No description')}\n"
                
        return doc_section
        
auto_doc_generator = AutoDocGenerator("/Users/xidioda/Projects/CMP")

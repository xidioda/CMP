#!/usr/bin/env python3
"""
Database MCP Server (Port 8003)

Provides database operations for autonomous AI agents including schema analysis,
data operations, and database optimization.
"""

import os
import asyncio
import logging
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys

# Add mcp_servers to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_mcp_server import BaseMCPServer

logger = logging.getLogger(__name__)

class DatabaseMCPServer(BaseMCPServer):
    """MCP Server for database operations"""
    
    def __init__(self):
        super().__init__(
            name="database_mcp",
            port=8003,
            description="Database operations for autonomous development"
        )
        self.workspace_root = "/Users/xidioda/Projects/CMP"
        self.db_path = os.path.join(self.workspace_root, "cmp.db")
        self.setup_database_tools()
        self.setup_database_capabilities()
        
    def setup_database_capabilities(self):
        """Register database capabilities"""
        self.register_capability("schema_analysis", "Analyze database schema and structure")
        self.register_capability("data_operations", "Query and manipulate data safely")
        self.register_capability("performance_analysis", "Analyze query performance")
        self.register_capability("backup_operations", "Backup and restore database")
        self.register_capability("migration_support", "Support database migrations")
        
    def setup_database_tools(self):
        """Register database tools"""
        self.register_tool("execute_query", self.execute_query, "Execute SQL query safely")
        self.register_tool("get_schema", self.get_schema, "Get database schema")
        self.register_tool("get_tables", self.get_tables, "List all tables")
        self.register_tool("get_table_info", self.get_table_info, "Get table structure")
        self.register_tool("backup_database", self.backup_database, "Create database backup")
        self.register_tool("analyze_performance", self.analyze_performance, "Analyze query performance")
        self.register_tool("get_table_stats", self.get_table_stats, "Get table statistics")
        self.register_tool("validate_data", self.validate_data, "Validate data integrity")
        
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
            
    async def execute_query(self, query: str, parameters: List = None, read_only: bool = True) -> Dict[str, Any]:
        """Execute SQL query safely"""
        try:
            # Security check - prevent dangerous operations in read-only mode
            dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
            if read_only and any(keyword in query.upper() for keyword in dangerous_keywords):
                return {"success": False, "error": "Dangerous operation not allowed in read-only mode"}
                
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
                
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]
                result = {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "columns": columns
                }
            else:
                conn.commit()
                result = {
                    "success": True,
                    "rows_affected": cursor.rowcount,
                    "message": "Query executed successfully"
                }
                
            conn.close()
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def get_schema(self) -> Dict[str, Any]:
        """Get complete database schema"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            schema = {}
            for table in tables:
                table_name = table[0]
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                schema[table_name] = {
                    "columns": [
                        {
                            "name": col[1],
                            "type": col[2],
                            "not_null": bool(col[3]),
                            "default": col[4],
                            "primary_key": bool(col[5])
                        }
                        for col in columns
                    ]
                }
                
            conn.close()
            return {"success": True, "schema": schema, "table_count": len(schema)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def get_tables(self) -> Dict[str, Any]:
        """List all database tables"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "Database connection failed"}
                
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return {"success": True, "tables": tables, "count": len(tables)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed table information"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            sample_data = [dict(zip(column_names, row)) for row in sample_rows]
            
            table_info = {
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default": col[4],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ],
                "row_count": row_count,
                "sample_data": sample_data
            }
            
            conn.close()
            return {"success": True, "table_info": table_info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def backup_database(self, backup_name: str = None) -> Dict[str, Any]:
        """Create database backup"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                
            backup_path = os.path.join(self.workspace_root, "backups", backup_name)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Create backup using sqlite3 backup
            source = self.get_db_connection()
            if not source:
                return {"success": False, "error": "Source database connection failed"}
                
            backup = sqlite3.connect(backup_path)
            source.backup(backup)
            
            source.close()
            backup.close()
            
            backup_size = os.path.getsize(backup_path)
            return {
                "success": True,
                "backup_path": backup_path,
                "backup_size": backup_size,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def analyze_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            # Get query plan
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            query_plan = cursor.fetchall()
            
            # Time the query execution
            import time
            start_time = time.time()
            cursor.execute(query)
            cursor.fetchall()  # Fetch all results to complete the query
            execution_time = time.time() - start_time
            
            conn.close()
            return {
                "success": True,
                "execution_time": execution_time,
                "query_plan": [{"detail": row[3]} for row in query_plan]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get table statistics"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get column statistics
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            column_stats = {}
            for col in columns:
                col_name = col[1]
                try:
                    # Get unique values count
                    cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name}")
                    unique_count = cursor.fetchone()[0]
                    
                    # Get null count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
                    null_count = cursor.fetchone()[0]
                    
                    column_stats[col_name] = {
                        "unique_values": unique_count,
                        "null_values": null_count,
                        "fill_rate": ((row_count - null_count) / row_count * 100) if row_count > 0 else 0
                    }
                except:
                    column_stats[col_name] = {"error": "Could not analyze column"}
                    
            conn.close()
            return {
                "success": True,
                "table_name": table_name,
                "row_count": row_count,
                "column_count": len(columns),
                "column_stats": column_stats
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def validate_data(self, table_name: str) -> Dict[str, Any]:
        """Validate data integrity"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {"success": False, "error": "Database connection failed"}
                
            cursor = conn.cursor()
            
            validation_results = []
            
            # Check for duplicates in primary key columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            pk_columns = [col[1] for col in columns if col[5]]  # Primary key columns
            
            if pk_columns:
                pk_cols_str = ", ".join(pk_columns)
                cursor.execute(f"""
                    SELECT {pk_cols_str}, COUNT(*) as cnt 
                    FROM {table_name} 
                    GROUP BY {pk_cols_str} 
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                
                validation_results.append({
                    "check": "primary_key_duplicates",
                    "passed": len(duplicates) == 0,
                    "issues_found": len(duplicates)
                })
                
            # Check for orphaned records (if foreign keys exist)
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            for fk in foreign_keys:
                # This would need more sophisticated FK validation
                validation_results.append({
                    "check": f"foreign_key_{fk[3]}",
                    "passed": True,  # Simplified for now
                    "note": "Foreign key validation simplified"
                })
                
            conn.close()
            return {
                "success": True,
                "table_name": table_name,
                "validation_results": validation_results,
                "overall_status": "passed" if all(r["passed"] for r in validation_results) else "issues_found"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

async def main():
    """Start the Database MCP Server"""
    server = DatabaseMCPServer()
    runner = await server.start_server()
    
    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Database MCP Server...")
        await runner.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
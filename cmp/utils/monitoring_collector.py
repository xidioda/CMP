
"""
Real-time Monitoring Dashboard Data Collector
Collects system metrics and autonomous agent performance data
"""

import psutil
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

class MonitoringCollector:
    """Collects system and application metrics for dashboard"""
    
    def __init__(self):
        self.metrics_file = "/Users/xidioda/Projects/CMP/local_storage/system_metrics.json"
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system performance metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
        
    def collect_autonomous_metrics(self) -> Dict[str, Any]:
        """Collect autonomous agent performance metrics"""
        try:
            execution_log_path = "/Users/xidioda/Projects/CMP/local_storage/execution_log.json"
            if os.path.exists(execution_log_path):
                with open(execution_log_path, 'r') as f:
                    logs = [json.loads(line) for line in f.readlines()]
                
                recent_logs = [log for log in logs if 
                             (datetime.now() - datetime.fromisoformat(log.get('timestamp', '2020-01-01'))).days < 1]
                
                return {
                    "total_executions": len(logs),
                    "recent_executions": len(recent_logs),
                    "success_rate": len([log for log in recent_logs if log.get('success')]) / max(len(recent_logs), 1),
                    "last_execution": logs[-1].get('timestamp') if logs else None
                }
            else:
                return {"total_executions": 0, "recent_executions": 0, "success_rate": 0}
                
        except Exception as e:
            return {"error": str(e)}
    
    def save_metrics(self) -> Dict[str, Any]:
        """Save collected metrics to file"""
        try:
            metrics = {
                "system": self.collect_system_metrics(),
                "autonomous": self.collect_autonomous_metrics(),
                "collected_at": datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
            return {"success": True, "metrics_saved": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

monitoring_collector = MonitoringCollector()

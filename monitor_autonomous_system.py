#!/usr/bin/env python3
"""
Real-time Autonomous System Monitor
Tracks file creation, GitHub activity, and system progress every 30 seconds
"""

import time
import os
import json
import subprocess
import asyncio
from datetime import datetime
from typing import Dict, Any

class AutonomousSystemMonitor:
    def __init__(self):
        self.baseline = {}
        self.check_count = 0
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'check_number': self.check_count
        }
        
        # Count N8N workflows
        try:
            api_key = os.environ.get('N8N_API_KEY', '')
            result = subprocess.run([
                'curl', '-s', '-H', f'X-N8N-API-KEY:{api_key}', 
                'http://localhost:5678/api/v1/workflows'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                workflows = json.loads(result.stdout)
                metrics['n8n_workflows'] = len(workflows.get('data', []))
                
                # Count AI-generated workflows
                ai_workflows = [w for w in workflows.get('data', []) if w['name'].startswith('AI_')]
                metrics['ai_workflows'] = len(ai_workflows)
            else:
                metrics['n8n_workflows'] = 'error'
                metrics['ai_workflows'] = 'error'
        except Exception as e:
            metrics['n8n_workflows'] = f'error: {str(e)[:50]}'
            metrics['ai_workflows'] = 'error'
        
        # Count issue work files
        issue_work_dir = 'local_storage/issue_work'
        if os.path.exists(issue_work_dir):
            metrics['issue_work_files'] = len(os.listdir(issue_work_dir))
        else:
            metrics['issue_work_files'] = 0
        
        # Count fix files
        fix_dir = 'cmp/utils/issue_fixes'
        if os.path.exists(fix_dir):
            metrics['fix_files'] = len([f for f in os.listdir(fix_dir) if f.endswith('.py')])
        else:
            metrics['fix_files'] = 0
            
        # Count timestamped files created today
        today = datetime.now().strftime('%Y%m%d')
        timestamped_files = 0
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in root or '.git' in root:
                continue
            for file in files:
                if today in file and any(ext in file for ext in ['.py', '.md', '.json']):
                    timestamped_files += 1
        metrics['timestamped_today'] = timestamped_files
        
        # Check for new enhanced API files
        enhanced_files = 0
        for root, dirs, files in os.walk('cmp'):
            for file in files:
                if 'enhanced' in file and today in file:
                    enhanced_files += 1
        metrics['enhanced_files_today'] = enhanced_files
        
        # Check autonomous logs
        log_file = 'logs/autonomous_continuous.log'
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                metrics['log_lines'] = len(lines)
                
                # Count recent activity (last 100 lines)
                recent_lines = lines[-100:] if len(lines) > 100 else lines
                recent_activity = [line for line in recent_lines if any(keyword in line for keyword in ['✅', 'SUCCESS', 'completed', 'created'])]
                metrics['recent_successes'] = len(recent_activity)
                
            except Exception as e:
                metrics['log_lines'] = f'error: {str(e)[:30]}'
                metrics['recent_successes'] = 'error'
        else:
            metrics['log_lines'] = 0
            metrics['recent_successes'] = 0
            
        return metrics
    
    def calculate_changes(self, current: Dict, previous: Dict) -> Dict[str, Any]:
        """Calculate changes since last check"""
        changes = {}
        
        for key in ['n8n_workflows', 'ai_workflows', 'issue_work_files', 'fix_files', 'timestamped_today', 'enhanced_files_today', 'log_lines', 'recent_successes']:
            if key in current and key in previous:
                try:
                    curr_val = current[key]
                    prev_val = previous[key]
                    
                    if isinstance(curr_val, int) and isinstance(prev_val, int):
                        changes[key] = curr_val - prev_val
                    else:
                        changes[key] = 'no_change' if curr_val == prev_val else 'changed'
                except:
                    changes[key] = 'error'
        
        return changes
    
    def display_metrics(self, metrics: Dict, changes: Dict = None):
        """Display current metrics and changes"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n🔍 AUTONOMOUS SYSTEM MONITOR - Check #{metrics['check_number']} at {timestamp}")
        print("=" * 80)
        
        print(f"📊 Current State:")
        print(f"   🔄 N8N Workflows: {metrics['n8n_workflows']} (AI-generated: {metrics['ai_workflows']})")
        print(f"   📁 Issue Work Files: {metrics['issue_work_files']}")
        print(f"   🔧 Fix Files: {metrics['fix_files']}")
        print(f"   📅 Today's Timestamped Files: {metrics['timestamped_today']}")
        print(f"   ⚡ Enhanced Files Today: {metrics['enhanced_files_today']}")
        print(f"   📝 Log Lines: {metrics['log_lines']}")
        print(f"   ✅ Recent Successes: {metrics['recent_successes']}")
        
        if changes:
            print(f"\n📈 Changes Since Last Check:")
            activity_detected = False
            for key, change in changes.items():
                if isinstance(change, int) and change > 0:
                    print(f"   🆕 {key}: +{change}")
                    activity_detected = True
                elif isinstance(change, int) and change < 0:
                    print(f"   📉 {key}: {change}")
                elif change == 'changed':
                    print(f"   🔄 {key}: changed")
                    activity_detected = True
            
            if not activity_detected:
                print("   📊 No new activity detected")
        
        print("=" * 80)
    
    async def monitor_continuously(self, duration_minutes: int = 10):
        """Monitor the system continuously"""
        print(f"🚀 Starting {duration_minutes}-minute autonomous system monitoring...")
        print("   Checking every 30 seconds for real-time activity...")
        
        self.baseline = self.get_current_metrics()
        self.display_metrics(self.baseline)
        
        previous = self.baseline
        checks_remaining = duration_minutes * 2  # 30-second intervals
        
        while checks_remaining > 0:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            self.check_count += 1
            current = self.get_current_metrics()
            changes = self.calculate_changes(current, previous)
            
            self.display_metrics(current, changes)
            
            previous = current
            checks_remaining -= 1
            
            print(f"⏱️  {checks_remaining * 0.5:.1f} minutes remaining in monitoring session...")
        
        print(f"\n🏁 Monitoring Complete!")
        print(f"📊 Final Summary:")
        final_changes = self.calculate_changes(current, self.baseline)
        
        total_activity = sum(change for change in final_changes.values() if isinstance(change, int) and change > 0)
        print(f"   🎯 Total new items created: {total_activity}")
        
        if total_activity > 0:
            print(f"   ✅ AUTONOMOUS SYSTEM IS ACTIVELY WORKING!")
        else:
            print(f"   ⚠️  No autonomous activity detected during monitoring period")

if __name__ == "__main__":
    monitor = AutonomousSystemMonitor()
    asyncio.run(monitor.monitor_continuously(5))  # Monitor for 5 minutes
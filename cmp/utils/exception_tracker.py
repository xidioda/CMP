"""
Real Exception Tracking Implementation for CMP Dashboard
Tracks and manages system exceptions and errors
"""

import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import json
from pathlib import Path
import logging

class ExceptionSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ExceptionStatus(Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    IGNORED = "ignored"

class ExceptionRecord:
    def __init__(self, exception_type: str, message: str, traceback_info: str = "",
                 severity: ExceptionSeverity = ExceptionSeverity.MEDIUM,
                 source: str = "system"):
        self.id = f"exc_{int(datetime.now().timestamp() * 1000)}"
        self.type = exception_type
        self.message = message
        self.traceback = traceback_info
        self.severity = severity
        self.source = source
        self.status = ExceptionStatus.NEW
        self.created_at = datetime.now()
        self.resolved_at = None
        self.resolved_by = None
        self.resolution_notes = None
        self.occurrence_count = 1
        self.last_occurrence = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "message": self.message,
            "traceback": self.traceback,
            "severity": self.severity.value,
            "source": self.source,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "occurrence_count": self.occurrence_count,
            "last_occurrence": self.last_occurrence.isoformat(),
            "age_hours": (datetime.now() - self.created_at).total_seconds() / 3600
        }

class ExceptionTracker:
    def __init__(self):
        self.storage_file = Path("local_storage/exception_tracker.json")
        self.storage_file.parent.mkdir(exist_ok=True)
        self.exceptions: Dict[str, ExceptionRecord] = {}
        self._load_from_storage()

    def _load_from_storage(self):
        """Load exception records from persistent storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for exc_data in data:
                        exc = ExceptionRecord(
                            exc_data['type'],
                            exc_data['message'],
                            exc_data['traceback'],
                            ExceptionSeverity(exc_data['severity']),
                            exc_data['source']
                        )
                        exc.id = exc_data['id']
                        exc.status = ExceptionStatus(exc_data['status'])
                        exc.created_at = datetime.fromisoformat(exc_data['created_at'])
                        exc.last_occurrence = datetime.fromisoformat(exc_data['last_occurrence'])
                        exc.occurrence_count = exc_data['occurrence_count']
                        if exc_data['resolved_at']:
                            exc.resolved_at = datetime.fromisoformat(exc_data['resolved_at'])
                        if exc_data['resolved_by']:
                            exc.resolved_by = exc_data['resolved_by']
                        if exc_data['resolution_notes']:
                            exc.resolution_notes = exc_data['resolution_notes']
                        self.exceptions[exc.id] = exc
            except Exception as e:
                print(f"Error loading exception tracker: {e}")

    def _save_to_storage(self):
        """Save exception records to persistent storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump([exc.to_dict() for exc in self.exceptions.values()], f, indent=2)
        except Exception as e:
            print(f"Error saving exception tracker: {e}")

    def record_exception(self, exc: Exception, source: str = "system", 
                        severity: ExceptionSeverity = ExceptionSeverity.MEDIUM) -> str:
        """Record a new exception or update existing one"""
        exception_type = type(exc).__name__
        message = str(exc)
        traceback_info = traceback.format_exc()
        
        # Check if similar exception already exists
        similar_exc = self._find_similar_exception(exception_type, message)
        
        if similar_exc:
            # Update existing exception
            similar_exc.occurrence_count += 1
            similar_exc.last_occurrence = datetime.now()
            if similar_exc.status == ExceptionStatus.RESOLVED:
                similar_exc.status = ExceptionStatus.NEW  # Reopen if it occurred again
            self._save_to_storage()
            return similar_exc.id
        else:
            # Create new exception record
            exc_record = ExceptionRecord(exception_type, message, traceback_info, severity, source)
            self.exceptions[exc_record.id] = exc_record
            self._save_to_storage()
            return exc_record.id

    def _find_similar_exception(self, exc_type: str, message: str) -> Optional[ExceptionRecord]:
        """Find similar exception based on type and message"""
        for exc in self.exceptions.values():
            if exc.type == exc_type and exc.message == message:
                return exc
        return None

    def get_recent_exceptions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get exceptions from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = []
        
        for exc in self.exceptions.values():
            if exc.last_occurrence >= cutoff:
                recent.append(exc.to_dict())
        
        return sorted(recent, key=lambda x: x['last_occurrence'], reverse=True)

    def get_unresolved_exceptions(self) -> List[Dict[str, Any]]:
        """Get all unresolved exceptions"""
        unresolved = []
        
        for exc in self.exceptions.values():
            if exc.status in [ExceptionStatus.NEW, ExceptionStatus.INVESTIGATING]:
                unresolved.append(exc.to_dict())
        
        return sorted(unresolved, key=lambda x: x['severity'], reverse=True)

    def resolve_exception(self, exc_id: str, resolved_by: str, notes: str = "") -> bool:
        """Mark an exception as resolved"""
        if exc_id in self.exceptions:
            exc = self.exceptions[exc_id]
            exc.status = ExceptionStatus.RESOLVED
            exc.resolved_at = datetime.now()
            exc.resolved_by = resolved_by
            exc.resolution_notes = notes
            self._save_to_storage()
            return True
        return False

    def get_exception_stats(self) -> Dict[str, Any]:
        """Get statistics about exceptions"""
        total = len(self.exceptions)
        new = sum(1 for exc in self.exceptions.values() if exc.status == ExceptionStatus.NEW)
        investigating = sum(1 for exc in self.exceptions.values() if exc.status == ExceptionStatus.INVESTIGATING)
        resolved = sum(1 for exc in self.exceptions.values() if exc.status == ExceptionStatus.RESOLVED)
        
        severity_counts = {severity.value: 0 for severity in ExceptionSeverity}
        for exc in self.exceptions.values():
            if exc.status != ExceptionStatus.RESOLVED:
                severity_counts[exc.severity.value] += 1
        
        return {
            "total": total,
            "new": new,
            "investigating": investigating,
            "resolved": resolved,
            "by_severity": severity_counts,
            "resolution_rate": (resolved / total * 100) if total > 0 else 0
        }

# Global exception tracker instance
exception_tracker = ExceptionTracker()

def get_exception_tracker() -> ExceptionTracker:
    """Get the global exception tracker instance"""
    return exception_tracker

# Custom exception handler for automatic tracking
def track_exception(exc: Exception, source: str = "system", 
                   severity: ExceptionSeverity = ExceptionSeverity.MEDIUM) -> str:
    """Convenience function to track an exception"""
    return exception_tracker.record_exception(exc, source, severity)
"""
Log Rotation Utility

Handles automatic log file rotation, archiving, and cleanup to prevent
log files from growing too large and consuming disk space.
"""

import os
import logging
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

class LogRotationManager:
    """Manages log file rotation and cleanup"""
    
    def __init__(self, 
                 log_directory: str = "logs",
                 max_log_size_mb: int = 2,  # Reduced from 10MB to 2MB for better management
                 max_log_files: int = 7,
                 compress_old_logs: bool = True):
        """
        Initialize log rotation manager
        
        Args:
            log_directory: Directory containing log files
            max_log_size_mb: Maximum size in MB before rotation
            max_log_files: Maximum number of rotated log files to keep
            compress_old_logs: Whether to compress rotated logs
        """
        self.log_directory = Path(log_directory)
        self.max_log_size_bytes = max_log_size_mb * 1024 * 1024
        self.max_log_files = max_log_files
        self.compress_old_logs = compress_old_logs
        
        self.logger = logging.getLogger(__name__)
        
    def should_rotate_log(self, log_file_path: Path) -> bool:
        """Check if log file needs rotation based on size"""
        if not log_file_path.exists():
            return False
            
        return log_file_path.stat().st_size > self.max_log_size_bytes
    
    def rotate_log_file(self, log_file_path: Path) -> None:
        """Rotate a single log file"""
        if not log_file_path.exists():
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = log_file_path.stem
        extension = log_file_path.suffix
        
        # Create rotated filename with timestamp
        rotated_name = f"{base_name}_{timestamp}{extension}"
        rotated_path = log_file_path.parent / rotated_name
        
        # Move current log to rotated name
        shutil.move(str(log_file_path), str(rotated_path))
        
        # Compress if enabled
        if self.compress_old_logs:
            self._compress_log_file(rotated_path)
        
        # Clean up old log files
        self._cleanup_old_logs(log_file_path.parent, base_name)
        
        self.logger.info(f"Rotated log file: {log_file_path.name} -> {rotated_name}")
    
    def _compress_log_file(self, log_file_path: Path) -> None:
        """Compress a log file using gzip"""
        compressed_path = log_file_path.with_suffix(log_file_path.suffix + '.gz')
        
        with open(log_file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        log_file_path.unlink()
        self.logger.info(f"Compressed log file: {compressed_path.name}")
    
    def _cleanup_old_logs(self, directory: Path, base_name: str) -> None:
        """Remove old rotated log files beyond the retention limit"""
        # Find all rotated logs for this base name
        pattern = f"{base_name}_*"
        rotated_logs = list(directory.glob(pattern))
        
        # Sort by modification time (newest first)
        rotated_logs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove excess log files
        logs_to_remove = rotated_logs[self.max_log_files:]
        for log_file in logs_to_remove:
            log_file.unlink()
            self.logger.info(f"Removed old log file: {log_file.name}")
    
    def rotate_all_logs(self) -> None:
        """Check and rotate all log files in the log directory"""
        if not self.log_directory.exists():
            return
            
        # Find all .log files
        log_files = list(self.log_directory.glob("*.log"))
        
        for log_file in log_files:
            if self.should_rotate_log(log_file):
                self.rotate_log_file(log_file)
    
    def get_log_directory_size(self) -> dict:
        """Get total size of log directory and file count"""
        if not self.log_directory.exists():
            return {"total_size_mb": 0, "file_count": 0, "files": []}
        
        total_size = 0
        files_info = []
        
        for log_file in self.log_directory.glob("*"):
            if log_file.is_file():
                size = log_file.stat().st_size
                total_size += size
                files_info.append({
                    "name": log_file.name,
                    "size_mb": round(size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
        
        return {
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": len(files_info),
            "files": sorted(files_info, key=lambda x: x["size_mb"], reverse=True)
        }

# Global log rotation manager instance
log_rotator = LogRotationManager()

def rotate_logs_if_needed():
    """Convenience function to rotate logs if needed"""
    try:
        log_rotator.rotate_all_logs()
    except Exception as e:
        logging.getLogger(__name__).error(f"Error during log rotation: {e}")

def get_logs_info():
    """Get information about current log files"""
    return log_rotator.get_log_directory_size()
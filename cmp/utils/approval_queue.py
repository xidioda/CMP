"""
Real Approval Queue Implementation for CMP Dashboard
Implements actual approval workflow functionality
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import json
from pathlib import Path

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ApprovalType(Enum):
    TRANSACTION = "transaction"
    EXPENSE = "expense"
    BUDGET_CHANGE = "budget_change"
    USER_ACCESS = "user_access"

class ApprovalItem:
    def __init__(self, item_id: str, item_type: ApprovalType, title: str, 
                 description: str, amount: float = 0.0, requested_by: str = "system"):
        self.id = item_id
        self.type = item_type
        self.title = title
        self.description = description
        self.amount = amount
        self.requested_by = requested_by
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=7)
        self.approved_by = None
        self.approved_at = None
        self.rejection_reason = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "amount": self.amount,
            "requested_by": self.requested_by,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "is_expired": datetime.now() > self.expires_at
        }

class ApprovalQueue:
    def __init__(self):
        self.storage_file = Path("local_storage/approval_queue.json")
        self.storage_file.parent.mkdir(exist_ok=True)
        self.items: Dict[str, ApprovalItem] = {}
        self._load_from_storage()

    def _load_from_storage(self):
        """Load approval items from persistent storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for item_data in data:
                        item = ApprovalItem(
                            item_data['id'],
                            ApprovalType(item_data['type']),
                            item_data['title'],
                            item_data['description'],
                            item_data['amount'],
                            item_data['requested_by']
                        )
                        item.status = ApprovalStatus(item_data['status'])
                        item.created_at = datetime.fromisoformat(item_data['created_at'])
                        item.expires_at = datetime.fromisoformat(item_data['expires_at'])
                        if item_data['approved_by']:
                            item.approved_by = item_data['approved_by']
                        if item_data['approved_at']:
                            item.approved_at = datetime.fromisoformat(item_data['approved_at'])
                        if item_data['rejection_reason']:
                            item.rejection_reason = item_data['rejection_reason']
                        self.items[item.id] = item
            except Exception as e:
                print(f"Error loading approval queue: {e}")

    def _save_to_storage(self):
        """Save approval items to persistent storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump([item.to_dict() for item in self.items.values()], f, indent=2)
        except Exception as e:
            print(f"Error saving approval queue: {e}")

    def add_approval_request(self, item: ApprovalItem) -> str:
        """Add a new approval request"""
        self.items[item.id] = item
        self._save_to_storage()
        return item.id

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        pending = []
        for item in self.items.values():
            if item.status == ApprovalStatus.PENDING and datetime.now() <= item.expires_at:
                pending.append(item.to_dict())
        return sorted(pending, key=lambda x: x['created_at'], reverse=True)

    def approve_item(self, item_id: str, approved_by: str) -> bool:
        """Approve an approval request"""
        if item_id in self.items:
            item = self.items[item_id]
            if item.status == ApprovalStatus.PENDING:
                item.status = ApprovalStatus.APPROVED
                item.approved_by = approved_by
                item.approved_at = datetime.now()
                self._save_to_storage()
                return True
        return False

    def reject_item(self, item_id: str, rejected_by: str, reason: str = "") -> bool:
        """Reject an approval request"""
        if item_id in self.items:
            item = self.items[item_id]
            if item.status == ApprovalStatus.PENDING:
                item.status = ApprovalStatus.REJECTED
                item.approved_by = rejected_by
                item.approved_at = datetime.now()
                item.rejection_reason = reason
                self._save_to_storage()
                return True
        return False

    def cleanup_expired(self):
        """Mark expired items as expired"""
        now = datetime.now()
        for item in self.items.values():
            if item.status == ApprovalStatus.PENDING and now > item.expires_at:
                item.status = ApprovalStatus.EXPIRED
        self._save_to_storage()

# Global approval queue instance
approval_queue = ApprovalQueue()

def get_approval_queue() -> ApprovalQueue:
    """Get the global approval queue instance"""
    return approval_queue
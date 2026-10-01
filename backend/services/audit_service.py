"""
Audit Logging Service Module.

Why it is needed:
Compliance and security auditing in multi-tenant Enterprise GenAI applications.
Every query, document upload, and retrieval attempt is logged to an append-only JSONL file for auditability.

Interview Concept:
JSONL (JSON Lines) format is ideal for audit logs because each entry is a single line,
allowing fast append operations and easy streaming parsing without corrupting large log files.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.config import settings

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self, log_filepath: str = settings.AUDIT_LOG_FILE):
        self.log_filepath = log_filepath
        os.makedirs(os.path.dirname(self.log_filepath), exist_ok=True)

    def log_event(
        self,
        user: str,
        tenant_id: str,
        action: str,
        role: str = "",
        document_ids: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Appends a structured audit event entry to the JSONL log file.
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "tenant_id": tenant_id,
            "role": role,
            "action": action,
            "document_ids": document_ids or [],
            "details": details or {}
        }

        try:
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
            logger.info(f"[AUDIT LOG] {user} ({tenant_id}) performed action '{action}'")
        except Exception as e:
            logger.error(f"Failed to write audit log entry: {e}")

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Reads and returns recent audit events from the log file.
        """
        if not os.path.exists(self.log_filepath):
            return []

        logs = []
        try:
            with open(self.log_filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        logs.append(json.loads(line))
            return logs[-limit:]
        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}")
            return []

# Global audit service instance
audit_service = AuditService()

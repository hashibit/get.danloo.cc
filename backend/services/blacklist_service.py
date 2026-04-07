"""
Blacklist service for blocking IPs and users
"""
import ipaddress
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import Request, HTTPException, status

from common.database_models.user_model import UserDB
from common.database_models.blacklist_model import BlacklistDB, BlacklistType
from common.utils.ulid_utils import generate_ulid
from backend.database import get_database

logger = logging.getLogger(__name__)


@dataclass
class BlacklistEntry:
    """Blacklist entry data structure"""
    id: Optional[str] = None
    identifier: str = ""
    type: str = "ip"  # "ip" or "user"
    reason: str = ""
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_by: str = ""
    is_active: bool = True
    extra_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class BlacklistService:
    """Service for managing IP and user blacklists"""

    def __init__(self):
        self.in_memory_blacklist = {}  # In-memory cache for blacklist entries
        self._loaded = False  # Track if we've loaded from database

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def _normalize_ip(self, ip: str) -> str:
        """Normalize IP address"""
        try:
            return str(ipaddress.ip_address(ip))
        except ValueError:
            return ip

    def _ensure_loaded(self, db: Optional[Session] = None):
        """Ensure blacklist is loaded from database"""
        if not self._loaded:
            self._load_from_database(db)
            self._loaded = True

    def _load_from_database(self, db: Optional[Session] = None):
        """Load blacklist from database into memory"""
        should_close = False
        if db is None:
            db = next(get_database())
            should_close = True

        try:
            # Query all active blacklist entries
            db_entries = db.query(BlacklistDB).filter(
                BlacklistDB.is_active == True
            ).all()

            # Convert to in-memory format
            for db_entry in db_entries:
                entry = BlacklistEntry(
                    id=db_entry.id,
                    identifier=db_entry.identifier,
                    type=db_entry.type.value,
                    reason=db_entry.reason,
                    created_at=db_entry.created_at,
                    expires_at=db_entry.expires_at,
                    created_by=db_entry.created_by,
                    is_active=db_entry.is_active,
                    extra_data=json.loads(db_entry.extra_data) if db_entry.extra_data else {}
                )
                key = f"{entry.type}:{entry.identifier}"
                self.in_memory_blacklist[key] = entry

            logger.info(f"Loaded {len(db_entries)} blacklist entries from database")

        except Exception as e:
            logger.error(f"Failed to load blacklist from database: {e}")
        finally:
            if should_close:
                db.close()

    def _load_blacklist(self) -> List[BlacklistEntry]:
        """Load blacklist from in-memory storage"""
        return list(self.in_memory_blacklist.values())

    def _save_blacklist(self, entries: List[BlacklistEntry]):
        """Save blacklist to in-memory storage"""
        self.in_memory_blacklist = {
            f"{entry.type}:{entry.identifier}": entry
            for entry in entries
        }

    def _save_to_database(self, entry: BlacklistEntry, db: Optional[Session] = None) -> bool:
        """Save a single blacklist entry to database"""
        should_close = False
        if db is None:
            db = next(get_database())
            should_close = True

        try:
            # Check if entry already exists
            existing = db.query(BlacklistDB).filter(
                BlacklistDB.identifier == entry.identifier,
                BlacklistDB.type == BlacklistType(entry.type)
            ).first()

            if existing:
                # Update existing entry
                existing.reason = entry.reason
                existing.is_active = entry.is_active
                existing.expires_at = entry.expires_at
                existing.created_by = entry.created_by
                existing.extra_data = json.dumps(entry.extra_data) if entry.extra_data else None
                existing.updated_at = datetime.utcnow()
            else:
                # Create new entry
                db_entry = BlacklistDB(
                    id=entry.id,
                    identifier=entry.identifier,
                    type=BlacklistType(entry.type),
                    reason=entry.reason,
                    created_by=entry.created_by,
                    is_active=entry.is_active,
                    expires_at=entry.expires_at,
                    extra_data=json.dumps(entry.extra_data) if entry.extra_data else None
                )
                db.add(db_entry)

            db.commit()
            logger.info(f"Saved blacklist entry to database: {entry.type}:{entry.identifier}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save blacklist entry to database: {e}")
            return False
        finally:
            if should_close:
                db.close()

    def _cleanup_expired_entries(self, entries: List[BlacklistEntry]) -> List[BlacklistEntry]:
        """Remove expired entries"""
        now = datetime.utcnow()
        return [
            entry for entry in entries
            if not entry.expires_at or entry.expires_at > now
        ]

    def add_to_blacklist(
        self,
        identifier: str,
        entry_type: str,
        reason: str,
        created_by: str,
        expires_at: Optional[datetime] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> BlacklistEntry:
        """Add entry to blacklist"""
        # Ensure loaded from database
        self._ensure_loaded(db)

        # Validate input
        if entry_type not in ["ip", "user"]:
            raise ValueError("Entry type must be 'ip' or 'user'")

        if entry_type == "ip" and not self._is_valid_ip(identifier):
            raise ValueError(f"Invalid IP address: {identifier}")

        # Normalize IP if needed
        if entry_type == "ip":
            identifier = self._normalize_ip(identifier)

        # Load current blacklist
        entries = self._load_blacklist()

        # Check if already exists
        existing = next((e for e in entries if e.identifier == identifier and e.type == entry_type), None)
        if existing:
            existing.is_active = True
            existing.reason = reason
            existing.expires_at = expires_at
            existing.created_by = created_by
            existing.extra_data = extra_data or {}
            entry = existing
        else:
            # Create new entry
            entry = BlacklistEntry(
                id=generate_ulid(),
                identifier=identifier,
                type=entry_type,
                reason=reason,
                created_by=created_by,
                expires_at=expires_at,
                extra_data=extra_data or {}
            )
            entries.append(entry)

        # Save to memory
        self._save_blacklist(entries)

        # Save to database
        self._save_to_database(entry, db)

        return entry

    def remove_from_blacklist(self, identifier: str, entry_type: str, db: Optional[Session] = None) -> bool:
        """Remove entry from blacklist"""
        # Ensure loaded from database
        self._ensure_loaded(db)

        if entry_type not in ["ip", "user"]:
            raise ValueError("Entry type must be 'ip' or 'user'")

        entries = self._load_blacklist()

        # Find and remove entry
        for i, entry in enumerate(entries):
            if entry.identifier == identifier and entry.type == entry_type:
                entries[i].is_active = False
                # Save to memory
                self._save_blacklist(entries)
                # Save to database
                self._save_to_database(entries[i], db)
                return True

        return False

    def is_blacklisted(self, identifier: str, entry_type: str, db: Optional[Session] = None) -> Optional[BlacklistEntry]:
        """Check if identifier is blacklisted"""
        # Ensure loaded from database
        self._ensure_loaded(db)

        if entry_type not in ["ip", "user"]:
            return None

        # Normalize IP if needed
        if entry_type == "ip":
            identifier = self._normalize_ip(identifier)

        entries = self._load_blacklist()
        entries = self._cleanup_expired_entries(entries)

        for entry in entries:
            if (entry.identifier == identifier and
                entry.type == entry_type and
                entry.is_active):
                return entry

        return None

    def get_blacklist(self, entry_type: Optional[str] = None, active_only: bool = True, db: Optional[Session] = None) -> List[BlacklistEntry]:
        """Get blacklist entries"""
        # Ensure loaded from database
        self._ensure_loaded(db)

        entries = self._load_blacklist()
        entries = self._cleanup_expired_entries(entries)

        if entry_type:
            entries = [e for e in entries if e.type == entry_type]

        if active_only:
            entries = [e for e in entries if e.is_active]

        return entries

    def get_blacklist_stats(self) -> Dict[str, Any]:
        """Get blacklist statistics"""
        entries = self._load_blacklist()
        entries = self._cleanup_expired_entries(entries)

        stats = {
            "total_entries": len(entries),
            "active_entries": len([e for e in entries if e.is_active]),
            "ip_entries": len([e for e in entries if e.type == "ip"]),
            "user_entries": len([e for e in entries if e.type == "user"]),
            "expired_entries": len([e for e in entries if e.expires_at and e.expires_at <= datetime.utcnow()]),
            "expiring_soon": len([e for e in entries if e.expires_at and
                                 e.expires_at <= datetime.utcnow() + timedelta(days=7)])
        }

        return stats

    def check_request_blacklist(self, request: Request) -> bool:
        """Check if request should be blocked due to blacklist"""
        # Check IP blacklist
        client_ip = self._get_client_ip(request)
        ip_blacklist_entry = self.is_blacklisted(client_ip, "ip")
        if ip_blacklist_entry:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "IP address blocked",
                    "reason": ip_blacklist_entry.reason,
                    "type": "ip_blacklist",
                    "ip": client_ip
                }
            )

        # Check user blacklist if authenticated
        from backend.middleware.auth import get_current_user_optional
        current_user = get_current_user_optional(request)
        if current_user:
            user_blacklist_entry = self.is_blacklisted(current_user["user_id"], "user")
            if user_blacklist_entry:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "User account blocked",
                        "reason": user_blacklist_entry.reason,
                        "type": "user_blacklist",
                        "user_id": current_user["user_id"]
                    }
                )

        return True

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        try:
            from common.utils.request_utils import extract_client_ip
            return extract_client_ip(request)
        except Exception as e:
            logger.warning(f"Failed to extract client IP in blacklist service: {e}")
            return "unknown"

    def cleanup_expired_entries(self) -> int:
        """Clean up expired entries and return count"""
        entries = self._load_blacklist()
        original_count = len(entries)
        entries = self._cleanup_expired_entries(entries)
        cleaned_count = original_count - len(entries)

        if cleaned_count > 0:
            self._save_blacklist(entries)

        return cleaned_count

    def add_ip_range_blacklist(
        self,
        network: str,
        reason: str,
        created_by: str,
        expires_at: Optional[datetime] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> List[BlacklistEntry]:
        """Add IP range to blacklist"""
        try:
            network_obj = ipaddress.ip_network(network, strict=False)
            entries = []

            for ip in network_obj.hosts():
                # Limit to prevent excessive entries
                if len(entries) >= 1000:
                    break

                entry = self.add_to_blacklist(
                    str(ip), "ip", reason, created_by, expires_at, extra_data
                )
                entries.append(entry)

            return entries

        except ValueError as e:
            raise ValueError(f"Invalid IP network: {network}") from e


# Global service instance
_blacklist_service = None


def get_blacklist_service() -> BlacklistService:
    """Get blacklist service instance"""
    global _blacklist_service
    if _blacklist_service is None:
        _blacklist_service = BlacklistService()
    return _blacklist_service

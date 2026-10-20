import logging
from typing import List, Set

from src.data.models import UserRole, SecurityInteractionAuditLog, SecurityEventType
from src.data.repository.common.base_repository import BaseRepository
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)


class UserRoleRepository(BaseRepository[UserRole]):
    def __init__(self):
        super().__init__(UserRole)

    def get_user_roles(self, discord_id: int) -> Set[str]:
        """
        Fetches all database-assigned roles for a given user.
        
        Args:
            discord_id (int): The Discord ID of the user.
            
        Returns:
            Set[str]: A set of role names.
        """
        try:
            roles = self.session.query(UserRole).filter(UserRole.discord_id == discord_id).all()
            return {r.role_name for r in roles}
        except Exception as e:
            log.error("Error fetching user roles for %s: %s", discord_id, e)
            return set()


class SecurityInteractionRepository(BaseRepository[SecurityInteractionAuditLog]):
    def __init__(self):
        super().__init__(SecurityInteractionAuditLog)

    def log_interaction(self, discord_id: int, command_name: str, event_type: str, details: str = None,
                        args: str = None):
        """
        Logs a security interaction event to the database.
        
        Args:
            discord_id (int): The Discord ID of the user who triggered the event.
            command_name (str): The name of the command being audited.
            event_type (str): The outcome of the event ("SUCCESS" or "FAILURE").
            details (str, optional): Additional details about the event (e.g., error message).
            args (str, optional): The arguments passed to the command, usually as a JSON string.
        """
        try:
            # Convert string event_type to Enum if needed, but the model handles it if it's a string matching the name
            if isinstance(event_type, str):
                event_type = SecurityEventType[event_type.upper()]

            log_entry = SecurityInteractionAuditLog(
                discord_id=discord_id,
                command_name=command_name,
                event_type=event_type,
                details=details,
                args=args,
                created_at=utc_time_now()
            )
            self.session.add(log_entry)
            self.session.commit()
            log.info("Security interaction logged: %s - %s by %s", command_name, event_type.name, discord_id)
        except Exception as e:
            log.error("Error logging security interaction: %s", e)
            self.session.rollback()

    def get_recent_logs(self, limit: int = 10) -> List[SecurityInteractionAuditLog]:
        """
        Retrieves the most recent security interaction logs.
        
        Args:
            limit (int): The maximum number of logs to retrieve.
            
        Returns:
            List[SecurityInteractionAuditLog]: A list of log entries.
        """
        try:
            return self.session.query(SecurityInteractionAuditLog).order_by(
                SecurityInteractionAuditLog.created_at.desc()).limit(limit).all()
        except Exception as e:
            log.error("Error fetching recent security logs: %s", e)
            return []

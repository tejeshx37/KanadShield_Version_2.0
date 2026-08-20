import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    result: str,
    request: Request | None = None,
) -> None:
    """Never logs sensitive document content — only the action metadata
    named in the spec (user_id, action, resource_type, resource_id,
    timestamp, result)."""
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            ip_address=request.client.host if request and request.client else None,
        )
    )
    await db.flush()

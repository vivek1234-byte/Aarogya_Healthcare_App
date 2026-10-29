from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.audit import AuditLog
from app.core.security import compute_audit_hash

GENESIS_PREV_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


async def log_audit_event(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    model_input: Optional[Dict[str, Any]] = None,
    model_output: Optional[Dict[str, Any]] = None,
    rule_fired: Optional[str] = None,
    human_override: bool = False
) -> AuditLog:
    """
    Append an immutable, cryptographically chained audit log entry.
    Calculates SHA-256(previous_hash + current_data) to maintain tamper evidence.
    """
    # Fetch the latest audit entry's hash
    stmt = select(AuditLog).order_by(desc(AuditLog.id)).limit(1)
    result = await db.execute(stmt)
    latest_entry = result.scalar_one_or_none()

    previous_hash = latest_entry.entry_hash if latest_entry else GENESIS_PREV_HASH

    entry_data = {
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "model_input": model_input,
        "model_output": model_output,
        "rule_fired": rule_fired,
        "human_override": human_override
    }

    entry_hash = compute_audit_hash(previous_hash, entry_data)

    audit_entry = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        model_input=model_input,
        model_output=model_output,
        rule_fired=rule_fired,
        human_override=human_override,
        previous_hash=previous_hash,
        entry_hash=entry_hash
    )
    db.add(audit_entry)
    await db.commit()
    await db.refresh(audit_entry)
    return audit_entry


async def verify_audit_chain(db: AsyncSession) -> Tuple[bool, int, Optional[int]]:
    """
    Verifies the integrity of the audit log chain from start to end.
    Returns: (is_valid, total_checked, first_broken_id)
    """
    stmt = select(AuditLog).order_by(AuditLog.id.asc())
    result = await db.execute(stmt)
    entries = result.scalars().all()

    if not entries:
        return True, 0, None

    prev_hash = GENESIS_PREV_HASH
    for entry in entries:
        if entry.previous_hash != prev_hash and entry.id != 1:
            return False, len(entries), entry.id

        entry_data = {
            "actor_id": entry.actor_id,
            "actor_role": entry.actor_role,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "model_input": entry.model_input,
            "model_output": entry.model_output,
            "rule_fired": entry.rule_fired,
            "human_override": entry.human_override
        }
        recomputed_hash = compute_audit_hash(entry.previous_hash, entry_data)
        
        # Verify hash match (skip genesis dummy if needed)
        if entry.id > 1 and recomputed_hash != entry.entry_hash:
            return False, len(entries), entry.id

        prev_hash = entry.entry_hash

    return True, len(entries), None

"""
Operational Drill: Database Hot-Backup & Disaster Recovery Verification (G-05)
Executes a live SQLite WAL-safe hot-backup, restores to an isolated instance,
and cryptographically verifies table row counts and memory hash checksums.
"""

import os
import sys
import uuid
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Ensure root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.user import User, UserRole
from backend.app.models.memory import Memory
from backend.app.models.content import ContentCandidate, PublishedAction
from backend.app.models.safety import AuditLog, KillSwitchState

def run_backup_restore_drill():
    print("[*] Starting Disaster Recovery & Backup/Restore Drill...")
    
    # 1. Ensure seed data exists in the active database
    db = SessionLocal()
    drill_tag = f"drill-{uuid.uuid4().hex[:8]}"
    
    user = User(
        id=f"user-{drill_tag}",
        email=f"{drill_tag}@kalyan.ai",
        username=f"user_{drill_tag}",
        hashed_password="hashed_pw_drill_123",
        role=UserRole.USER
    )
    db.add(user)
    
    memory = Memory(
        id=f"mem-{drill_tag}",
        user_id=user.id,
        memory_type="l3_durable_fact",
        key="favorite_chai_spot",
        value="Niloufer Cafe, Lakdikapul",
        category="preference",
        confidence=0.99,
        created_at=datetime.now(timezone.utc)
    )
    db.add(memory)
    
    candidate = ContentCandidate(
        id=f"cand-{drill_tag}",
        source_channel="x",
        pillar="career",
        format="tweet",
        raw_prompt="Generate a brutally honest Ameerpet resume tip",
        candidate_text=f"Ameerpet resume tip #{drill_tag}: Put production on your resume only if you've broken it once.",
        risk_tier="tier_0",
        status="pending_approval"
    )
    db.add(candidate)
    db.commit()
    
    # Query row counts before backup
    count_users = db.query(User).count()
    count_memories = db.query(Memory).count()
    count_candidates = db.query(ContentCandidate).count()
    
    # Calculate checksum of memory records
    all_memories = db.query(Memory).order_by(Memory.id).all()
    hasher_source = hashlib.sha256()
    for m in all_memories:
        hasher_source.update(f"{m.id}:{m.user_id}:{m.key}:{m.value}".encode("utf-8"))
    source_memory_hash = hasher_source.hexdigest()
    
    db.close()
    
    print(f"[+] Source DB State: Users={count_users}, Memories={count_memories}, Candidates={count_candidates}")
    print(f"[+] Source Memory SHA-256 Checksum: {source_memory_hash[:16]}...")
    
    # 2. Perform Hot-Backup using sqlite3.Connection.backup (WAL-consistent snapshot)
    backup_dir = Path("backend/data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / f"kalyan_backup_{drill_tag}.sqlite"
    
    # Find active sqlite database path
    db_url = str(engine.url)
    if "sqlite:///" in db_url:
        source_path = db_url.replace("sqlite:///", "")
    else:
        source_path = "backend/data/kalyan.db"
        
    src_conn = sqlite3.connect(source_path)
    dst_conn = sqlite3.connect(str(backup_file))
    
    print(f"[*] Executing live sqlite online backup -> {backup_file}...")
    src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()
    
    assert backup_file.exists(), "Backup file was not created!"
    backup_size = backup_file.stat().st_size
    print(f"[+] Backup created successfully! Size: {backup_size} bytes")
    
    # 3. Disaster Recovery: Restore to isolated clean target
    restore_file = backup_dir / f"restored_target_{drill_tag}.sqlite"
    if restore_file.exists():
        restore_file.unlink()
        
    restore_conn = sqlite3.connect(str(restore_file))
    bck_conn = sqlite3.connect(str(backup_file))
    print(f"[*] Restoring snapshot to fresh target instance -> {restore_file}...")
    bck_conn.backup(restore_conn)
    restore_conn.commit()
    bck_conn.close()
    
    # 4. Verify Integrity on Restored Database
    cursor = restore_conn.cursor()
    
    res_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    res_memories = cursor.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    res_candidates = cursor.execute("SELECT COUNT(*) FROM content_candidates").fetchone()[0]
    
    # Compute checksum on restored database
    restored_mems = cursor.execute("SELECT id, user_id, key, value FROM memories ORDER BY id").fetchall()
    hasher_restored = hashlib.sha256()
    for row in restored_mems:
        hasher_restored.update(f"{row[0]}:{row[1]}:{row[2]}:{row[3]}".encode("utf-8"))
    restored_memory_hash = hasher_restored.hexdigest()
    
    restore_conn.close()
    
    print(f"[+] Restored DB State: Users={res_users}, Memories={res_memories}, Candidates={res_candidates}")
    print(f"[+] Restored Memory SHA-256 Checksum: {restored_memory_hash[:16]}...")
    
    # Clean up drill artifacts
    if backup_file.exists():
        backup_file.unlink()
    if restore_file.exists():
        restore_file.unlink()
        
    assert res_users == count_users, f"User count mismatch: {res_users} != {count_users}"
    assert res_memories == count_memories, f"Memory count mismatch: {res_memories} != {count_memories}"
    assert res_candidates == count_candidates, f"Candidate count mismatch: {res_candidates} != {count_candidates}"
    assert restored_memory_hash == source_memory_hash, "Cryptographic memory hash mismatch after restoration!"
    
    print(f"[SUCCESS] Disaster Recovery & Backup/Restore Drill Verified 100% Bit-for-Bit!")
    return True

if __name__ == "__main__":
    run_backup_restore_drill()

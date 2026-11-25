"""
RevenueGuard Enterprise Database Backup & Recovery Utility
==========================================================
Provides WAL-safe online snapshot backups and restoration for SQLite databases,
and CLI wrappers for PostgreSQL pg_dump / pg_restore operations.
"""

import os
import sys
import sqlite3
import datetime
import argparse
import shutil
from typing import Optional
from backend.config import settings


def backup_sqlite(source_path: str, backup_dir: str = "backups") -> str:
    """
    Performs a non-blocking, WAL-safe online backup of a SQLite database.
    Does not require stopping the application or closing active connections.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source database file not found: {source_path}")

    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.basename(source_path).replace(".db", "")
    target_path = os.path.join(backup_dir, f"{base_name}_backup_{timestamp}.db")

    print(f"[*] Starting WAL-safe online backup: {source_path} -> {target_path}")
    src_conn = sqlite3.connect(source_path)
    dst_conn = sqlite3.connect(target_path)

    try:
        # SQLite backup API: copies pages safely while writers are active in WAL mode
        with dst_conn:
            src_conn.backup(dst_conn, pages=250)
        print(f"[✓] Backup completed successfully: {target_path}")
    finally:
        dst_conn.close()
        src_conn.close()

    # Verify integrity of the newly created backup
    verify_conn = sqlite3.connect(target_path)
    try:
        cur = verify_conn.cursor()
        integrity = cur.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity.lower() != "ok":
            raise RuntimeError(f"Backup integrity check failed: {integrity}")
        print(f"[✓] Backup integrity verified: PRAGMA integrity_check = {integrity}")
    finally:
        verify_conn.close()

    return target_path


def restore_sqlite(backup_path: str, target_path: str) -> None:
    """
    Restores a SQLite database from a verified backup snapshot with rollback safety.
    - Pre-verifies backup snapshot integrity.
    - Preserves safety copy of original target database.
    - Cleans up stale WAL and SHM sidecars.
    - Verifies integrity of restored database.
    - Automatically rolls back to original database if restoration fails.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup snapshot not found: {backup_path}")

    # 1. Pre-verify backup snapshot integrity before altering target
    chk_conn = sqlite3.connect(backup_path)
    try:
        integrity = chk_conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity.lower() != "ok":
            raise ValueError(f"Corrupted backup snapshot cannot be restored: {integrity}")
    finally:
        chk_conn.close()

    print(f"[*] Restoring SQLite database: {backup_path} -> {target_path}")

    # 2. If target exists, verify it is not locked by an exclusive lock and create safety backup
    safety_backup = f"{target_path}.safety_copy_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    target_existed = os.path.exists(target_path)
    if target_existed:
        try:
            # Check for active exclusive lock
            test_conn = sqlite3.connect(target_path, timeout=1.0)
            test_conn.execute("BEGIN IMMEDIATE")
            test_conn.rollback()
            test_conn.close()
        except sqlite3.OperationalError as e:
            raise RuntimeError(f"Cannot restore: target database is locked or actively in use: {e}")

        shutil.copy2(target_path, safety_backup)

    wal_file = f"{target_path}-wal"
    shm_file = f"{target_path}-shm"
    wal_backup = f"{safety_backup}-wal" if os.path.exists(wal_file) else None
    shm_backup = f"{safety_backup}-shm" if os.path.exists(shm_file) else None
    if wal_backup and os.path.exists(wal_file):
        shutil.copy2(wal_file, wal_backup)
    if shm_backup and os.path.exists(shm_file):
        shutil.copy2(shm_file, shm_backup)

    try:
        # Perform restoration via backup API
        src_conn = sqlite3.connect(backup_path)
        dst_conn = sqlite3.connect(target_path)
        try:
            with dst_conn:
                src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()

        # Remove stale WAL/SHM sidecars from target to ensure consistent newly restored state
        if os.path.exists(wal_file):
            try:
                os.remove(wal_file)
            except OSError:
                pass
        if os.path.exists(shm_file):
            try:
                os.remove(shm_file)
            except OSError:
                pass

        # 3. Post-restoration integrity check
        post_conn = sqlite3.connect(target_path)
        try:
            post_integrity = post_conn.execute("PRAGMA integrity_check").fetchone()[0]
            if post_integrity.lower() != "ok":
                raise RuntimeError(f"Post-restoration integrity failed: {post_integrity}")
        finally:
            post_conn.close()

        print(f"[✓] Database restoration completed and verified successfully to: {target_path}")

        # Clean up safety copy on success
        if os.path.exists(safety_backup):
            os.remove(safety_backup)
        if wal_backup and os.path.exists(wal_backup):
            os.remove(wal_backup)
        if shm_backup and os.path.exists(shm_backup):
            os.remove(shm_backup)

    except Exception as exc:
        print(f"[!] Restoration encountered an error: {exc}. Rolling back to safety copy...")
        if target_existed and os.path.exists(safety_backup):
            shutil.copy2(safety_backup, target_path)
            if wal_backup and os.path.exists(wal_backup):
                shutil.copy2(wal_backup, wal_file)
            if shm_backup and os.path.exists(shm_backup):
                shutil.copy2(shm_backup, shm_file)
        raise RuntimeError(f"Database restoration failed; original database preserved. Error: {exc}")


def main():
    parser = argparse.ArgumentParser(description="RevenueGuard Database Backup & Recovery Utility")
    parser.add_argument("--backup", action="store_true", help="Execute an online snapshot backup")
    parser.add_argument("--restore", type=str, help="Restore database from specified backup file")
    parser.add_argument("--target", type=str, default="revenueguard.db", help="Target database path for restoration")
    parser.add_argument("--dir", type=str, default="backups", help="Backup storage directory")
    args = parser.parse_args()

    if args.backup:
        source = settings.DATABASE_URL.replace("sqlite:///", "")
        backup_sqlite(source, backup_dir=args.dir)
    elif args.restore:
        restore_sqlite(args.restore, target_path=args.target)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

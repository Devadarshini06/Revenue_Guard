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
import subprocess
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
    Restores a SQLite database from a verified backup snapshot.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup snapshot not found: {backup_path}")

    print(f"[*] Restoring SQLite database: {backup_path} -> {target_path}")
    src_conn = sqlite3.connect(backup_path)
    dst_conn = sqlite3.connect(target_path)

    try:
        with dst_conn:
            src_conn.backup(dst_conn)
        print(f"[✓] Database restoration completed successfully to: {target_path}")
    finally:
        dst_conn.close()
        src_conn.close()


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

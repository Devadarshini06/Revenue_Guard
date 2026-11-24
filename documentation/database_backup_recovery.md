# RevenueGuard – Database Backup, Recovery & Disaster Plan
## Enterprise Procedures for SQLite Snapshotting and PostgreSQL Failover

**Document Version:** 1.0  
**Scope:** `revenueguard.db` (SQLite) and Clustered PostgreSQL Operations  

---

## 1. Executive Summary

RevenueGuard stores high-value financial records and audit history. This document establishes verified, non-blocking operational procedures for automated scheduled backups, point-in-time recovery, backup verification, and emergency restoration.

---

## 2. SQLite Online Snapshot Backup Strategy

Because SQLite operates in **Write-Ahead Logging (WAL)** mode, simple file-copy commands (`cp revenueguard.db backup.db`) while the application is actively writing can result in corrupted or incomplete snapshots due to writes pending in `-wal` and `-shm` sidecar files.

### Recommended Tool: `backend/database_backup.py`
RevenueGuard provides a built-in backup utility utilizing SQLite's native C-level backup API:
- **Lock-Free Execution**: Reads pages incrementally (in 250-page chunks) while writers continue committing transactions.
- **Sidecar Reintegration**: Safely flushes and integrates pending WAL writes into the backup file.
- **Integrity Certification**: Automatically executes `PRAGMA integrity_check` on the target backup snapshot before marking it successful.

### Automated Backup Execution:
```bash
python -m backend.database_backup --backup --dir backups/
```
Output:
```
[*] Starting WAL-safe online backup: revenueguard.db -> backups/revenueguard_backup_20261124_221501.db
[✓] Backup completed successfully: backups/revenueguard_backup_20261124_221501.db
[✓] Backup integrity verified: PRAGMA integrity_check = ok
```

### Scheduled Cron Automation (Single-Node Linux / Docker Host):
Create a root/appuser cron job to execute snapshots hourly:
```cron
# Run RevenueGuard online backup every hour at minute 0
0 * * * * cd /opt/revenueguard && /opt/revenueguard/venv/bin/python -m backend.database_backup --backup --dir /var/backups/revenueguard >> /var/log/revenueguard_backup.log 2>&1

# Prune snapshots older than 14 days daily at 02:00
0 2 * * * find /var/backups/revenueguard -type f -name "*.db" -mtime +14 -delete
```

---

## 3. SQLite Restoration & Recovery Procedure

> [!CAUTION]
> Always verify database backup integrity before restoration. Never overwrite a running database file without stopping the application or ensuring all connections are drained.

### Restoration Steps:
1. **Stop Application Containers / Services**:
   ```bash
   docker-compose down
   # or: systemctl stop revenueguard-backend
   ```
2. **Quarantine Existing Database (If Present)**:
   ```bash
   mv /app/data/revenueguard.db /app/data/revenueguard_corrupted_$(date +%Y%m%d_%H%M%S).db
   # Clean up any leftover sidecar files
   rm -f /app/data/revenueguard.db-wal /app/data/revenueguard.db-shm
   ```
3. **Execute Restoration**:
   ```bash
   python -m backend.database_backup --restore backups/revenueguard_backup_20261124_221501.db --target /app/data/revenueguard.db
   ```
4. **Verify Restored Database Integrity & Row Counts**:
   ```bash
   sqlite3 /app/data/revenueguard.db "PRAGMA integrity_check;"
   sqlite3 /app/data/revenueguard.db "SELECT count(*) FROM orders;"
   # Expected result: ok, 5200 orders
   ```
5. **Restart Service**:
   ```bash
   docker-compose up -d
   ```

---

## 4. PostgreSQL Enterprise Backup & Recovery Strategy

When operating with a PostgreSQL database cluster:

### Backup Procedure (Physical & Logical):
1. **Logical Backups via `pg_dump` (Daily Compressed Snapshot)**:
   ```bash
   pg_dump -Fc -h postgres-host -U rg_admin -d revenueguard_prod -f /var/backups/rg_prod_$(date +%Y%m%d_%H%M%S).dump
   ```
2. **Point-in-Time Recovery (PITR) via WAL Archiving**:
   - Configure PostgreSQL `archive_mode = on` and `archive_command` shipping WAL segments to cloud storage.
   - Allows point-in-time recovery to any second within the retention window.

### Restoration Procedure:
```bash
# 1. Terminate active application connections
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'revenueguard_prod';"

# 2. Restore using pg_restore
pg_restore -c -h postgres-host -U rg_admin -d revenueguard_prod /var/backups/rg_prod_20261124_221501.dump
```

---

## 5. Backup Retention & Testing Schedule

- **Retention Window**:
  - Hourly snapshots retained for 48 hours.
  - Daily snapshots retained for 30 days.
  - Monthly archives retained for 1 year (regulatory compliance).
- **Automated Verification**:
  - Validated by unit test `test_database_backup_and_restore_cycle_in_temp_db` in `tests/test_production_readiness.py`.
  - Monthly automated disaster recovery rehearsal restoring a snapshot into a staging environment and verifying exact row counts against production benchmarks.

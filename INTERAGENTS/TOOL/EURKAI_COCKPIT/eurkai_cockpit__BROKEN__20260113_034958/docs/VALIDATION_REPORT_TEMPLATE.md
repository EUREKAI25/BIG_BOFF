# EURKAI_COCKPIT — Validation Report Template

> This template is automatically populated by `install_all.sh`.  
> Manual validation should follow this same structure.

---

## Report Metadata

| Field | Value |
|-------|-------|
| **Generated** | `<TIMESTAMP>` |
| **Installation started** | `<START_TIMESTAMP>` |
| **Target directory** | `<TARGET_DIR>` |
| **Validator** | `install_all.sh` / `manual` |
| **Version** | `1.0.0` |

---

## System Information

| Component | Version | Status |
|-----------|---------|--------|
| Operating System | `<OS_INFO>` | ✅ / ❌ |
| Python | `<PYTHON_VERSION>` | ✅ >= 3.11 required |
| Git | `<GIT_VERSION>` | ⚠️ Optional |
| npm | `<NPM_VERSION>` | ⚠️ Optional (frontend) |

---

## Component Status

### Core Components (Required)

| Component | Path | Status | Notes |
|-----------|------|--------|-------|
| Backend API | `backend/` | ✅ / ❌ | FastAPI server |
| Storage Layer | `backend/storage/` | ✅ / ❌ | SQLite CRUD |
| CLI | `cli/` | ✅ / ❌ | Click-based CLI |
| Database | `data/cockpit.db` | ✅ / ❌ | SQLite file |

### Optional Components

| Component | Path | Status | Notes |
|-----------|------|--------|-------|
| Frontend | `frontend/` | ✅ / ⏭️ | React + Vite |
| Secrets Module | `backend/secrets/` | ✅ / ❌ | Encrypted storage |
| Backup Module | `backend/backup/` | ✅ / ❌ | Git integration |

---

## Test Results

### Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | `<COUNT>` |
| **Passed** | `<PASSED>` |
| **Failed** | `<FAILED>` |
| **Skipped** | `<SKIPPED>` |
| **Duration** | `<DURATION>` |

### Test Suites

| Suite | File | Status | Notes |
|-------|------|--------|-------|
| Storage | `test_storage.py` | ✅ / ❌ | CRUD operations |
| API Smoke | `test_api_smoke.py` | ✅ / ❌ | Endpoint validation |
| Secrets | `test_secrets.py` | ✅ / ❌ | Encryption & gating |
| Backup | `test_backup_dryrun.py` | ✅ / ❌ | Dry-run mode |
| CLI | `test_cli.py` | ✅ / ❌ | Command parsing |

### Failed Tests (if any)

```
<FAILED_TEST_OUTPUT>
```

---

## Validation Checklist

### Pre-Installation

- [ ] Python >= 3.11 available
- [ ] Target directory accessible
- [ ] Sufficient disk space (>100MB)

### Installation

- [ ] Dependencies installed successfully
- [ ] No pip errors
- [ ] Frontend built (if present)

### Database

- [ ] Schema created
- [ ] Tables exist: projects, briefs, runs, secrets, config, modules, backups, tags
- [ ] Migrations applied

### Functionality

- [ ] API server starts
- [ ] Health endpoint responds
- [ ] CLI `--help` works
- [ ] CLI `init` succeeds

### Security

- [ ] EURKAI_MASTER_PASSWORD set (for secrets)
- [ ] Secrets not exposed in list endpoints
- [ ] Session gating works for copy

### Backup

- [ ] Dry-run creates files
- [ ] SQLite copy successful
- [ ] JSON export successful
- [ ] Git commit (if configured)

---

## Known Issues

| Issue | Severity | Workaround |
|-------|----------|------------|
| *None* | - | - |

---

## Recommendations

1. **Set master password** before using secrets:
   ```bash
   export EURKAI_MASTER_PASSWORD="secure-password"
   ```

2. **Configure Git** for automated backups:
   ```bash
   git init
   git remote add origin <your-repo-url>
   ```

3. **Run periodic backups**:
   ```bash
   python -m backend.backup.backup
   ```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Installer | `install_all.sh` | `<DATE>` | ✅ Automated |
| Reviewer | | | |

---

## Appendix: Full Test Output

```
<FULL_TEST_OUTPUT>
```

---

*Template version: 1.0.0 — EURKAI_COCKPIT C08*

# Local backup and restore rehearsal

Run this before database migration or changes to stored records. MySQL must be
running in XAMPP; Apache is not required for Flask or Vite. Pause application
uploads and record edits until the backup finishes so files and database rows
describe the same checkpoint.

From the repository root in PowerShell:

```powershell
& '.venv\Scripts\python.exe' graphiscan/tools/backup_local.py --verify-restore
```

The tool reads the existing local `graphiscan/config.py` without printing its
values. It uses the XAMPP clients at `C:/xampp/mysql/bin`; use `--mysql-bin` to
specify another client directory. The configured database account must be able
to read the source and create/drop a temporary database for the restore check.

Output is a unique checkpoint directory inside the Git-ignored
`.local-backups/`. It contains:

- `database.sql`: a transactional dump of the current configured database.
- `project-and-private-assets.zip`: Git-visible project files, local app/root
  configuration, active model files, and current uploaded images.
- `manifest.json`: archive/dump hashes and restore-check results.

These files contain private data and configuration. Keep them outside Git and
share them only through an approved private backup location. This local copy
does not protect against loss of the machine. Dependencies, training datasets,
Git history, and external hosting settings are not included in the archive.

With `--verify-restore`, the tool creates a random temporary database, imports
the dump there, and compares every base table's schema, row count, and row
content hash with the source baseline. It then drops only that newly created
temporary database. It never imports into or drops the source database. ZIP
integrity is checked separately; application startup from an extracted archive
is not tested by this command.

Treat the checkpoint as complete only when the command succeeds and the
manifest reports `database_restore_verified: true`. Failed runs may leave an
incomplete checkpoint directory; do not use it as the migration backup.
Transient client credentials are removed in cleanup. An interrupted process
or power failure may require private cleanup of the temporary files/database.

If the command reports connection error 2003, check that MySQL stays running and
that its configured host/port are reachable before retrying. Do not migrate or
repair database files merely to bypass a connection failure.

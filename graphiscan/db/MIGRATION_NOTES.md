# Legacy MySQL to Supabase PostgreSQL

This is a migration plan, not a completed data transfer. The source is the schema-only `legacy_mysql_schema.sql` extracted from an export dated 2026-07-28. The folder `C:\Users\MY_PC\Downloads\CAPSTONE\graphiscan_db` contains raw MySQL/MariaDB `.frm` and `.ibd` files; these are not PostgreSQL imports. The XAMPP database copy has later file timestamps. Obtain a fresh logical SQL export and a secure backup before moving real rows.

| Existing MySQL table | Target |
| --- | --- |
| `users` | Supabase Auth credentials plus `user_profiles`; map integer IDs to Auth UUIDs. Do not copy password hashes into the new app as usable passwords. Create temporary credentials through the approved account-issuance flow. |
| `students` | `students` plus required `schools`; normalize grade text to integer 1, 2, or 3 and reconcile school assignment. |
| `handwriting_samples` | `handwriting_samples`; move files into a private Storage bucket and store object paths, not local Flask static paths. |
| `results` | `screening_results` with the historical binary model/version and `task_type = 'binary'`. Convert stored percentage scores to fractions in 0–1. Never infer a Low Potential class from old Normal results. Do not import obsolete AI advice. |
| `validations` | `expert_validations`; map expert IDs and retain expert-authored remarks/recommendations. |
| `reports` | `screening_reports`; reconcile one Initial report per student and label later reports Follow-up by actual assessment order. |
| `audit_logs` | `audit_logs`; map actor IDs where possible and review old action text for unnecessary personal details. |
| `password_reset_tokens` | Do not migrate. Supabase Auth handles future password resets; old reset tokens should not remain valid. |

Target table definitions are in `postgres/001_identity.sql` and `postgres/002_screening.sql`. Neither has been applied. The final migration still needs a secure import program, rollback plan, server API conversion, and reconciliation of row counts and relationships. Keep the original export and raw database files outside Git.

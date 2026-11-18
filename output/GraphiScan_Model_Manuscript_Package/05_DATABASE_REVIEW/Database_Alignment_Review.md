# Manuscript database alignment review

Reviewed 16 November 2026. Verdict: the supplied manuscript data dictionary (Tables 2-9, PDF pages 38-43) is not an accurate physical description of the current Supabase implementation.

## Evidence

Read the supplied Graphiscan (5).pdf extracted database section. Inspected the signed-in Supabase Schema Visualizer for graphiscan-test, main PRODUCTION, public schema. Live column names and types were observed for user_profiles, students, expert_validations, screening_reports, user_school_grades and final_screening_reports. Compared repository PostgreSQL migrations 001, 002, 003, 004, 023 and 030 for constraints and additional structures. Constraints and tables outside the inspected viewport were checked from source rather than independently queried live. No application rows were read, no SQL was executed against the live database, and no schema or manuscript was changed by this review.

## Table-by-table findings

| Manuscript table | Finding | Required correction if presented as physical schema |
|---|---|---|
| Table 2: seven-table list | The seven conceptual entities omit the shared user design and supporting tables. | Explain that seven entities are conceptual if retaining them. Do not label the list as the complete physical schema. Include schools, user_profiles, model_registry, final_screening_reports and access/link structures in the implementation mapping. |
| Table 3: Student | Live students uses student_id bigint (int8), full_name text, age smallint (int2), grade_level smallint (int2), school_id bigint, teacher_id uuid, parent_id uuid, created_at/updated_at timestamptz and revision bigint. The manuscript lists INT, VARCHAR(100), mandatory age and VARCHAR grade. | Use actual field names/types. Source defines age nullable and grade_level required, constrained to 1-3. Add school and account relationships, timestamps and revision if documenting every column. |
| Table 4: Teacher | Teachers are represented by user_profiles with role='teacher'; live user_id is uuid and full_name is text. There is no separate Teacher table in the migration-defined physical schema. | Map conceptual Teacher to user_profiles. Login identity/email belongs to Supabase Auth; contactno is not defined in user_profiles. Do not document invented mandatory phone fields. |
| Table 5: Handwriting Sample | Source defines handwriting_samples: sample_id bigint, student_id bigint, teacher_id uuid, storage_path text, created_at timestamptz. | Replace image_file BLOB/VARCHAR with storage_path text and date_captured DATETIME with created_at timestamptz. Images are referenced in private storage. Source makes teacher_id nullable and student_id/storage_path required. |
| Table 6: Result | Source defines screening_results with result_id/sample_id/model_id bigint, task_type/classification text, class_probabilities jsonb, confidence_score numeric(6,5), date_generated timestamptz, revision bigint, provenance text, model_snapshot/decision_rule jsonb. Migration 003 removes analysis_summary. | Remove dysgraphia_probability FLOAT and analysis_summary. Describe stored image classification and model score, not a clinically calibrated probability. Add model/version provenance and actual data types. Sample reference is unique. |
| Table 7: Expert | Experts use user_profiles with role='expert'; expert references use uuid. The manuscript invents a separate Expert table and license number field. | Map conceptual Expert to user_profiles; remove unsupported license_no and INT account ID. Describe authorized expert review without asserting credentials stored in this schema. |
| Table 8: Validation | Live expert_validations has validation_id/result_id bigint, status text, expert_id uuid, remarks text, expert_recommendation text, follow_up_needed bool, validation_date/created_at/updated_at timestamptz, revision bigint and provenance text. | Change validation_status to status and DATETIME to timestamptz. Source defines validation_date nullable while Pending; manuscript incorrectly says Not Null. Include recommendation/follow-up fields and unique result relationship. |
| Table 9: Report | Live screening_reports has report_id/student_id/result_id bigint, report_type/report_status text, created_at timestamptz and school_context jsonb. A distinct live final_screening_reports stores whole-history expert conclusions. | Replace Progress example with Follow-up Screening; add result_id and school_context. Do not state that created_at proves a generated PDF. Do not combine individual reports with finalized whole-history reports or assert Draft/Finalized as the individual report states. Source default report_status is Generated. |

## Final report structure missing from the manuscript

Live final_screening_reports columns: final_report_id bigint, student_id bigint, revision bigint, expert_id uuid, expert_name text, summary text, conclusion text, next_steps text, history_fingerprint text, screenings jsonb, request_key text, request_digest text and finalized_at timestamptz. It records expert-authored whole-history conclusions and an ordered screening snapshot. Individual screening_reports is a different structure.

## Other structures to explain

- schools stores school records referenced by students.
- user_school_grades stores user/school/grade scope assignments; live types are uuid, bigint and smallint.
- model_registry records model versions and selection/default metadata; screening_results references it.
- school_memberships, assignment_eligibilities and user_permission_grants support authorization according to the migration source.
- expert_review_history, screening_expert_assignments, privacy agreement/acceptance, audit and request-operation tables are supporting structures in the source. A focused conceptual ERD can omit operational detail when its scope is stated, but a complete physical dictionary must account for it.

## Suggested replacement explanation

The conceptual model describes students, teacher and expert roles, handwriting samples, screening results, expert reviews and reports. In the implemented Supabase PostgreSQL database, teacher, expert and parent identities share user_profiles and are distinguished by role; authentication identities are managed by Supabase Auth. Student records reference schools and authorized teacher or parent accounts. Handwriting samples store private-storage object paths, and screening results record the selected model, classification, scores and decision metadata. Expert reviews are stored in expert_validations. Individual Initial and Follow-up reports are represented by screening_reports, while finalized whole-history expert conclusions and snapshots are stored separately in final_screening_reports. Supporting tables maintain school/grade responsibilities, authorization, privacy acceptance, review history and audit records.

## Next manuscript changes

Retain the seven-entity figure as a conceptual ERD only if explicitly labeled and mapped to the implementation. Correct the physical data dictionary names, data types, nullability and relationships using the actual schema. Update the figure and prose together; the current seven-table physical description should not be treated as aligned. This review does not redesign the ERD or edit the retained Validation Table automatically.

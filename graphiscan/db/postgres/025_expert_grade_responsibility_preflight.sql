-- Read-only verification after migration025. Does not query student/account rows.
WITH bodies AS (
    SELECT proname,regexp_replace(prosrc,'[[:space:]]+','','g') AS body
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname='public' AND proname IN
        ('graphiscan_read_directory','graphiscan_read_screenings','graphiscan_write_review','graphiscan_screening_image')
)
SELECT
    (SELECT strpos(body,'(a.role=''expert''ANDpublic.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))')>0
        FROM bodies WHERE proname='graphiscan_read_directory') AS grade_student_access,
    (SELECT (length(body)-length(replace(body,'(a.role=''expert''ANDpublic.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))','')))
        / length('(a.role=''expert''ANDpublic.graphiscan_grade_allowed(subject_id,s.school_id,s.grade_level))')=2
        FROM bodies WHERE proname='graphiscan_read_screenings') AS grade_screening_access,
    (SELECT strpos(body,'IFNOTpublic.graphiscan_grade_allowed(subject_id,st.school_id,st.grade_level)THEN')>0
        AND strpos(body,'IFassignedISDISTINCTFROMsubject_id')=0
        FROM bodies WHERE proname='graphiscan_write_review') AS grade_review_access,
    (SELECT strpos(body,'public.graphiscan_read_screenings(')>0
        FROM bodies WHERE proname='graphiscan_screening_image') AS image_rechecks_record_scope;

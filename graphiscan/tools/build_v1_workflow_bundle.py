"""Build reviewable migration 015 and atomic audience/fictional-fixture bundle; offline only."""
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
SQL = APP / 'db/postgres'


def replacement(source, name, old, new):
    content = (SQL / source).read_text(encoding='utf-8')
    start = content.index('CREATE FUNCTION public.' + name + '(')
    end = content.index('\n$$;', start) + len('\n$$;')
    function = content[start:end]
    if function.count(old) != 1:
        raise ValueError('Audience source changed: ' + source)
    return function.replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION', 1).replace(old, new)


def migration():
    header = """-- UNAPPLIED 015, after 001-014. No notice/accounts/grants are seeded here.
-- Existing single-account and ordinary notice behavior is preserved.
BEGIN;
ALTER TABLE public.privacy_agreements ADD COLUMN test_subject_ids uuid[];
ALTER TABLE public.privacy_agreements ADD CONSTRAINT privacy_test_audience_valid CHECK (
    test_subject_ids IS NULL OR (
        test_subject_id IS NULL AND cardinality(test_subject_ids) BETWEEN 1 AND 16
        AND array_ndims(test_subject_ids)=1 AND array_position(test_subject_ids,NULL) IS NULL
    ));
"""
    functions = [replacement('007_privacy_acceptance.sql', 'graphiscan_accept_privacy',
        'OR (a.test_subject_id IS NOT NULL AND a.test_subject_id <> subject_id) THEN',
        'OR (a.test_subject_id IS NOT NULL AND a.test_subject_id <> subject_id)\n'
        '       OR (a.test_subject_ids IS NOT NULL AND NOT (subject_id = ANY(a.test_subject_ids))) THEN')]
    for source, name in [('009_directory_reads.sql','graphiscan_read_directory'),
                         ('012_screening_reads.sql','graphiscan_read_screenings')]:
        functions.append(replacement(source, name,
            'AND (a.test_subject_id IS NULL OR a.test_subject_id = p.user_id)',
            'AND (a.test_subject_id IS NULL OR a.test_subject_id = p.user_id)\n'
            '        AND (a.test_subject_ids IS NULL OR p.user_id = ANY(a.test_subject_ids))'))
    return header + '\n\n'.join(functions) + '\nCOMMIT;\n'


def bundle():
    notice = (APP / 'api/fictional-workflow-notice.txt').read_text(encoding='utf-8')
    seed = (SQL / 'seed_workflow_fixtures.sql').read_text(encoding='utf-8')
    if '$workflow_notice$' in notice:
        raise ValueError('Notice SQL delimiter conflict')
    seed = seed.replace('WORKFLOW_NOTICE_TEXT', '$workflow_notice$' + notice + '$workflow_notice$')
    return ('-- Apply ONLY this bundle once; do not also apply 015 or seed_workflow_fixtures.sql.\n'
            '-- Atomic migration + four-account fictional setup. No passwords or acceptances.\n'
            + migration().removesuffix('COMMIT;\n') + '\n'
            + seed.replace('BEGIN;\n','',1).removesuffix('COMMIT;\n') + '\nCOMMIT;\n')


def main():
    (SQL / '015_privacy_test_audience.sql').write_text(migration(), encoding='utf-8', newline='\n')
    (SQL / '015_workflow_fixtures.sql').write_text(bundle(), encoding='utf-8', newline='\n')
    print('Prepared 015 source migration and atomic workflow bundle; no database connection or writes.')


if __name__ == '__main__':
    main()

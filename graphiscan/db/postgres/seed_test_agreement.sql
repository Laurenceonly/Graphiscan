-- Optional OWNER-run fictional fixture, after reviewed 007. No acceptance is created.
-- User authorized temporary fictional testing only on 2026-10-20.
-- Refuses an existing current notice/version; never overwrites published text.
BEGIN;
DO $seed$
DECLARE subject uuid; notice text := $notice$GraphiScan temporary test notice - fictional account only
Version: graphiscan-test-v1

This notice is for the disposable GraphiScan development test. Use only fictional
student details and synthetic handwriting samples. Do not submit real student
names, handwriting, school records or screening information in this test.

The test checks account sign-in, first-login password changes, versioned notice
display and acceptance, and access restrictions. Supabase Auth manages the test
account's credentials and sessions. The test database records the account, the
notice version accepted, the server-recorded acceptance time and related audit
events. Passwords and tokens must not be shared in chat or included in reports.

GraphiScan is a handwriting screening aid, not a clinical diagnosis. The active
predictor has Normal and High Potential labels. A screening result does not
establish that a child has a condition. Planned expert review and parent-release
flows remain subject to the implemented server permissions and verification.

Account access is limited by server-side account status, onboarding, role and
record scope. Completing this test notice does not grant administrative
permissions, authorize access to another account's records or establish that
production student-data protections or private image hosting are complete.

You may decline by leaving the test without accepting. Acceptance records only
your agreement to participate in this fictional-data development test. It is not
guardian permission, permission for real student-data collection, authorization
for model training, or approval of a production privacy policy.

The responsible institution/contact, real-data purposes and recipients, retention
and deletion periods, participant permissions and request procedures remain to be
reviewed before real-user use. No real-data retention period or production
privacy compliance is promised by this temporary notice. Raise test questions
with the GraphiScan project team through your existing project contact.

If the notice changes, a new version will be published and you will be asked to
read and accept that version before continuing. Earlier acceptance stays linked
to the earlier text; it is not transferred to a revised notice automatically.
$notice$;
BEGIN
    SELECT u.id INTO STRICT subject FROM auth.users u JOIN public.user_profiles p ON p.user_id=u.id
        WHERE u.email='graphiscan.test@example.invalid' AND p.full_name='Synthetic Test Admin'
          AND p.role='admin' AND p.account_status='active' AND NOT p.must_change_password
          AND NOT p.credential_update_pending;
    IF EXISTS (SELECT 1 FROM public.privacy_agreements WHERE is_current OR version='graphiscan-test-v1') THEN
        RAISE EXCEPTION 'Existing current notice or fixture version; review instead of overwriting';
    END IF;
    INSERT INTO public.privacy_agreements(version,title,content,content_sha256,
        approved_by,approved_at,published_at,is_current,test_subject_id)
    VALUES ('graphiscan-test-v1','GraphiScan temporary test notice - fictional account only',notice,
        encode(sha256(convert_to(notice,'UTF8')),'hex'),subject,clock_timestamp(),clock_timestamp(),true,subject);
    INSERT INTO public.audit_logs(actor_id,action,resource_type,resource_id)
        VALUES(subject,'test_fixture.notice_published','privacy_agreement','graphiscan-test-v1');
END;
$seed$;
COMMIT;

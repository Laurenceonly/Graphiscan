// Isolated PostgreSQL checks. No hosted connection, credentials or user data.
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import assert from 'node:assert/strict'
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..')
const {PGlite}=await import(pathToFileURL(path.join(root,'.local-tools/api-validation/node_modules/@electric-sql/pglite/dist/index.js')))
const read=name=>fs.readFile(path.join(root,'graphiscan/db/postgres',name+'.sql'),'utf8')
const db=new PGlite()
let checks=0
const check=(actual,expected)=>{assert.deepEqual(actual,expected);checks++}
const A='00000000-0000-4000-8000-000000000001',T='00000000-0000-4000-8000-000000000002',E='00000000-0000-4000-8000-000000000003',P='00000000-0000-4000-8000-000000000004',F='00000000-0000-4000-8000-000000000005'
const ids=[A,T,E,P,F], emails=['graphiscan.test@example.invalid','graphiscan.teacher.test@example.invalid','graphiscan.expert.test@example.invalid','graphiscan.parent.test@example.invalid','foreign@example.invalid']
const one=async(sql,args=[])=> (await db.query(sql,args)).rows[0]
const snapshot=(await read('access_snapshot')).replaceAll('%(user_id)s','$1').replaceAll('%(session_id)s','$2')
const py=await fs.readFile(path.join(root,'graphiscan/v1_privacy.py'),'utf8')
const agreement=py.match(/AGREEMENT_SQL = """([\s\S]*?)"""/)[1].replaceAll('%s','$1')
const bundle=await read('015_workflow_fixtures')
const canonical=value=>value.replaceAll('\r\n','\n')
const migration=canonical(await read('015_privacy_test_audience')).replace(/COMMIT;\n$/,'')
check(canonical(bundle).includes(migration),true)
const fixtureSource=canonical(await read('seed_workflow_fixtures')).replace('WORKFLOW_NOTICE_TEXT', '$workflow_notice$'+canonical(await fs.readFile(path.join(root,'graphiscan/api/fictional-workflow-notice.txt'),'utf8'))+'$workflow_notice$').replace('BEGIN;\n','').replace(/COMMIT;\n$/,'')
check(canonical(bundle).includes(fixtureSource),true)
async function rejected(sql,args=[]){await assert.rejects(db.query(sql,args));checks++;await db.exec('ROLLBACK')}
try{
  await db.exec(`CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY,email text,email_confirmed_at timestamptz,banned_until timestamptz,deleted_at timestamptz);
    CREATE TABLE auth.sessions(id uuid PRIMARY KEY,user_id uuid REFERENCES auth.users(id),created_at timestamptz DEFAULT clock_timestamp(),not_after timestamptz);
    CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role;`)
  for(const migration of ['001_identity','002_screening','003_api_contract','004_session_access','005_api_reader','006_password_change','007_privacy_acceptance','008_session_logout','009_directory_reads','010_directory_writes','011_assignment_options','012_screening_reads','013_014_screening_writes'])await db.exec(await read(migration))
  for(let index=0;index<ids.length;index++)await db.query('INSERT INTO auth.users VALUES($1,$2,clock_timestamp(),NULL,NULL)',[ids[index],emails[index]])
  await db.exec(await read('seed_test_profile'))
  await db.query('UPDATE user_profiles SET must_change_password=false WHERE user_id=$1',[A])
  await db.exec(await read('seed_test_agreement'))
  const originalSession='30000000-0000-4000-8000-000000000001'
  await db.query('INSERT INTO auth.sessions(id,user_id) VALUES($1,$2)',[originalSession,A])
  check((await one(snapshot,[A,originalSession])).required_agreement_version,'graphiscan-test-v1')
  check((await db.query(agreement,[A])).rows.length,1)
  check((await db.query(agreement,[F])).rows.length,0)
  const oldNotice=await one("SELECT to_jsonb(a)-'is_current' original FROM privacy_agreements a")
  const oldCounts=await one('SELECT (SELECT count(*) FROM user_profiles)::int profiles,(SELECT count(*) FROM audit_logs)::int audits')
  // Each failure must roll back the DDL as well as all fixture rows.
  for(const mutation of ["UPDATE auth.users SET email_confirmed_at=NULL WHERE email='graphiscan.teacher.test@example.invalid'",
                         "UPDATE auth.users SET banned_until=clock_timestamp()+interval '1 day' WHERE email='graphiscan.teacher.test@example.invalid'",
                         "UPDATE auth.users SET deleted_at=clock_timestamp() WHERE email='graphiscan.teacher.test@example.invalid'"]){
    await db.exec(mutation);await assert.rejects(db.exec(bundle));checks++;await db.exec('ROLLBACK')
    check(await one('SELECT (SELECT count(*) FROM user_profiles)::int profiles,(SELECT count(*) FROM audit_logs)::int audits'),oldCounts)
    check((await one("SELECT count(*)::int n FROM information_schema.columns WHERE table_name='privacy_agreements' AND column_name='test_subject_ids'")).n,0)
    await db.exec("UPDATE auth.users SET email_confirmed_at=clock_timestamp(),banned_until=NULL,deleted_at=NULL WHERE email='graphiscan.teacher.test@example.invalid'")
  }
  await db.query('INSERT INTO schools(name) VALUES($1)',['GraphiScan Synthetic Workflow School'])
  await assert.rejects(db.exec(bundle));checks++;await db.exec('ROLLBACK')
  check((await one('SELECT count(*)::int n FROM user_profiles')).n,1)
  await db.exec('DELETE FROM schools')
  await db.exec(bundle)
  check((await one('SELECT count(*)::int n FROM app_session_revocations WHERE session_id=$1',[originalSession])).n,1)
  check((await one('SELECT count(*)::int n FROM user_profiles')).n,4)
  check((await one('SELECT count(*)::int n FROM user_profiles WHERE must_change_password')).n,3)
  check((await one("SELECT count(*)::int n FROM user_permission_grants WHERE permission_key='assignments.manage' AND school_id IS NOT NULL")).n,1)
  check((await one('SELECT count(*)::int n FROM user_permission_grants')).n,1)
  check((await one('SELECT count(*)::int n FROM school_memberships')).n,2)
  check((await one('SELECT count(*)::int n FROM assignment_eligibilities')).n,4)
  check((await one('SELECT count(*)::int n FROM students')).n,1)
  check((await one('SELECT teacher_id::text teacher,parent_id::text parent,age,grade_level FROM students')),{teacher:T,parent:P,age:8,grade_level:2})
  check((await one("SELECT test_subject_ids audience FROM privacy_agreements WHERE is_current")).audience,[A,T,E,P])
  check(await one("SELECT to_jsonb(a)-'is_current' original FROM privacy_agreements a WHERE version='graphiscan-test-v1'"),{original:{...oldNotice.original,test_subject_ids:null}})
  check((await one('SELECT count(*)::int n FROM privacy_agreement_acceptances')).n,0)
  // Repeat must fail without duplicating any fixtures or resetting onboarding.
  await assert.rejects(db.exec(bundle));checks++;await db.exec('ROLLBACK')
  check((await one('SELECT count(*)::int n FROM user_profiles')).n,4)
  const published=await one('SELECT content,content_sha256 FROM privacy_agreements WHERE is_current')
  check(published.content,canonical(await fs.readFile(path.join(root,'graphiscan/api/fictional-workflow-notice.txt'),'utf8')))
  check((await one("SELECT encode(sha256(convert_to(content,'UTF8')),'hex') hash FROM privacy_agreements WHERE is_current")).hash,published.content_sha256)
  const checker=await fs.readFile(path.join(root,'graphiscan/tools/check_v1_workflow_setup.py'),'utf8')
  const fixtureQuery=checker.match(/FIXTURE_SQL = """([\s\S]*?)"""/)[1].replaceAll('%s','$1')
  await db.exec('SET ROLE graphiscan_api_reader')
  check(await one(fixtureQuery,[published.content_sha256]),{profiles:true,exact_notice:true,old_notice_retained:true,narrow_grant:true,memberships:true})
  await db.exec('RESET ROLE')
  // Add a foreign authenticated teacher to prove the audience excludes otherwise active users.
  await db.query("INSERT INTO user_profiles(user_id,full_name,role,account_status,must_change_password,created_by) VALUES($1,'Foreign Fictional Teacher','teacher','active',false,$2)",[F,A])
  const sessions={}
  for(let i=0;i<ids.length;i++){
    sessions[ids[i]]=`10000000-0000-4000-8000-00000000000${i+1}`
    await db.query('INSERT INTO auth.sessions(id,user_id) VALUES($1,$2)',[sessions[ids[i]],ids[i]])
  }
  const directory=async(id)=> (await one("SELECT graphiscan_read_directory($1,$2,'schools','',NULL,NULL,NULL,NULL,25,NULL) result",[id,sessions[id]])).result
  const screenings=async(id)=> (await one("SELECT graphiscan_read_screenings($1,$2,'screenings','{}',NULL,NULL,25,NULL,false) result",[id,sessions[id]])).result
  const accept=async(id,version='graphiscan-workflow-test-v1')=>one('SELECT * FROM graphiscan_accept_privacy($1,$2,$3,$4)',[id,sessions[id],version,'20000000-0000-4000-8000-000000000001'])
  for(const id of [T,E,P]){check((await directory(id)).code,'PASSWORD_CHANGE_REQUIRED');check((await accept(id)).outcome,'password_required')}
  for(const id of [A,T,E,P]){
    check((await one(snapshot,[id,sessions[id]])).required_agreement_version,'graphiscan-workflow-test-v1')
    check((await db.query(agreement,[id])).rows.length,1)
  }
  check((await one(snapshot,[F,sessions[F]])).required_agreement_version,null)
  check((await db.query(agreement,[F])).rows.length,0)
  check((await directory(F)).code,'AGREEMENT_NOT_CONFIGURED')
  check((await screenings(F)).code,'AGREEMENT_NOT_CONFIGURED')
  check((await accept(F)).outcome,'agreement_unavailable')
  await db.query("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES($1,'graphiscan-workflow-test-v1')",[F])
  check((await directory(F)).code,'AGREEMENT_NOT_CONFIGURED')
  check((await screenings(F)).code,'AGREEMENT_NOT_CONFIGURED')
  await db.query('DELETE FROM privacy_agreement_acceptances WHERE user_id=$1',[F])
  // Preserve the original singleton restriction as well as normal non-test notices.
  await db.exec("BEGIN; UPDATE privacy_agreements SET is_current=false WHERE is_current; UPDATE privacy_agreements SET is_current=true WHERE version='graphiscan-test-v1';")
  check((await db.query(agreement,[A])).rows.length,1)
  check((await db.query(agreement,[F])).rows.length,0)
  check((await one(snapshot,[A,sessions[A]])).required_agreement_version,'graphiscan-test-v1')
  check((await one(snapshot,[F,sessions[F]])).required_agreement_version,null)
  check((await accept(A,'graphiscan-test-v1')).outcome,'accepted')
  check((await accept(F,'graphiscan-test-v1')).outcome,'agreement_unavailable')
  await db.exec('ROLLBACK')
  await db.exec("BEGIN; UPDATE privacy_agreements SET is_current=false WHERE is_current;")
  await db.query("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES('ordinary','Ordinary compatibility fixture','x',encode(sha256(convert_to('x','UTF8')),'hex'),$1,clock_timestamp(),clock_timestamp(),true)",[A])
  check((await db.query(agreement,[F])).rows.length,1)
  check((await one(snapshot,[F,sessions[F]])).required_agreement_version,'ordinary')
  check((await accept(F,'ordinary')).outcome,'accepted')
  check((await directory(F)).code,null)
  check((await screenings(F)).code,null)
  await db.exec('ROLLBACK')
  // Simulate successful first-password changes only in this isolated DB; then issue fresh sessions.
  await db.query('UPDATE user_profiles SET must_change_password=false WHERE user_id=ANY($1::uuid[])',[[T,E,P]])
  await db.exec("DELETE FROM auth.sessions; DELETE FROM app_session_revocations;")
  for(const id of ids)await db.query('INSERT INTO auth.sessions(id,user_id) VALUES($1,$2)',[sessions[id],id])
  for(const id of [A,T,E,P]){
    check((await directory(id)).code,'PRIVACY_ACCEPTANCE_REQUIRED')
    check((await screenings(id)).code,'PRIVACY_ACCEPTANCE_REQUIRED')
    check((await accept(id,'graphiscan-test-v1')).outcome,'agreement_changed')
    const accepted=await accept(id);check(accepted.outcome,'accepted')
    check((await accept(id)).accepted_at,accepted.accepted_at)
    check((await directory(id)).code,null)
    check((await screenings(id)).code,null)
  }
  check((await one('SELECT count(*)::int n FROM privacy_agreement_acceptances')).n,4)
  const school=(await one('SELECT school_id::text id FROM students')).id
  const choices=(await one('SELECT graphiscan_assignment_options($1,$2,$3,NULL,NULL,25) result',[A,sessions[A],school])).result
  check(choices.rows.map(x=>x.data.role).sort(),['expert','parent','teacher'])
  for(const bad of ["'{}'::uuid[]",`ARRAY[NULL]::uuid[]`,`ARRAY[ARRAY['${A}']]::uuid[]`,`array_fill('${A}'::uuid,ARRAY[17])`]){
    await rejected(`INSERT INTO privacy_agreements(version,title,content,content_sha256,test_subject_ids) VALUES('bad','bad','x',repeat('a',64),${bad})`)
  }
  await rejected(`INSERT INTO privacy_agreements(version,title,content,content_sha256,test_subject_id,test_subject_ids) VALUES('bad','bad','x',repeat('a',64),'${A}',ARRAY['${A}']::uuid[])`)
  await rejected("UPDATE privacy_agreements SET test_subject_ids=ARRAY[]::uuid[] WHERE is_current")
  // Published test audience is immutable too.
  await rejected(`UPDATE privacy_agreements SET test_subject_ids=ARRAY['${F}']::uuid[] WHERE is_current`)
  for(const role of ['anon','authenticated','service_role']){
    check((await one("SELECT has_function_privilege($1,'graphiscan_accept_privacy(uuid,uuid,text,uuid)','EXECUTE') allowed",[role])).allowed,false)
    check((await one("SELECT has_function_privilege($1,'graphiscan_read_directory(uuid,uuid,text,text,bigint,smallint,timestamptz,bigint,integer,bigint)','EXECUTE') allowed",[role])).allowed,false)
    check((await one("SELECT has_function_privilege($1,'graphiscan_read_screenings(uuid,uuid,text,jsonb,timestamptz,bigint,integer,bigint,boolean)','EXECUTE') allowed",[role])).allowed,false)
    check((await one("SELECT has_table_privilege($1,'privacy_agreements','INSERT,UPDATE,DELETE') allowed",[role])).allowed,false)
  }
  console.log(JSON.stringify({status:'workflow-sql-checks-passed',checks,scope:'isolated PGlite, actual 001-015 bundle and reader SQL; no hosted changes'}))
}finally{await db.close()}

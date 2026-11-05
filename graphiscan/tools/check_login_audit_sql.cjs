const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {createRequire}=require('module');
const root=path.resolve(__dirname,'../..'),req=createRequire(path.join(root,'.local-tools/api-validation/package.json'));
(async()=>{
 const {PGlite}=req('@electric-sql/pglite');const db=new PGlite();let checks=0;
 const check=(ok,msg)=>{assert(ok,msg);checks++},q=(sql,p=[])=>db.query(sql,p);
 const U=n=>'00000000-0000-4000-8000-'+String(n).padStart(12,'0');
 try{
 await db.exec('CREATE ROLE anon;CREATE ROLE authenticated;CREATE ROLE service_role;CREATE SCHEMA auth;CREATE TABLE auth.users(id uuid PRIMARY KEY);CREATE TABLE auth.sessions(id uuid PRIMARY KEY,user_id uuid REFERENCES auth.users(id),created_at timestamptz NOT NULL DEFAULT clock_timestamp(),not_after timestamptz);');
 for(const file of ['001_identity.sql','002_screening.sql','003_api_contract.sql','004_session_access.sql','005_api_reader.sql','006_password_change.sql','024_login_audit.sql'])await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres',file),'utf8'));
 await q('INSERT INTO auth.users VALUES ($1),($2)',[U(1),U(2)]);
 await q("INSERT INTO user_profiles(user_id,full_name,role,created_by) VALUES ($1,'Sample Admin','admin',NULL),($2,'Sample Parent','parent',$1)",[U(1),U(2)]);
 await q('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[U(3),U(1)]);
 const record=async(subject=U(1),session=U(3))=>(await q('SELECT graphiscan_record_login($1,$2,$3) AS ok',[subject,session,U(4)])).rows[0].ok;
 for(const role of ['anon','authenticated','service_role','graphiscan_api_reader'])check(!(await q("SELECT has_function_privilege($1,'graphiscan_record_login(uuid,uuid,uuid)','EXECUTE') AS ok",[role])).rows[0].ok,'denied '+role);
 await db.exec('SET ROLE graphiscan_password_writer');
 check(await record(),'valid login');check(await record(),'duplicate accepted');check(!await record(U(2)),'wrong actor denied');check(!await record(U(1),U(99)),'missing session denied');
 await db.exec('RESET ROLE');
 check((await q("SELECT count(*)::int AS n FROM audit_logs WHERE action='session.login'")).rows[0].n===1,'exactly one event');
 await q("INSERT INTO app_session_revocations(session_id,user_id,reason) VALUES ($1,$2,'logout')",[U(3),U(1)]);
 check(!await record(),'revoked session denied');
 await q('INSERT INTO auth.sessions(id,user_id,not_after) VALUES ($1,$2,clock_timestamp()-interval \'1 second\')',[U(5),U(1)]);
 check(!await record(U(1),U(5)),'expired session denied');
 await q("UPDATE user_profiles SET account_status='disabled' WHERE user_id=$1",[U(1)]);
 await q('INSERT INTO auth.sessions(id,user_id) VALUES ($1,$2)',[U(6),U(1)]);
 check(!await record(U(1),U(6)),'disabled account denied');
 console.log('Login audit SQL: PASS ('+checks+' isolated checks).');
 }finally{await db.close()}
})().catch(error=>{console.error(error);process.exitCode=1});

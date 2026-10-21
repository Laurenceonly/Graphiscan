// Offline validation of proposed artifacts. Does not import app.py/config.py,
// contact MySQL/Supabase, or claim that v1 handlers enforce these declarations.
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const {createRequire} = require('module');
const root = path.resolve(__dirname, '../..');
const validationRequire = createRequire(path.join(root, '.local-tools/api-validation/package.json'));
let checks = 0;
function check(condition, message) { assert(condition, message); checks++; }

async function main() {
  const Parser = validationRequire('@apidevtools/swagger-parser');
  const Ajv = validationRequire('ajv');
  const addFormats = validationRequire('ajv-formats');
  const {PGlite} = validationRequire('@electric-sql/pglite');
  const file = path.join(root, 'graphiscan/api/openapi.json');
  const spec = await Parser.validate(file, {resolve: {external: false}});
  const ajv = new Ajv({strict: false, allErrors: true});
  addFormats(ajv);
  ajv.addFormat('binary', true);
  const schemas = spec.components.schemas;
  const accept = (name, value, expected) => {
    const validator = ajv.compile(schemas[name]);
    check(validator(value) === expected, `Schema case ${name} expected ${expected}: ${JSON.stringify(validator.errors)}`);
  };
  const ops = Object.entries(spec.paths).flatMap(([route, methods]) => Object.entries(methods).map(([method, op]) => ({route, method: method.toUpperCase(), op})));
  check(ops.length === 33, 'Endpoint count changed; reconcile the prose contract');
  check(new Set(ops.map(x=>x.op.operationId)).size === ops.length, 'Duplicate operation ID');
  const prose = fs.readFileSync(path.join(root, 'API_CONTRACT.md'), 'utf8');
  const catalogue = prose.split('## 5. Endpoint catalogue')[1].split('## 6.')[0];
  const proseOps = [...catalogue.matchAll(/`(GET|POST|PATCH|DELETE) (\/[^` ]+)`/g)].map(m=>m[1]+' '+m[2]);
  check(JSON.stringify(proseOps.sort()) === JSON.stringify(ops.map(x=>x.method+' '+x.route).sort()), 'Prose/OpenAPI endpoint drift');
  for (const {route, method, op} of ops) {
    check(method !== 'DELETE', 'Unresolved deletion policy acquired an endpoint');
    if (['/health','/session/login','/session/refresh'].includes(route)) check(op.security.length === 0, 'Public session/liveness declaration mismatch');
    else check((op.security || spec.security).some(s=>s.BearerAuth), `Missing auth declaration: ${route}`);
    const expectedStatus = (['/health', '/me', '/privacy-agreement', '/schools', '/students', '/students/{student_id}', '/schools/{school_id}/assignment-options','/screenings','/screenings/{result_id}','/students/{student_id}/history','/reports/{report_id}','/models','/screening-requests/{idempotency_key}','/screenings/{result_id}/image'].includes(route) && method === 'GET') ||
      (['/me/password', '/me/privacy-acceptance','/session/login','/session/refresh','/session/logout','/schools','/students','/screenings'].includes(route) && method === 'POST') ||
      (['/schools/{school_id}','/students/{student_id}','/screenings/{result_id}/review','/screenings/{result_id}/expert-assignment'].includes(route) && method === 'PATCH') ? 'foundation' : 'proposed';
    check(op['x-implementation-status'] === expectedStatus, 'Runtime implementation status drift');
    for (const name of [...route.matchAll(/\{([^}]+)\}/g)].map(m=>m[1])) {
      check(op.parameters.some(p=>p.in==='path' && p.name===name && p.required), 'Missing required path parameter');
    }
  }
  check(spec.paths['/screenings'].post['x-roles'].join() === 'teacher', 'Official upload expanded beyond teacher');
  check(spec.paths['/screenings/{result_id}/review'].patch['x-roles'].join() === 'expert', 'Review expanded beyond expert');
  check(spec.paths['/accounts'].post['x-permission'] === 'accounts.manage', 'Account issuance grant missing');
  const cases = JSON.parse(fs.readFileSync(path.join(root, 'graphiscan/api/access-cases.json'), 'utf8')).cases;
  check(new Set(cases.map(c=>c.id)).size === cases.length, 'Duplicate proposed access case');
  for (const c of cases) check(spec.paths[c.path]?.[c.method.toLowerCase()]?.responses[c.expected_status], 'Access case has no specified endpoint/status');
  const student = {full_name:'Synthetic Student',age:8,school_id:'1',grade_level:2};
  accept('StudentCreate', student, true);
  accept('StudentCreate', {...student,grade_level:4}, false);
  accept('StudentCreate', {...student,school_id:1}, false);
  accept('StudentCreate', {...student,full_name:'  '}, false);
  accept('StudentCreate', {...student,role:'admin'}, false);
  accept('BinaryScores', {normal:.4,high_potential:.6}, true);
  accept('BinaryScores', {normal:40,high_potential:60}, false);
  accept('BinaryScores', {normal:.4,high_potential:.5,low_potential:.1}, false);
  accept('ClassScores', null, true);
  accept('TaskClassification', {task_type:'binary',classification:'Low Potential'}, false);
  accept('TaskClassification', {task_type:'binary',classification:'Normal'}, true);
  accept('ReviewWrite', {status:'Validated',remarks:'Synthetic review',follow_up_needed:false,expected_revision:1}, true);
  accept('ReviewWrite', {status:'Flagged',remarks:'Synthetic review',expert_recommendation:null,follow_up_needed:true,expected_revision:1}, true);
  accept('ReviewWrite', {status:'Pending',remarks:'Synthetic review',follow_up_needed:false,expected_revision:1}, false);
  accept('ReviewWrite', {status:'Validated',remarks:' ',follow_up_needed:false,expected_revision:1}, false);
  accept('ReviewWrite', {status:'Validated',remarks:'Review',follow_up_needed:'No',expected_revision:1}, false);
  accept('ReviewWrite', {status:'Validated',remarks:'Review',follow_up_needed:false,expected_revision:0}, false);
  accept('ScreeningUpload', {student_id:'1',handwriting_image:'synthetic-file'}, true);
  accept('ScreeningUpload', {student_id:'1',handwriting_image:'synthetic-file',classification:'Normal'}, false);
  accept('DemoUpload', {student_id:'1',handwriting_image:'synthetic-file'}, false);
  accept('PrivacyAcceptance', {agreement_version:'synthetic',accepted:false}, false);
  const account={full_name:'Synthetic Account',email:'fixture@example.invalid',role:'teacher',temporary_password:'Synthetic!2026Value',school_ids:['1']};
  accept('AccountCreate', account, true);
  accept('AccountCreate', {...account,temporary_password:'weak'}, false);
  accept('AccountCreate', {...account,email:'not-an-email'}, false);
  accept('AccountUpdate', {expected_revision:1,permission_grants:[{permission_key:'accounts.manage',school_id:'1'}]}, true);
  accept('AccountUpdate', {expected_revision:1,permission_grants:[{permission_key:'unknown.power',school_id:null}]}, false);
  for(const {op} of ops)for(const response of Object.values(op.responses)){
    const json=response.content?.['application/json']?.schema;
    if(!json)continue;
    const text=JSON.stringify(json);
    check(!/"(?:temporary_password|current_password|new_password|confirm_password)"\s*:/.test(text),'A response schema exposes a credential field');
  }
  console.log(`OpenAPI structure, declarations, ${cases.length} proposed access cases and payload fixtures: PASS (${checks} checks).`);

  const db = new PGlite();
  let sqlChecks=0;
  const sqlCheck=(value,message)=>{assert(value,message);sqlChecks++;};
  const query=(sql,args=[])=>db.query(sql,args);
  const reject=async(sql,args=[],state)=>{
    await db.exec('BEGIN');let error;
    try { await query(sql,args); } catch(e) { error=e; } finally { await db.exec('ROLLBACK'); }
    sqlCheck(!!error && (!state || error.code===state), `Expected SQL rejection ${state}: ${error?.message || 'accepted'}`);
  };
  const U=n=>`00000000-0000-4000-8000-${String(n).padStart(12,'0')}`;
  try {
    await db.exec(`CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role;
      CREATE SCHEMA auth; CREATE TABLE auth.users (id uuid PRIMARY KEY);
      CREATE TABLE auth.sessions (id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES auth.users(id),
        created_at timestamptz NOT NULL DEFAULT clock_timestamp(), not_after timestamptz);`);
    for(const file of ['001_identity.sql','002_screening.sql','003_api_contract.sql','004_session_access.sql','005_api_reader.sql'])await db.exec(fs.readFileSync(path.join(root,'graphiscan/db/postgres',file),'utf8'));
    const tables=await query("SELECT relname,relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r'");
    sqlCheck(tables.rows.length===20 && tables.rows.every(r=>r.relrowsecurity),'Expected all 20 target tables to enable RLS');
    for(const [n,role]of [[1,'admin'],[2,'teacher'],[3,'parent'],[4,'expert'],[5,'expert']]){
      await query('INSERT INTO auth.users VALUES ($1)',[U(n)]);
      await query('INSERT INTO user_profiles (user_id,full_name,role,created_by) VALUES ($1,$2,$3,$4)',[U(n),'Synthetic '+role,role,n===1?null:U(1)]);
    }
    const school=(await query("INSERT INTO schools(name) VALUES ('Synthetic School') RETURNING school_id")).rows[0].school_id;
    const student=(await query("INSERT INTO students(full_name,age,school_id,grade_level,teacher_id,parent_id) VALUES ('Synthetic Child',8,$1,2,$2,$3) RETURNING student_id",[school,U(2),U(3)])).rows[0].student_id;
    await reject("INSERT INTO students(full_name,school_id,grade_level) VALUES ('Invalid', $1,4)",[school],'23514');
    const beforeGrant=(await query('SELECT revision FROM user_profiles WHERE user_id=$1',[U(1)])).rows[0].revision;
    await query("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES ($1,'accounts.manage',$1)",[U(1)]);
    const afterGrant=(await query('SELECT revision FROM user_profiles WHERE user_id=$1',[U(1)])).rows[0].revision;
    sqlCheck(BigInt(afterGrant)===BigInt(beforeGrant)+1n,'Permission changes did not advance account revision');
    await reject("INSERT INTO user_permission_grants(user_id,permission_key,granted_by) VALUES ($1,'accounts.manage',$1)",[U(1)],'23505');
    await reject("INSERT INTO model_evaluations(task_type,dataset_key,dataset_version,split_key,split_unit,writer_separation_verified,evidence_reference) VALUES ('binary','synthetic','v1','split','image',true,'fixture')",[],'23514');
    const evaluation=(await query("INSERT INTO model_evaluations(task_type,dataset_key,dataset_version,split_key,split_unit,evidence_reference) VALUES ('binary','synthetic','v1','split','image','fixture') RETURNING evaluation_id")).rows[0].evaluation_id;
    const rule=JSON.stringify({kind:'high_potential_threshold',threshold:.75});
    const model=(await query("INSERT INTO model_registry(model_key,model_version,architecture,task_type,test_accuracy,evaluation_id,preprocessing_key,class_labels,decision_rule,provenance,is_selectable,is_default) VALUES ('synthetic','v1','fixture','binary',0.5,$1,'fixture','[\"Normal\",\"High Potential\"]',$2,'verified',true,true) RETURNING model_id",[evaluation,rule])).rows[0].model_id;
    await reject("UPDATE model_registry SET class_labels='[\"Normal\",\"Low Potential\"]' WHERE model_id=$1",[model]);
    const makeResult=async()=>{
      const sample=(await query("INSERT INTO handwriting_samples(student_id,teacher_id,storage_path) VALUES ($1,$2,'private/synthetic-object') RETURNING sample_id",[student,U(2)])).rows[0].sample_id;
      return (await query("INSERT INTO screening_results(sample_id,model_id,task_type,classification,class_probabilities,confidence_score,model_snapshot,decision_rule,provenance) VALUES ($1,$2,'binary','Normal','{\"normal\":0.4,\"high_potential\":0.6}',0.4,'{\"model_key\":\"synthetic\",\"model_version\":\"v1\"}',$3,'verified') RETURNING result_id",[sample,model,rule])).rows[0].result_id;
    };
    const result=await makeResult();
    const second=await makeResult();
    sqlCheck(!!result,'Threshold-based Normal with class score below max accepted');
    await reject('UPDATE model_registry SET model_version=\'changed\' WHERE model_id=$1',[model],'P0001');
    await reject("UPDATE screening_results SET classification='High Potential' WHERE result_id=$1",[result],'P0001');
    await reject("INSERT INTO screening_results(sample_id,model_id,task_type,classification,confidence_score) SELECT sample_id,$1,'binary','Normal',90 FROM handwriting_samples LIMIT 1",[model],'22003');
    sqlCheck((await query("SELECT public.valid_class_scores('{\"normal\":40,\"high_potential\":60}','binary') AS ok")).rows[0].ok===false,'Percentage vector accepted');
    sqlCheck((await query("SELECT public.valid_class_scores('{\"normal\":0.4,\"high_potential\":0.5,\"low_potential\":0.1}','binary') AS ok")).rows[0].ok===false,'Binary vector accepted low class');
    sqlCheck((await query("SELECT public.valid_class_scores('{\"normal\":0.4,\"high_potential\":0.3}','binary') AS ok")).rows[0].ok===false,'Unnormalized vector accepted');
    sqlCheck((await query("SELECT public.valid_class_labels('[\"Normal\",\"Low Potential\"]','binary') AS ok")).rows[0].ok===false,'Binary model accepted low-potential class');
    sqlCheck((await query("SELECT public.valid_decision_rule('{\"kind\":\"high_potential_threshold\",\"threshold\":75}','binary') AS ok")).rows[0].ok===false,'Percentage cutoff accepted');
    await query("INSERT INTO expert_validations(result_id,provenance) VALUES ($1,'verified')",[result]);
    const originalRevision=(await query('SELECT revision FROM expert_validations WHERE result_id=$1',[result])).rows[0].revision;
    await query('INSERT INTO screening_expert_assignments(result_id,assigned_expert_id,assigned_by) VALUES ($1,$2,$3)',[result,U(4),U(1)]);
    const assigned=(await query('SELECT revision FROM expert_validations WHERE result_id=$1',[result])).rows[0].revision;
    sqlCheck(BigInt(assigned)===BigInt(originalRevision)+1n,'Assignment failed to advance review revision');
    const stale=await query("UPDATE expert_validations SET remarks='stale' WHERE result_id=$1 AND revision=$2 RETURNING result_id",[result,originalRevision]);
    sqlCheck(stale.rows.length===0,'Stale conditional update overwrote review');
    await reject("UPDATE expert_validations SET status='Validated',remarks=' ',expert_id=$2,validation_date=now() WHERE result_id=$1",[result,U(4)],'23514');
    await query("UPDATE expert_validations SET status='Validated',remarks='Synthetic review',expert_id=$2,validation_date=now() WHERE result_id=$1",[result,U(4)]);
    await query('UPDATE screening_expert_assignments SET assigned_expert_id=$2 WHERE result_id=$1',[result,U(5)]);
    sqlCheck((await query('SELECT expert_id FROM expert_validations WHERE result_id=$1',[result])).rows[0].expert_id===U(4),'Reassignment rewrote reviewer authorship');
    sqlCheck((await query('SELECT count(*)::int AS n FROM expert_review_history WHERE result_id=$1',[result])).rows[0].n===2,'Expected Pending and actual decision history, not a new decision on assignment');
    await reject("UPDATE expert_review_history SET remarks='tampered' WHERE result_id=$1",[result],'P0001');
    await query("INSERT INTO screening_reports(student_id,result_id,report_type,school_context) VALUES ($1,$2,'Initial Screening','{\"school_id\":\"1\",\"school_name\":\"Synthetic\",\"grade_level\":2}')",[student,result]);
    await reject("INSERT INTO screening_reports(student_id,result_id,report_type) VALUES ($1,$2,'Initial Screening')",[student,second],'23505');
    await query("INSERT INTO screening_reports(student_id,result_id,report_type) VALUES ($1,$2,'Follow-up Screening')",[student,second]);
    await reject("UPDATE screening_reports SET report_type='Follow-up Screening' WHERE result_id=$1",[result],'P0001');
    await reject("INSERT INTO privacy_agreements(version,title,content,content_sha256,is_current) VALUES ('unapproved','Synthetic','Fixture',$1,true)",['a'.repeat(64)],'23514');
    await query("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES ('synthetic-v1','Synthetic','Test fixture only',$1,$2,now(),now(),true)",['a'.repeat(64),U(1)]);
    await reject("INSERT INTO privacy_agreements(version,title,content,content_sha256,approved_by,approved_at,published_at,is_current) VALUES ('synthetic-v2','Synthetic','Fixture',$1,$2,now(),now(),true)",['b'.repeat(64),U(1)],'23505');
    await reject("UPDATE privacy_agreements SET content='changed' WHERE version='synthetic-v1'",[],'P0001');
    await query("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES ($1,'synthetic-v1')",[U(2)]);
    await reject("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES ($1,'synthetic-v1')",[U(2)],'23505');
    await reject("INSERT INTO privacy_agreement_acceptances(user_id,agreement_version) VALUES ($1,'missing')",[U(3)],'23503');
    await query("INSERT INTO api_requests(actor_id,operation,idempotency_key,request_digest,state) VALUES ($1,'screenings.create','synthetic-request-key',$2,'processing')",[U(2),'c'.repeat(64)]);
    await reject("INSERT INTO api_requests(actor_id,operation,idempotency_key,request_digest,state) VALUES ($1,'screenings.create','synthetic-request-key',$2,'processing')",[U(2),'c'.repeat(64)],'23505');
    await reject("UPDATE api_requests SET state='completed' WHERE actor_id=$1",[U(2)],'23514');
    await query("UPDATE api_requests SET state='completed',result_id=$2 WHERE actor_id=$1",[U(2),result]);
    await db.exec('CREATE ROLE contract_client; GRANT USAGE ON SCHEMA public TO contract_client; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO contract_client; GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO contract_client;');
    await db.exec('BEGIN; SET LOCAL ROLE contract_client;');
    sqlCheck((await query('SELECT count(*)::int AS n FROM students')).rows[0].n===0,'RLS leaked students to direct client role');
    let rlsError;
    try { await query("INSERT INTO schools(name) VALUES ('Unauthorized')"); } catch(e) { rlsError=e; }
    await db.exec('ROLLBACK');
    sqlCheck(rlsError?.code==='42501','RLS allowed direct client insertion');
    console.log(`Isolated PostgreSQL migration/constraint/trigger/RLS checks: PASS (${sqlChecks} checks; no live database used).`);
    await require('./check_v1_access_sql.cjs')({db, root, U});
    await require('./check_v1_password_sql.cjs')({db, root, U});
    await require('./check_v1_privacy_sql.cjs')({db, root, U});
    await require('./check_v1_sessions_sql.cjs')({db, root, U});
    await require('./check_v1_directory_sql.cjs')({db, root, U});
    await require('./check_v1_directory_writes_sql.cjs')({db, root, U});
    await require('./check_v1_assignment_options_sql.cjs')({db, root, U});
    await require('./check_v1_screenings_sql.cjs')({db, root, U, validateRow:(name,row)=>{
      const validator=ajv.compile(schemas[name]);return {ok:validator(row),errors:validator.errors};
    }});
  } finally { await db.close(); }
}
main().catch(error=>{console.error('Contract validation FAILED: '+error.message+
  (error.position ? ' (SQL position '+error.position+')' : '')+
  (error.internalPosition ? ' (function position '+error.internalPosition+')' : ''));process.exitCode=1;});

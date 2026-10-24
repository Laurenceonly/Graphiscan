// Execute the actual publication/rollback in disposable PostgreSQL only.
import fs from 'node:fs/promises'
import path from 'node:path'
import {fileURLToPath,pathToFileURL} from 'node:url'
import assert from 'node:assert/strict'
import crypto from 'node:crypto'

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..')
const validation=process.env.GRAPHISCAN_VALIDATION_ROOT||path.join(root,'.local-tools/api-validation')
const {PGlite}=await import(pathToFileURL(path.join(validation,'node_modules/@electric-sql/pglite/dist/index.js')))
const db=new PGlite()
const read=name=>fs.readFile(path.join(root,'graphiscan/db/postgres',name+'.sql'),'utf8')
let checks=0
const check=(actual,expected)=>{assert.deepEqual(actual,expected);checks++}
const rows=async()=> (await db.query('SELECT model_id,model_key,model_version,is_selectable,is_default FROM model_registry ORDER BY model_id')).rows
const evaluate=async sql=>{await assert.rejects(db.exec(sql));checks++;await db.exec('ROLLBACK')}
try {
  await db.exec('CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY); CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role;')
  for(const migration of ['001_identity','002_screening','003_api_contract'])await db.exec(await read(migration))
  await db.exec(await read('publish_binary_models'))
  const before=await rows()
  check(before.length,3)
  check(before.filter(row=>row.is_default).map(row=>row.model_key),['mobilenetv2'])
  await db.exec('CREATE TABLE fictional_history(model_id bigint PRIMARY KEY REFERENCES model_registry(model_id)); INSERT INTO fictional_history SELECT model_id FROM model_registry;')
  const publication=await read('publish_lite_binary_models'), rollback=await read('rollback_lite_binary_models')
  await db.exec(publication)
  const published=await rows()
  check(published.length,6)
  check(published.filter(row=>row.is_selectable).length,3)
  check(published.filter(row=>row.is_default).map(row=>row.model_key),['mobilenetv2'])
  check(published.find(row=>row.is_default).model_version.endsWith('-litert-fp32-v1'),true)
  check(published.filter(row=>before.some(prior=>prior.model_id===row.model_id)).map(row=>row.is_selectable),[false,false,false])
  await db.exec('INSERT INTO fictional_history SELECT model_id FROM model_registry ON CONFLICT DO NOTHING')
  const countEvaluations=async()=>Number((await db.query('SELECT count(*) n FROM model_evaluations')).rows[0].n)
  const evaluationCount=await countEvaluations()
  await db.exec(publication)
  check(await rows(),published)
  check(await countEvaluations(),evaluationCount)
  await db.exec(rollback)
  const reverted=await rows()
  check(reverted.slice(0,3),before)
  check(reverted.slice(3).map(row=>[row.is_selectable,row.is_default]),[[false,false],[false,false],[false,false]])
  check(Number((await db.query('SELECT count(*) n FROM fictional_history')).rows[0].n),6)
  await db.exec(rollback)
  check(await rows(),reverted)
  await db.exec(publication)
  check(await rows(),published)
  check(await countEvaluations(),evaluationCount)

  // A different current default must survive a rejected cutover/rollback.
  await db.exec(`UPDATE model_registry SET is_default=false WHERE is_default;
    INSERT INTO model_registry(model_key,model_version,architecture,task_type,test_accuracy,is_selectable,is_default,
      evaluation_id,preprocessing_key,class_labels,decision_rule,provenance)
    SELECT 'fictional-other','fictional-version',architecture,task_type,test_accuracy,true,true,
      evaluation_id,preprocessing_key,class_labels,decision_rule,provenance FROM model_registry ORDER BY model_id LIMIT 1;`)
  const foreign=await rows()
  await evaluate(publication);check(await rows(),foreign)
  await evaluate(rollback);check(await rows(),foreign)
  await db.exec("DELETE FROM model_registry WHERE model_key='fictional-other'")
  const selected=published.find(row=>row.is_default)
  await db.query('UPDATE model_registry SET is_default=true WHERE model_id=$1',[selected.model_id])

  // Previously reviewed metadata must not be silently overwritten.
  const old=before.find(row=>row.model_key==='resnet50')
  const accuracy=(await db.query('SELECT test_accuracy FROM model_registry WHERE model_id=$1',[old.model_id])).rows[0].test_accuracy
  await db.query('UPDATE model_registry SET test_accuracy=.1 WHERE model_id=$1',[old.model_id])
  const conflict=await rows()
  await evaluate(publication);check(await rows(),conflict)
  await db.query('UPDATE model_registry SET test_accuracy=$1 WHERE model_id=$2',[accuracy,old.model_id])

  // evidence_reference has no unique constraint; duplicate evidence must fail.
  const evidence=await fs.readFile(path.join(root,'graphiscan/api/litert-linux-evaluation.json'))
  const reference='sha256:'+crypto.createHash('sha256').update(evidence).digest('hex')
  const duplicate=(await db.query(`INSERT INTO model_evaluations(task_type,dataset_key,dataset_version,split_key,split_unit,
    writer_separation_verified,evidence_reference) SELECT task_type,dataset_key,dataset_version,split_key,split_unit,
    writer_separation_verified,evidence_reference FROM model_evaluations WHERE evidence_reference=$1 RETURNING evaluation_id`,[reference])).rows[0].evaluation_id
  await evaluate(publication);check(await rows(),published)
  await db.query('DELETE FROM model_evaluations WHERE evaluation_id=$1',[duplicate])
  check(Number((await db.query('SELECT count(*) n FROM fictional_history')).rows[0].n),6)
  console.log(JSON.stringify({status:'isolated-model-cutover-passed',checks,hosted_connections:0,production_writes:0}))
} finally {await db.close()}

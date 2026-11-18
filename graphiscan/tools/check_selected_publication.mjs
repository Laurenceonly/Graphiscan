// Execute the selected-model transaction only in disposable PostgreSQL.
import fs from 'node:fs/promises'
import path from 'node:path'
import {fileURLToPath,pathToFileURL} from 'node:url'
import assert from 'node:assert/strict'
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..')
const {PGlite}=await import(pathToFileURL(path.join(root,'.local-tools/api-validation/node_modules/@electric-sql/pglite/dist/index.js')))
const db=new PGlite()
const read=name=>fs.readFile(path.join(root,'graphiscan/db/postgres',name+'.sql'),'utf8')
let checks=0
const check=(a,b)=>{assert.deepEqual(a,b);checks++}
const rows=async()=> (await db.query('SELECT * FROM model_registry ORDER BY model_id')).rows
const reject=async(sql)=>{await assert.rejects(db.exec(sql));checks++;await db.exec('ROLLBACK')}
try {
  await db.exec('CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY); CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role;')
  for(const name of ['001_identity','002_screening','003_api_contract','publish_binary_models','publish_lite_binary_models'])await db.exec(await read(name))
  await db.exec('CREATE TABLE fictional_history(model_id bigint REFERENCES model_registry(model_id)); INSERT INTO fictional_history SELECT model_id FROM model_registry;')
  const before=await rows(), publish=await read('publish_selected_binary_models'), rollback=await read('rollback_selected_binary_models')
  await db.exec(publish)
  const after=await rows(), active=after.filter(r=>r.is_selectable)
  check(after.length,8);check(active.length,3)
  check(active.find(r=>r.is_default).model_version,'binary-3abdc7ee4b2b-litert-fp32-v1')
  check(active.find(r=>r.model_key==='efficientnetb0').test_accuracy,'0.78676')
  check(active.find(r=>r.model_key==='resnet50').test_accuracy,'0.86765')
  check(after.slice(0,6).map(r=>[r.model_id,r.model_version,r.test_accuracy]),before.map(r=>[r.model_id,r.model_version,r.test_accuracy]))
  await db.exec('INSERT INTO fictional_history SELECT model_id FROM model_registry WHERE model_id>6')
  await db.exec(publish);check(await rows(),after)
  const setDefault=await read('set_resnet_selected_default')
  await db.exec(setDefault)
  check((await rows()).filter(r=>r.is_default).map(r=>r.model_version),['binary-55e0844c9896-litert-fp32-v1'])
  await db.exec(setDefault)
  check((await rows()).filter(r=>r.is_default).map(r=>r.model_key),['resnet50'])
  await db.exec("UPDATE model_registry SET is_default=false WHERE is_default; UPDATE model_registry SET is_default=true WHERE model_version='binary-3abdc7ee4b2b-litert-fp32-v1'")
  await db.exec(rollback)
  check((await rows()).slice(0,6),before)
  check((await rows()).slice(6).map(r=>r.is_selectable),[false,false])
  await db.exec(rollback);check((await rows()).slice(0,6),before)
  await db.exec(publish);check(await rows(),after)
  await db.exec("UPDATE model_registry SET test_accuracy=.1 WHERE model_version='binary-e141366a992c-litert-fp32-v1'")
  const conflict=await rows();await reject(publish);check(await rows(),conflict)
  await db.exec("UPDATE model_registry SET test_accuracy=.72794 WHERE model_version='binary-e141366a992c-litert-fp32-v1'")
  const newConflict=await rows();await reject(publish.replace('"test_accuracy":0.86765','"test_accuracy":0.1'));check(await rows(),newConflict)
  await db.exec("UPDATE model_registry SET is_default=false; UPDATE model_registry SET is_default=true WHERE model_version='binary-55e0844c9896-litert-fp32-v1'")
  const foreign=await rows();await reject(publish);check(await rows(),foreign);await reject(rollback);check(await rows(),foreign)
  check(Number((await db.query('SELECT count(*) n FROM fictional_history')).rows[0].n),8)
  console.log(JSON.stringify({status:'selected-cutover-passed',checks,hosted_connections:0,production_writes:0}))
} finally {await db.close()}

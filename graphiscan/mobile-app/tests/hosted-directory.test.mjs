import test from 'node:test'
import assert from 'node:assert/strict'
import {recordId,studentPayload,studentQuery} from '../src/core/hosted-directory.ts'

const form={name:'  Fictional   Student ',age:'8',school:'9007199254740993',grade:'1',parent:''}
test('creation matches the hosted contract and leaves teacher ownership to the server',()=>{
  assert.deepEqual(studentPayload(form),{full_name:'Fictional Student',age:8,school_id:'9007199254740993',grade_level:1,parent_id:null})
  assert.equal('teacher_id' in studentPayload(form),false)
})
test('edits cannot move schools; only a historically unknown age may stay omitted',()=>{
  assert.equal('school_id' in studentPayload(form,true),false)
  assert.throws(()=>studentPayload({...form,age:''},true),/age/)
  const body=studentPayload({...form,age:''},true,true)
  assert.equal('age' in body,false);assert.equal('school_id' in body,false)
})
test('names preserve meaningful Unicode, normalize whitespace, and reject controls or empty values',()=>{
  assert.equal(studentPayload({...form,name:'  Fictional  Niño  '}).full_name,'Fictional Niño')
  for(const name of ['','   ','Bad\nName','Bad\u007fName','a'.repeat(201)])assert.throws(()=>studentPayload({...form,name}))
})
test('ages and grades match the existing server bounds',()=>{
  for(const age of ['', '0','-1','8.5','Infinity','32768','words'])assert.throws(()=>studentPayload({...form,age}))
  assert.equal(studentPayload({...form,age:'32767'}).age,32767)
  for(const grade of ['', '0','4','Grade 1'])assert.throws(()=>studentPayload({...form,grade}))
})
test('canonical int64 identifiers never pass through floating-point numbers',()=>{
  for(const value of ['1','9007199254740993','9223372036854775807'])assert.equal(recordId(value),true)
  for(const value of [1,null,undefined,'0','01','-1','1.5','9223372036854775808','12345678901234567890'])assert.equal(recordId(value),false)
})
test('search/school/grade filters are server parameters with an opaque encoded cursor',()=>{
  assert.equal(studentQuery({search:'  A&B +  ',school:form.school,grade:'2'},'opaque+/='),'/students?limit=25&q=A%26B%20%2B&school_id=9007199254740993&grade_level=2&cursor=opaque%2B%2F%3D')
  assert.equal(studentQuery({search:'',school:'',grade:''}),'/students?limit=25')
})
test('invalid filters cannot be turned into a directory request',()=>{
  for(const filters of [{search:'a'.repeat(121),school:'',grade:''},{search:'bad\u0000name',school:'',grade:''},{search:'',school:'01',grade:''},{search:'',school:'',grade:'4'}])assert.throws(()=>studentQuery(filters))
})

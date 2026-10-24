export interface School { school_id: string; name: string }
export interface Student {
  student_id: string; full_name: string; age: number | null; school_id: string;
  grade_level: number; teacher_id: string | null; parent_id: string | null; revision: number;
}
export interface AssignmentOption { user_id: string; full_name: string; role: string }
export interface StudentForm { name: string; age: string; school: string; grade: string; parent: string }
export interface StudentFilters { search: string; school: string; grade: string }

export function recordId(value: string) {
  return typeof value==='string' && /^[1-9][0-9]{0,18}$/.test(value) && (value.length < 19 || value <= '9223372036854775807')
}
export function studentPayload(form: StudentForm, editing = false, unknownAge = false) {
  if (/[\u0000-\u001f\u007f]/.test(form.name)) throw new Error('Enter the student name without control characters.')
  const full_name=form.name.trim().replace(/\s+/g,' ')
  if (!full_name || full_name.length > 200) throw new Error('Enter a student name of 1 to 200 characters.')
  if (!recordId(form.school)) throw new Error('Choose an available school.')
  if (!['1','2','3'].includes(form.grade)) throw new Error('Choose Grade 1, 2 or 3.')
  if ((!editing || !unknownAge || form.age.trim()) && (!/^[0-9]+$/.test(form.age) || Number(form.age)<1 || Number(form.age)>32767)) {
    throw new Error('Enter a valid whole-number age.')
  }
  const body: { full_name:string; grade_level:number; parent_id:string|null; age?:number; school_id?:string }={full_name,grade_level:Number(form.grade),parent_id:form.parent||null}
  if (form.age.trim()) body.age=Number(form.age)
  if (!editing) body.school_id=form.school
  return body
}
export function studentQuery(filters: StudentFilters, cursor: string | null = null) {
  const search=filters.search.trim()
  if (search.length>120 || /[\u0000-\u001f\u007f]/.test(search)) throw new Error('Use a search of up to 120 characters without control characters.')
  if (filters.school && !recordId(filters.school)) throw new Error('Choose an available school.')
  if (filters.grade && !['1','2','3'].includes(filters.grade)) throw new Error('Choose Grade 1, 2 or 3.')
  const pairs=[['limit','25']]
  if(search)pairs.push(['q',search])
  if(filters.school)pairs.push(['school_id',filters.school])
  if(filters.grade)pairs.push(['grade_level',filters.grade])
  if(cursor)pairs.push(['cursor',cursor])
  return '/students?'+pairs.map(([key,value])=>key+'='+encodeURIComponent(value)).join('&')
}

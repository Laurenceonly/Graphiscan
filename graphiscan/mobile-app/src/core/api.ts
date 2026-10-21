// Conversion adapter for the EXISTING /api/user contract. No Supabase-token bridge.
export type Role = 'teacher' | 'expert' | 'parent'
export interface User { user_id: number; fullname: string; email: string; role: Role; account_status: string }
export interface Student { student_id: number; fullname: string; age: number | null; grade_level: string; parent_name?: string }
export interface Result {
  result_id: number; student_id?: number; student_name: string; classification: string;
  confidence_score?: number | string | null; dysgraphia_probability?: number | string | null;
  validation_status?: string; date_generated?: string; grade_level?: string; age?: number;
  remarks?: string; expert_recommendation?: string; follow_up_needed?: string;
  expert_name?: string; validation_date?: string; parent_name?: string; teacher_name?: string;
  report_type?: string;
}
export class ApiFailure extends Error {
  status: number
  constructor(message: string, status = 0) { super(message); this.status = status }
}
export function createUserApi(origin: string, options: { fetchImpl?: typeof fetch; onExpired?: () => void } = {}) {
  const trusted = new URL(origin)
  if (!['http:', 'https:'].includes(trusted.protocol) || trusted.username || trusted.password ||
      trusted.search || trusted.hash || trusted.pathname !== '/') throw new Error('Configure a public API origin.')
  const base = trusted.origin + '/api/user'
  const send = options.fetchImpl ?? fetch
  let token: string | null = null, generation = 0
  function clear() { token = null; generation++ }
  async function request(path: string, init: { method?: string; body?: unknown; form?: FormData; image?: boolean; timeout?: number; bearer?: string } = {}): Promise<any> {
    if (!path.startsWith('/') || path.startsWith('//') || path.includes('://')) throw new ApiFailure('Invalid request.')
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), init.timeout ?? 15000)
    const bearer = init.bearer ?? token
    const expectedGeneration = generation
    try {
      const response = await send(base + path, {
        method: init.method ?? 'GET', credentials: 'omit', cache: 'no-store', signal: controller.signal,
        headers: { ...(bearer ? { Authorization: 'Bearer ' + bearer } : {}),
          ...(init.body ? { 'Content-Type': 'application/json' } : {}) },
        ...(init.form ? { body: init.form } : init.body ? { body: JSON.stringify(init.body) } : {})
      })
      if (bearer && generation !== expectedGeneration) throw new ApiFailure('This request belongs to an ended session.')
      if (init.image && response.ok) {
        const type = (response.headers.get('Content-Type') ?? '').split(';')[0]
        if (!['image/png', 'image/jpeg'].includes(type)) throw new ApiFailure('The image response was invalid.')
        return response.blob()
      }
      const data = await response.json().catch(() => ({}))
      if (bearer && generation !== expectedGeneration) throw new ApiFailure('This request belongs to an ended session.')
      if (!response.ok || data.success !== true) {
        if (response.status === 401 && bearer === token) { clear(); options.onExpired?.() }
        throw new ApiFailure(data.message || 'The request could not be completed.', response.status)
      }
      return data
    } catch (error) {
      if (error instanceof ApiFailure) throw error
      throw new ApiFailure('Unable to reach GraphiScan. Check your connection and try again.')
    } finally { clearTimeout(timer) }
  }
  return {
    clear, request,
    async login(email: string, password: string): Promise<User> {
      clear()
      const expected = generation
      const data = await request('/login', { method: 'POST', body: { email: email.trim().toLowerCase(), password } })
      const supported = ['teacher', 'expert', 'parent'].includes(data.user?.role)
      if (!supported || typeof data.token !== 'string' || !data.token || generation !== expected) {
        if (typeof data.token === 'string') await request('/logout', { method: 'POST', bearer: data.token }).catch(() => {})
        throw new ApiFailure(supported ? 'This sign-in was cancelled. Try again.' : 'Use an issued teacher, expert or parent account.')
      }
      token = data.token
      return data.user
    },
    async logout() {
      const old = token
      clear()
      if (old) await request('/logout', { method: 'POST', bearer: old })
    },
    students: () => request('/teacher/students').then(data => data.students as Student[]),
    parents: () => request('/teacher/parents').then(data => data.parents as { user_id: number; fullname: string }[]),
    results: (role: Role) => request('/' + role + '/results').then(data =>
      (data.results as Result[]).filter(row => role !== 'parent' || row.validation_status === 'Validated')),
    result: (role: Role, id: string) => request('/' + role + '/results/' + encodeURIComponent(id)).then(data => data.result as Result),
    progress: (role: Role, id: string) => request('/' + role + '/students/' + encodeURIComponent(id) + '/progress'),
    image: (id: string) => request('/results/' + encodeURIComponent(id) + '/download-image', { image: true }) as Promise<Blob>
  }
}
export type UserApi = ReturnType<typeof createUserApi>

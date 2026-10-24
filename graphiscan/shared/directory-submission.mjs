// Retain the exact creation payload/key after an uncertain result. Memory only.
export function createStudentSubmission(makeKey = () => globalThis.crypto.randomUUID()) {
  let pending = null
  return {
    get pending() { return pending !== null },
    async submit(client, draft) {
      if (!pending) pending = { key: makeKey(), body: JSON.parse(JSON.stringify(draft)) }
      try {
        const result = await client.request('/students', { method: 'POST', envelope: true,
          idempotencyKey: pending.key, body: JSON.parse(JSON.stringify(pending.body)) })
        const id = result?.data?.student_id
        if (typeof id !== 'string' || !/^[1-9][0-9]{0,18}$/.test(id) ||
            (id.length === 19 && id > '9223372036854775807')) {
          throw new Error('Saving could not be confirmed. Retry this same submission.')
        }
        pending = null
        return result
      } catch (error) {
        if (error.status === 400 || error.status === 422) pending = null
        throw error
      }
    }
  }
}

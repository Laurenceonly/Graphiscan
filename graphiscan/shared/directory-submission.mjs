// Retain the exact creation payload/key after an uncertain result. Memory only.
export function createStudentSubmission(makeKey = () => globalThis.crypto.randomUUID()) {
  let pending = null
  return {
    get pending() { return pending !== null },
    async submit(client, draft) {
      if (!pending) pending = { key: makeKey(), body: structuredClone(draft) }
      try {
        const result = await client.request('/students', { method: 'POST', envelope: true,
          idempotencyKey: pending.key, body: structuredClone(pending.body) })
        pending = null
        return result
      } catch (error) {
        if (error.status === 400 || error.status === 422) pending = null
        throw error
      }
    }
  }
}

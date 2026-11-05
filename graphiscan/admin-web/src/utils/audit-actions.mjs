const labels = {
  'session.login':'Signed in', 'session.logout':'Signed out',
  'schools.create':'Added school', 'schools.update':'Edited school',
  'students.create':'Added student', 'students.update':'Edited student',
  'accounts.updated':'Edited account', 'accounts.assignments.updated':'Updated account assignments',
  'screenings.create':'Added screening', 'screenings.review':'Reviewed screening',
  'screenings.expert_assignment':'Assigned screening expert',
  'assignments.eligibility.granted':'Granted assignment eligibility',
  'assignments.eligibility.revoked':'Removed assignment eligibility',
  'privacy.accepted':'Accepted privacy notice',
  'password_change.started':'Started password change', 'password_change.completed':'Changed password',
}
export function auditActionLabel(action) {
  if (labels[action]) return labels[action]
  if (String(action).startsWith('account.created:')) return 'Created account'
  const match = /^accounts\.(delete|reset_password|disable|activate)\.(started|completed)$/.exec(action || '')
  if (match) {
    const operations = {delete:['account deletion','Deleted account'],reset_password:['password reset','Reset account password'],disable:['account deactivation','Disabled account'],activate:['account activation','Activated account']}
    return match[2] === 'started' ? 'Started ' + operations[match[1]][0] : operations[match[1]][1]
  }
  return action || 'Activity not recorded'
}

// Search the same recorded codes the server authorizes and pages. Translate an
// exact displayed action phrase so users can search the labels they can see.
export function auditSearchQuery(value) {
  const query = value.trim()
  const known = Object.entries(labels).find(([, label]) => label.toLowerCase() === query.toLowerCase())
  if (known) return known[0]
  const extras = {'created account':'account.created:', 'deleted account':'accounts.delete.completed', 'started account deletion':'accounts.delete.started', 'reset account password':'accounts.reset_password.completed'}
  return extras[query.toLowerCase()] || query
}

import type { Result } from './api'
export function screeningType(value?: string | null): string {
  return value === 'Initial Screening' || value === 'Follow-up Screening' ? value : 'Screening type not recorded'
}
export function legacyPercent(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return 'Not recorded'
  const score = Number(String(value).replace('%', '').trim())
  return Number.isFinite(score) && score >= 0 && score <= 100 ? score.toFixed(2) + '%' : 'Not recorded'
}
export function dateLabel(value?: string): string {
  if (!value) return 'Not recorded'
  const date = new Date(value.replace(' ', 'T'))
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}
export function resultCounts(results: Result[]) {
  return {
    total: results.length,
    pending: results.filter(r => !r.validation_status || r.validation_status === 'Pending').length,
    reviewed: results.filter(r => r.validation_status === 'Validated').length,
    followUp: results.filter(r => r.follow_up_needed === 'Yes').length
  }
}

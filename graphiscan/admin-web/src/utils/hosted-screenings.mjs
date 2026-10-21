export function formatScore(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
    ? (value * 100).toFixed(1) + '%' : 'Score not recorded'
}

export function formatReportType(value) {
  return ['Initial Screening', 'Follow-up Screening'].includes(value) ? value : 'Screening type not recorded'
}

// Hosted v1 scores use fractions. Keep this separate from legacy percent units.
export function hostedPercent(value: unknown): string {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1 ? (value * 100).toFixed(2) + '%' : 'Not recorded'
}

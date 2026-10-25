// Display names match the server's supported architecture names; keys stay unchanged.
export function modelLabel(value: unknown): string {
  if (typeof value !== 'string' || !value.trim()) return 'Model not recorded'
  const names: Record<string, string> = { mobilenetv2: 'MobileNetV2', resnet50: 'ResNet50', efficientnetb0: 'EfficientNetB0' }
  return names[value.toLowerCase()] ?? value
}

// Hosted v1 scores use fractions. Keep this separate from legacy percent units.
export function hostedPercent(value: unknown): string {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1 ? (value * 100).toFixed(2) + '%' : 'Not recorded'
}

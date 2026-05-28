export function compareVersions(left: string, right: string): number {
  const leftParts = String(left || '')
    .split('.')
    .map((part) => Number.parseInt(part, 10) || 0)
  const rightParts = String(right || '')
    .split('.')
    .map((part) => Number.parseInt(part, 10) || 0)
  const maxLength = Math.max(leftParts.length, rightParts.length)

  for (let index = 0; index < maxLength; index += 1) {
    const leftValue = leftParts[index] ?? 0
    const rightValue = rightParts[index] ?? 0
    if (leftValue > rightValue) return 1
    if (leftValue < rightValue) return -1
  }

  return 0
}

export function buildMockDownloadProgressSteps(stepCount: number): number[] {
  return Array.from({ length: stepCount }, (_value, index) =>
    Math.round((((index + 1) / stepCount) * 1000)) / 10
  )
}

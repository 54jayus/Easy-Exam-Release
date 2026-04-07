export function useProctoringOptimizationMetrics() {
  const formatVariance = (val: any) => {
    if (val === undefined || val === null) return '-'
    return Number(val).toFixed(2)
  }

  const getVal = (m: any, key: string) => {
    if (!m) return 0
    const snake = key.replace(/[A-Z]/g, (l) => `_${l.toLowerCase()}`)
    return Number(m[key] ?? m[snake] ?? 0)
  }

  const getDiff = (before: any, after: any, key: string) => {
    const v1 = getVal(before, key)
    const v2 = getVal(after, key)
    const diff = v2 - v1
    if (Math.abs(diff) < 0.001) return ''
    const txt = Number.isInteger(diff) ? String(diff) : diff.toFixed(2)
    return diff > 0 ? `+${txt}` : `${txt}`
  }

  const getDiffClass = (before: any, after: any, key: string) => {
    const v1 = getVal(before, key)
    const v2 = getVal(after, key)
    return v2 < v1 ? 'text-emerald-600 font-bold' : (v2 > v1 ? 'text-rose-500 font-bold' : 'text-slate-400')
  }

  return {
    formatVariance,
    getDiff,
    getDiffClass,
  }
}

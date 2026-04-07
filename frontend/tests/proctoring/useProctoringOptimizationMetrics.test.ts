import { describe, expect, it } from 'vitest'
import { useProctoringOptimizationMetrics } from '@/views/ProctoringPage/composables/useProctoringOptimizationMetrics'

describe('useProctoringOptimizationMetrics', () => {
  it('formats variance and computes diffs for mixed key styles', () => {
    const metrics = useProctoringOptimizationMetrics()

    expect(metrics.formatVariance(2)).toBe('2.00')
    expect(metrics.formatVariance(null)).toBe('-')

    const before = { max_load: 10, variance: 1.25 }
    const after = { maxLoad: 8, variance: 1.0 }

    expect(metrics.getDiff(before, after, 'maxLoad')).toBe('-2')
    expect(metrics.getDiffClass(before, after, 'maxLoad')).toBe('text-emerald-600 font-bold')
    expect(metrics.getDiff(before, after, 'variance')).toBe('-0.25')
  })
})

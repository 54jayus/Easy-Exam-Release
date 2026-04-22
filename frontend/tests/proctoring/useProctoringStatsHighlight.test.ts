import { nextTick, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { useProctoringStatsHighlight } from '@/views/ProctoringPage/composables/useProctoringStatsHighlight'

describe('useProctoringStatsHighlight', () => {
  it('highlights the clicked row and related rows by previous supervision duration', () => {
    const teacherStats = ref([
      { id: 't1', name: '张老师', previousSupervisionDuration: 120 },
      { id: 't2', name: '李老师', previousSupervisionDuration: 120 },
      { id: 't3', name: '王老师', previousSupervisionDuration: 60 },
    ])

    const highlight = useProctoringStatsHighlight({ teacherStats })

    highlight.handleTeacherStatsCellClick(
      teacherStats.value[0],
      { property: 'previousSupervisionDuration' }
    )

    expect(highlight.getTeacherStatsRowClassName({ row: teacherStats.value[0] })).toBe('teacher-stats-row-selected')
    expect(highlight.getTeacherStatsRowClassName({ row: teacherStats.value[1] })).toBe('teacher-stats-row-related')
    expect(highlight.getTeacherStatsRowClassName({ row: teacherStats.value[2] })).toBe('')
    expect(
      highlight.getTeacherStatsCellClassName({
        row: teacherStats.value[0],
        column: { property: 'previousSupervisionDuration' },
      })
    ).toContain('teacher-stats-prev-duration-cell-selected')
    expect(highlight.getTeacherStatsDurationTextClass(teacherStats.value[1])).toBe('font-medium text-amber-700')
  })

  it('treats zero duration rows as clickable and related', () => {
    const teacherStats = ref([
      { id: 't1', name: '张老师', previousSupervisionDuration: 0 },
      { id: 't2', name: '李老师', previousSupervisionDuration: 0 },
    ])

    const highlight = useProctoringStatsHighlight({ teacherStats })

    highlight.handleTeacherStatsCellClick(
      teacherStats.value[0],
      { property: 'previousSupervisionDuration' }
    )

    expect(highlight.getTeacherStatsRowClassName({ row: teacherStats.value[0] })).toBe('teacher-stats-row-selected')
    expect(highlight.getTeacherStatsRowClassName({ row: teacherStats.value[1] })).toBe('teacher-stats-row-related')
    expect(
      highlight.getTeacherStatsCellClassName({
        row: teacherStats.value[0],
        column: { property: 'previousSupervisionDuration' },
      })
    ).toContain('teacher-stats-prev-duration-cell-clickable')
  })

  it('clears highlight when the selected row disappears from teacher stats', async () => {
    const teacherStats = ref([
      { id: 't1', name: '张老师', previousSupervisionDuration: 90 },
      { id: 't2', name: '李老师', previousSupervisionDuration: 90 },
    ])

    const highlight = useProctoringStatsHighlight({ teacherStats })

    highlight.handleTeacherStatsCellClick(
      teacherStats.value[0],
      { property: 'previousSupervisionDuration' }
    )

    teacherStats.value = [{ id: 't2', name: '李老师', previousSupervisionDuration: 90 }]
    await nextTick()

    expect(highlight.getTeacherStatsRowClassName({ row: teacherStats.value[0] })).toBe('')
    expect(highlight.getTeacherStatsDurationTextClass(teacherStats.value[0])).toBe('text-primary-600')
  })
})

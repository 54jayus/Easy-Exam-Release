import { ref, watch, type Ref } from 'vue'

export function useProctoringStatsHighlight(options: {
  teacherStats: Ref<any[]>
}) {
  const { teacherStats } = options

  const selectedStatsTeacherKey = ref('')
  const selectedStatsPreviousDuration = ref<number | null>(null)

  const normalizeStatsDuration = (value: unknown) => {
    const numeric = Number(value ?? 0)
    return Number.isFinite(numeric) ? numeric : 0
  }

  const getTeacherStatsRowKey = (row: any) => String(row?.id ?? row?.name ?? '')

  const isTeacherStatsDurationHighlightable = (row: any) => {
    const numeric = Number(row?.previousSupervisionDuration ?? 0)
    return Number.isFinite(numeric)
  }

  const clearTeacherStatsHighlight = () => {
    selectedStatsTeacherKey.value = ''
    selectedStatsPreviousDuration.value = null
  }

  const isTeacherStatsSelectedRow = (row: any) => {
    if (selectedStatsPreviousDuration.value === null) return false
    return (
      getTeacherStatsRowKey(row) === selectedStatsTeacherKey.value &&
      normalizeStatsDuration(row?.previousSupervisionDuration) === selectedStatsPreviousDuration.value
    )
  }

  const isTeacherStatsRelatedRow = (row: any) => {
    if (selectedStatsPreviousDuration.value === null) return false
    if (isTeacherStatsSelectedRow(row)) return false
    return normalizeStatsDuration(row?.previousSupervisionDuration) === selectedStatsPreviousDuration.value
  }

  const activateTeacherStatsHighlight = (row: any) => {
    if (!isTeacherStatsDurationHighlightable(row)) return

    const rowKey = getTeacherStatsRowKey(row)
    const previousDuration = normalizeStatsDuration(row?.previousSupervisionDuration)

    if (
      selectedStatsTeacherKey.value === rowKey &&
      selectedStatsPreviousDuration.value === previousDuration
    ) {
      clearTeacherStatsHighlight()
      return
    }

    selectedStatsTeacherKey.value = rowKey
    selectedStatsPreviousDuration.value = previousDuration
  }

  const handleTeacherStatsCellClick = (row: any, column: any) => {
    if (column?.property !== 'previousSupervisionDuration') return
    activateTeacherStatsHighlight(row)
  }

  const getTeacherStatsRowClassName = ({ row }: { row: any }) => {
    if (isTeacherStatsSelectedRow(row)) return 'teacher-stats-row-selected'
    if (isTeacherStatsRelatedRow(row)) return 'teacher-stats-row-related'
    return ''
  }

  const getTeacherStatsCellClassName = ({ row, column }: { row: any; column: any }) => {
    if (column?.property !== 'previousSupervisionDuration') return ''

    const classes = ['teacher-stats-prev-duration-cell']
    if (isTeacherStatsDurationHighlightable(row)) {
      classes.push('teacher-stats-prev-duration-cell-clickable')
    } else {
      classes.push('teacher-stats-prev-duration-cell-disabled')
    }
    if (isTeacherStatsSelectedRow(row)) {
      classes.push('teacher-stats-prev-duration-cell-selected')
    } else if (isTeacherStatsRelatedRow(row)) {
      classes.push('teacher-stats-prev-duration-cell-related')
    }

    return classes.join(' ')
  }

  const getTeacherStatsDurationTextClass = (row: any) => {
    if (!isTeacherStatsDurationHighlightable(row)) return 'text-slate-400'
    if (isTeacherStatsSelectedRow(row)) return 'font-semibold text-sky-700'
    if (isTeacherStatsRelatedRow(row)) return 'font-medium text-amber-700'
    return 'text-primary-600'
  }

  watch(teacherStats, (rows) => {
    if (selectedStatsPreviousDuration.value === null) return

    const stillExists = rows.some((row) => {
      return (
        getTeacherStatsRowKey(row) === selectedStatsTeacherKey.value &&
        normalizeStatsDuration(row?.previousSupervisionDuration) === selectedStatsPreviousDuration.value
      )
    })

    if (!stillExists) {
      clearTeacherStatsHighlight()
    }
  })

  return {
    clearTeacherStatsHighlight,
    handleTeacherStatsCellClick,
    getTeacherStatsRowClassName,
    getTeacherStatsCellClassName,
    getTeacherStatsDurationTextClass,
  }
}

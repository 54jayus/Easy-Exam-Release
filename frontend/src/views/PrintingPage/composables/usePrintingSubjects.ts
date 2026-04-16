import { computed, ref, watch, type ComputedRef, type Ref } from 'vue'
import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionError, formatActionSuccess } from '@/lib/uiFeedback'
import { GAOKAO_SUBJECT_ORDER } from '@/types/gaokao'

export type SubjectRow = {
  name: string
  time: string
}

type StorageLike = {
  getJsonPref<T>(key: string, defaultValue: T): T
  setJsonPref(key: string, value: unknown): void
}

type UsePrintingSubjectsOptions = {
  storage: StorageLike
  sourceType: Ref<string>
  isGaokaoMode: ComputedRef<boolean>
}

function ensureSubjectRowsLength(rows: SubjectRow[], count: number): SubjectRow[] {
  const safeCount = Math.min(20, Math.max(1, Math.floor(count || 0)))
  const next = rows.map((row) => ({
    name: String(row?.name ?? ''),
    time: String(row?.time ?? '')
  }))

  if (next.length > safeCount) return next.slice(0, safeCount)
  while (next.length < safeCount) next.push({ name: '', time: '' })
  return next
}

function formatMonthDay(examDate: string): string {
  const text = String(examDate || '').trim()
  const match = text.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
  if (!match) return ''

  const month = String(parseInt(match[2], 10))
  const day = String(parseInt(match[3], 10))
  return `${month}月${day}日`
}

function parseSubjectTime(raw: string): { dateText: string; range?: [string, string] } {
  const text = String(raw ?? '').trim()
  const match = text.match(/(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})/)
  if (!match) return { dateText: text }

  const start = match[1]
  const end = match[2]
  const index = match.index ?? 0
  const dateText = `${text.slice(0, index)}${text.slice(index + match[0].length)}`.trim()
  return { dateText, range: [start, end] }
}

function buildSubjectTime(dateText: string, range?: [string, string]): string {
  const date = String(dateText ?? '').trim()
  if (range && range[0] && range[1]) return `${date}${range[0]}-${range[1]}`.trim()
  return date
}

function mapRegularSubjectsToRows(list: any[]): SubjectRow[] {
  return list.slice(0, 20).map((subject) => {
    const name = String(subject?.name ?? '')
    const datePart = formatMonthDay(String(subject?.exam_date ?? ''))
    const timePart = String(subject?.exam_time ?? '')
    return { name, time: `${datePart}${timePart}`.trim() }
  })
}

function mapGaokaoSettingsToRows(settings: any): SubjectRow[] {
  const examTimes = settings?.examTimes ?? {}
  return GAOKAO_SUBJECT_ORDER.map((subjectKey) => {
    const config = examTimes?.[subjectKey]
    const datePart = formatMonthDay(String(config?.date ?? ''))
    const start = String(config?.startTime ?? '').trim()
    const end = String(config?.endTime ?? '').trim()
    const range = start && end ? `${start}-${end}` : ''
    return {
      name: String(config?.subjectName ?? subjectKey).trim() || subjectKey,
      time: `${datePart}${range}`.trim(),
    }
  })
}

export function usePrintingSubjects({ storage, sourceType, isGaokaoMode }: UsePrintingSubjectsOptions) {
  const feedback = createUiFeedback()
  const showSubjectDialog = ref(false)
  const syncingSubjects = ref(false)
  const subjectRows = ref<SubjectRow[]>([])
  const subjectDraftRows = ref<SubjectRow[]>([])
  const subjectDraftCount = ref(9)

  const subjectPreview = computed(() => {
    return subjectRows.value.map((row) => row.name).filter((value) => value.trim()).slice(0, 7)
  })

  const subjectPreviewWithTime = computed(() => {
    return subjectRows.value
      .filter((row) => row.name.trim() || row.time.trim())
      .slice(0, 7)
  })

  function loadStoredSubjectRows(): SubjectRow[] | null {
    const parsed = storage.getJsonPref<unknown>('subjectRows_v1', null)
    if (!Array.isArray(parsed)) return null
    return parsed.map((row: any) => ({
      name: String(row?.name ?? ''),
      time: String(row?.time ?? '')
    }))
  }

  function persistSubjectRows(rows: SubjectRow[]) {
    storage.setJsonPref('subjectRows_v1', rows)
  }

  function setAndPersistSubjectRows(rows: SubjectRow[], count?: number) {
    const nextCount = count ?? rows.length ?? 9
    const nextRows = ensureSubjectRowsLength(rows, nextCount)
    subjectRows.value = nextRows
    persistSubjectRows(nextRows)
  }

  async function syncSubjectRowsForCurrentSource() {
    if (sourceType.value !== 'schedule') return

    if (isGaokaoMode.value) {
      const response = await pythonBackend.request<any>('rooms.getGaokaoTimeSettings', {})
      const rows = mapGaokaoSettingsToRows(response?.settings)
      setAndPersistSubjectRows(rows, rows.length || 8)
      return
    }

    const response = await pythonBackend.request<any>('subjects.list', {})
    const rows = mapRegularSubjectsToRows((response?.subjects || []) as any[])
    setAndPersistSubjectRows(rows, rows.length || 9)
  }

  function initializeSubjectRows() {
    const stored = loadStoredSubjectRows()
    if (stored && stored.length) {
      subjectRows.value = ensureSubjectRowsLength(stored, stored.length)
      return
    }

    subjectRows.value = ensureSubjectRowsLength([], 9)
  }

  function resetSubjectRows(count = 9) {
    setAndPersistSubjectRows([], count)
  }

  function getRowDate(row: SubjectRow): string {
    return parseSubjectTime(row.time).dateText
  }

  function setRowDate(row: SubjectRow, dateText: string) {
    const parsed = parseSubjectTime(row.time)
    row.time = buildSubjectTime(dateText, parsed.range)
  }

  function getRowTimeRange(row: SubjectRow): [string, string] | undefined {
    return parseSubjectTime(row.time).range
  }

  function setRowTimeRange(row: SubjectRow, value: unknown) {
    const parsed = parseSubjectTime(row.time)
    if (Array.isArray(value) && value.length === 2 && value[0] && value[1]) {
      row.time = buildSubjectTime(parsed.dateText, [String(value[0]), String(value[1])])
      return
    }

    row.time = buildSubjectTime(parsed.dateText)
  }

  function openSubjectDialog() {
    subjectDraftCount.value = subjectRows.value.length || 9
    subjectDraftRows.value = ensureSubjectRowsLength(
      subjectRows.value.map((row) => ({ ...row })),
      subjectDraftCount.value
    )
    showSubjectDialog.value = true
  }

  watch(subjectDraftCount, (value) => {
    subjectDraftRows.value = ensureSubjectRowsLength(subjectDraftRows.value, value)
  })

  async function handleSyncSubjects() {
    syncingSubjects.value = true
    try {
      if (sourceType.value === 'schedule' && isGaokaoMode.value) {
        const response = await pythonBackend.request<any>('rooms.getGaokaoTimeSettings', {})
        const mapped = mapGaokaoSettingsToRows(response?.settings)
        subjectDraftCount.value = Math.min(20, Math.max(1, mapped.length || 8))
        subjectDraftRows.value = ensureSubjectRowsLength(mapped, subjectDraftCount.value)
        feedback.success(formatActionSuccess('同步高考高级设置'))
      } else {
        const response = await pythonBackend.request<any>('subjects.list', {})
        const mapped = mapRegularSubjectsToRows((response?.subjects || []) as any[])
        subjectDraftCount.value = Math.min(20, Math.max(1, mapped.length || 9))
        subjectDraftRows.value = ensureSubjectRowsLength(mapped, subjectDraftCount.value)
        feedback.success(formatActionSuccess('同步科目设置'))
      }
    } catch (error) {
      feedback.error(formatActionError('同步科目与时间', error))
    } finally {
      syncingSubjects.value = false
    }
  }

  function handleSaveSubjects() {
    const rows = ensureSubjectRowsLength(subjectDraftRows.value, subjectDraftCount.value)
    subjectRows.value = rows
    persistSubjectRows(rows)
    showSubjectDialog.value = false
  }

  return {
    subjectRows,
    subjectDraftRows,
    subjectDraftCount,
    showSubjectDialog,
    syncingSubjects,
    subjectPreview,
    subjectPreviewWithTime,
    initializeSubjectRows,
    resetSubjectRows,
    syncSubjectRowsForCurrentSource,
    openSubjectDialog,
    handleSyncSubjects,
    handleSaveSubjects,
    getRowDate,
    setRowDate,
    getRowTimeRange,
    setRowTimeRange
  }
}

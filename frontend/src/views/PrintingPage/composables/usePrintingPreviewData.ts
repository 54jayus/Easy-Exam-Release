import { computed, type ComputedRef, type Ref } from 'vue'

type SubjectRow = {
  name: string
  time: string
}

type PrintingConfig = {
  table: {
    groupMode: string
    includeSubjectFields: boolean
  }
  examBag: {
    schoolName: string
  }
}

type UsePrintingPreviewDataOptions = {
  activeTab: Ref<string>
  sourceType: Ref<string>
  previewMode: Ref<string>
  previewData: Ref<any[]>
  previewTotal: Ref<number>
  config: PrintingConfig
  subjectRows: Ref<SubjectRow[]>
}

type StudentInfoSortKey = [number, number | string]

const FIELD_ROOM = '\u8003\u573a'
const FIELD_ROOM_NO = '\u8003\u573a\u53f7'
const FIELD_SEAT_NO = '\u5ea7\u4f4d\u53f7'
const FIELD_SEAT = '\u5ea7\u4f4d'
const FIELD_NAME = '\u8003\u751f\u59d3\u540d'
const FIELD_NAME_FALLBACK = '\u59d3\u540d'
const FIELD_EXAM_NO = '\u8003\u751f\u8003\u53f7'
const FIELD_EXAM_NO_FALLBACK = '\u8003\u53f7'
const FIELD_CLASS = '\u73ed\u7ea7'
const FIELD_STUDENT_NO = '\u5b66\u53f7'
const FIELD_CLASS_STUDENT = '\u8003\u751f\u73ed\u7ea7\u5b66\u53f7'
const FIELD_FIRST = '\u9996\u9009'
const FIELD_TYPE = '\u7c7b\u522b'
const FIELD_SUB1 = '\u9009\u79d11'
const FIELD_SUB2 = '\u9009\u79d12'
const FIELD_SUB_ALT = '\u9009\u8003'
const FIELD_SUBJECT_DATA = '\u79d1\u76ee\u6570\u636e'
const FIELD_SUBJECT = '\u79d1\u76ee'
const FIELD_TIME = '\u65f6\u95f4'

function compareStudentInfoSortKey(a: StudentInfoSortKey, b: StudentInfoSortKey) {
  if (a[0] !== b[0]) return a[0] - b[0]
  const av = a[1]
  const bv = b[1]
  if (typeof av === 'number' && typeof bv === 'number') return av - bv
  return String(av).localeCompare(String(bv), 'zh-CN')
}

function studentInfoClassSortKey(value: any): StudentInfoSortKey {
  const text = String(value ?? '').trim()
  if (/^\d+$/.test(text)) return [0, Number(text)]
  return [1, text]
}

function studentInfoExamroomSortKey(value: any): StudentInfoSortKey {
  const text = String(value ?? '').trim()
  if (/^\d+$/.test(text)) return [0, Number(text)]
  if (text) return [1, text]
  return [2, '']
}

function studentInfoSeatSortKey(value: any): StudentInfoSortKey {
  const text = String(value ?? '').trim()
  if (/^\d+$/.test(text)) return [0, Number(text)]
  return [1, text]
}

function getCornerPreviewData(item: Record<string, any>) {
  const room = String(item[FIELD_ROOM] ?? '')
  const roomNo = String(item[FIELD_ROOM_NO] ?? '')
  const seatNo = String(item[FIELD_SEAT_NO] ?? '')

  let name = ''
  let examNo = ''
  let classStudent = ''

  if (item[FIELD_SUBJECT_DATA] && Array.isArray(item[FIELD_SUBJECT_DATA]) && item[FIELD_SUBJECT_DATA].length > 0) {
    const firstSubject = item[FIELD_SUBJECT_DATA][0]
    name = String(firstSubject[FIELD_NAME] ?? '')
    examNo = String(firstSubject[FIELD_EXAM_NO] ?? '')
    classStudent = String(firstSubject[FIELD_CLASS_STUDENT] ?? '')
  } else {
    name = String(item[FIELD_NAME] ?? item[FIELD_NAME_FALLBACK] ?? '')
    examNo = String(item[FIELD_EXAM_NO] ?? item[FIELD_EXAM_NO_FALLBACK] ?? '')
    classStudent = String(item[FIELD_CLASS_STUDENT] ?? '')

    if (!classStudent) {
      const className = String(item[FIELD_CLASS] ?? '')
      const studentNo = String(item[FIELD_STUDENT_NO] ?? '')
      if (className || studentNo) {
        classStudent = `${className}\u73ed${studentNo}\u53f7`
      }
    }
  }

  return {
    [FIELD_ROOM]: room,
    [FIELD_ROOM_NO]: roomNo,
    [FIELD_SEAT_NO]: seatNo,
    [FIELD_NAME]: name,
    [FIELD_EXAM_NO]: examNo,
    [FIELD_CLASS_STUDENT]: classStudent,
    [FIELD_SUBJECT_DATA]: item[FIELD_SUBJECT_DATA]
  }
}

function getTicketPreviewData(item: Record<string, any>) {
  const name = String(item[FIELD_NAME] ?? item[FIELD_NAME_FALLBACK] ?? '')
  const examNo = String(item[FIELD_EXAM_NO] ?? item[FIELD_EXAM_NO_FALLBACK] ?? '')
  const className = String(item[FIELD_CLASS] ?? '')
  const studentNo = String(item[FIELD_STUDENT_NO] ?? '')

  let room = ''
  let roomNo = ''
  let seatNo = ''

  if (item[FIELD_SUBJECT_DATA] && Array.isArray(item[FIELD_SUBJECT_DATA]) && item[FIELD_SUBJECT_DATA].length > 0) {
    const firstSubject = item[FIELD_SUBJECT_DATA][0]
    room = String(firstSubject[FIELD_ROOM] ?? '')
    roomNo = String(firstSubject[FIELD_ROOM_NO] ?? '')
    seatNo = String(firstSubject[FIELD_SEAT_NO] ?? '')
  } else {
    room = String(item[FIELD_ROOM] ?? '')
    roomNo = String(item[FIELD_ROOM_NO] ?? '')
    seatNo = String(item[FIELD_SEAT_NO] ?? '')
  }

  return {
    [FIELD_ROOM]: room,
    [FIELD_ROOM_NO]: roomNo,
    [FIELD_SEAT_NO]: seatNo,
    [FIELD_NAME]: name,
    [FIELD_EXAM_NO]: examNo,
    [FIELD_CLASS]: className,
    [FIELD_STUDENT_NO]: studentNo,
    [FIELD_SUBJECT_DATA]: item[FIELD_SUBJECT_DATA]
  }
}

export function usePrintingPreviewData({
  activeTab,
  sourceType,
  previewMode,
  previewData,
  previewTotal,
  config,
  subjectRows
}: UsePrintingPreviewDataOptions) {
  const hasPreviewData = computed(() => {
    if (sourceType.value === 'empty') return true
    return previewData.value.length > 0
  })

  const displayData = computed(() => {
    if (sourceType.value === 'empty') return []
    return previewData.value
  })

  const tablePreviewRows = computed(() => {
    const rows = displayData.value.slice(0, 20).map((item: any, idx: number) => {
      const name = String(item?.[FIELD_NAME] ?? item?.[FIELD_NAME_FALLBACK] ?? '\u5f20\u4e09')
      const examNo = String(item?.[FIELD_EXAM_NO] ?? item?.[FIELD_EXAM_NO_FALLBACK] ?? `1000${idx}`)
      const roomNo = String(item?.[FIELD_ROOM_NO] ?? '01')
      const seatNo = String(item?.[FIELD_SEAT_NO] ?? String(idx + 1).padStart(2, '0'))
      const classRaw = item?.[FIELD_CLASS]
      const classText = classRaw === undefined || classRaw === null ? '' : String(classRaw)
      const classDigits = classText.match(/\d+/)?.[0]
      const classLabel = classDigits ? `${classDigits}\u73ed` : (classText || '\u9ad8\u4e09(1)\u73ed')
      const studentNo = String(item?.[FIELD_STUDENT_NO] ?? (idx + 1))
      const subjects = `${String(item?.[FIELD_FIRST] ?? '\u7269\u7406')} ${String(item?.[FIELD_SUB1] ?? '\u5316\u5b66')} ${String(item?.[FIELD_SUB2] ?? '\u751f\u7269')}`
      return { name, examNo, roomNo, seatNo, classLabel, studentNo, subjects: subjects.trim() }
    })

    if (config.table.groupMode === 'examroom') {
      return rows.sort((a, b) => {
        const ra = parseInt(a.roomNo, 10)
        const rb = parseInt(b.roomNo, 10)
        if (!Number.isNaN(ra) && !Number.isNaN(rb) && ra !== rb) return ra - rb
        if (a.roomNo !== b.roomNo) return a.roomNo.localeCompare(b.roomNo, 'zh-CN')
        const sa = parseInt(a.seatNo, 10)
        const sb = parseInt(b.seatNo, 10)
        if (!Number.isNaN(sa) && !Number.isNaN(sb) && sa !== sb) return sa - sb
        return a.seatNo.localeCompare(b.seatNo, 'zh-CN')
      })
    }

    return rows.sort((a, b) => {
      if (a.classLabel !== b.classLabel) return a.classLabel.localeCompare(b.classLabel, 'zh-CN')
      const sa = parseInt(a.studentNo, 10)
      const sb = parseInt(b.studentNo, 10)
      if (!Number.isNaN(sa) && !Number.isNaN(sb) && sa !== sb) return sa - sb
      return a.studentNo.localeCompare(b.studentNo, 'zh-CN')
    })
  })

  const studentInfoColumns = computed(() => {
    const toPercent = (weight: number, total: number) => `${((weight / total) * 100).toFixed(4)}%`
    if (config.table.includeSubjectFields) {
      const weights = [5, 5, 7, 12, 5, 5, 5, 9, 6, 5]
      const total = weights.reduce((a, b) => a + b, 0)
      const widths = weights.map((weight) => toPercent(weight, total))
      return [
        { key: 'class', label: '\u73ed\u7ea7', width: widths[0] },
        { key: 'studentNo', label: '\u5b66\u53f7', width: widths[1] },
        { key: 'name', label: '\u59d3\u540d', width: widths[2] },
        { key: 'examNo', label: '\u8003\u53f7', width: widths[3] },
        { key: 'first', label: '\u9996\u9009', width: widths[4] },
        { key: 'sub1', label: '\u9009\u79d11', width: widths[5] },
        { key: 'sub2', label: '\u9009\u79d12', width: widths[6] },
        { key: 'room', label: '\u8003\u573a', width: widths[7] },
        { key: 'roomNo', label: '\u8003\u573a\u53f7', width: widths[8] },
        { key: 'seatNo', label: '\u5ea7\u4f4d', width: widths[9] }
      ] as const
    }

    const weights = [5, 5, 7, 12, 9, 6, 5]
    const total = weights.reduce((a, b) => a + b, 0)
    const widths = weights.map((weight) => toPercent(weight, total))
    return [
      { key: 'class', label: '\u73ed\u7ea7', width: widths[0] },
      { key: 'studentNo', label: '\u5b66\u53f7', width: widths[1] },
      { key: 'name', label: '\u59d3\u540d', width: widths[2] },
      { key: 'examNo', label: '\u8003\u53f7', width: widths[3] },
      { key: 'room', label: '\u8003\u573a', width: widths[4] },
      { key: 'roomNo', label: '\u8003\u573a\u53f7', width: widths[5] },
      { key: 'seatNo', label: '\u5ea7\u4f4d', width: widths[6] }
    ] as const
  })

  const studentInfoPrintLayout = computed(() => {
    const ptToMm = (pt: number) => `${(pt * 0.3527777778).toFixed(2)}mm`
    const contentHeightMm = 297 - 20
    const safetyGapPt = 24

    const isExamroom = config.table.groupMode === 'examroom'
    const titlePt = 22
    const headerPt = 20
    const summaryPt = isExamroom ? 16.5 : 16
    const bodyMinPt = isExamroom ? 16.5 : 11

    const titleMm = titlePt * 0.3527777778
    const headerMm = headerPt * 0.3527777778
    const summaryMm = summaryPt * 0.3527777778
    const bodyMinMm = bodyMinPt * 0.3527777778
    const safetyGapMm = safetyGapPt * 0.3527777778

    const maxRowsLast = Math.max(5, Math.floor((contentHeightMm - titleMm - headerMm - summaryMm - safetyGapMm) / bodyMinMm))
    const maxRowsMid = Math.max(5, Math.floor((contentHeightMm - titleMm - headerMm - safetyGapMm) / bodyMinMm))
    const fontSize = config.table.includeSubjectFields ? 8 : 9

    const bodyH =
      sourceType.value === 'empty'
        ? `${Math.max(1, (contentHeightMm - titleMm - headerMm - safetyGapMm) / (isExamroom ? 42 : 50)).toFixed(2)}mm`
        : ptToMm(bodyMinPt)

    return {
      titleH: ptToMm(titlePt),
      headerH: ptToMm(headerPt),
      bodyH,
      summaryH: ptToMm(summaryPt),
      maxRowsMid,
      maxRowsLast,
      fontSizePx: `${fontSize}px`,
      titleFontSizePx: '14px'
    }
  })

  const studentInfoFirstGroupRows = computed(() => {
    const data = displayData.value as any[]
    if (!Array.isArray(data) || !data.length) return []

    const isExamroom = config.table.groupMode === 'examroom'
    const keyOf = (item: any) => String((isExamroom ? item?.[FIELD_ROOM_NO] : item?.[FIELD_CLASS]) ?? '').trim()

    const groups = new Map<string, any[]>()
    for (const item of data) {
      const key = keyOf(item)
      if (!groups.has(key)) groups.set(key, [])
      groups.get(key)!.push(item)
    }

    const keys = Array.from(groups.keys())
    keys.sort((a, b) => {
      const ka = isExamroom ? studentInfoExamroomSortKey(a) : studentInfoClassSortKey(a)
      const kb = isExamroom ? studentInfoExamroomSortKey(b) : studentInfoClassSortKey(b)
      return compareStudentInfoSortKey(ka, kb)
    })

    const firstKey = keys[0] ?? ''
    const rows = (groups.get(firstKey) || []).slice()

    if (isExamroom) {
      rows.sort((a, b) => {
        const ka = studentInfoExamroomSortKey(a?.[FIELD_ROOM_NO])
        const kb = studentInfoExamroomSortKey(b?.[FIELD_ROOM_NO])
        const kcmp = compareStudentInfoSortKey(ka, kb)
        if (kcmp) return kcmp

        const sa = studentInfoSeatSortKey(a?.[FIELD_SEAT_NO] ?? a?.[FIELD_SEAT])
        const sb = studentInfoSeatSortKey(b?.[FIELD_SEAT_NO] ?? b?.[FIELD_SEAT])
        const scmp = compareStudentInfoSortKey(sa, sb)
        if (scmp) return scmp

        const ca = studentInfoClassSortKey(a?.[FIELD_CLASS])
        const cb = studentInfoClassSortKey(b?.[FIELD_CLASS])
        const ccmp = compareStudentInfoSortKey(ca, cb)
        if (ccmp) return ccmp

        const na = studentInfoSeatSortKey(a?.[FIELD_STUDENT_NO])
        const nb = studentInfoSeatSortKey(b?.[FIELD_STUDENT_NO])
        return compareStudentInfoSortKey(na, nb)
      })
    } else {
      rows.sort((a, b) => {
        const na = studentInfoSeatSortKey(a?.[FIELD_STUDENT_NO])
        const nb = studentInfoSeatSortKey(b?.[FIELD_STUDENT_NO])
        const ncmp = compareStudentInfoSortKey(na, nb)
        if (ncmp) return ncmp
        const ea = String(a?.[FIELD_EXAM_NO] ?? a?.[FIELD_EXAM_NO_FALLBACK] ?? '').trim()
        const eb = String(b?.[FIELD_EXAM_NO] ?? b?.[FIELD_EXAM_NO_FALLBACK] ?? '').trim()
        return ea.localeCompare(eb, 'zh-CN')
      })
    }

    return rows
  })

  const studentInfoFirstPageMeta = computed(() => {
    if (sourceType.value === 'empty') {
      const blankRows = config.table.groupMode === 'examroom' ? 42 : 50
      return { maxRows: blankRows, showSummary: false }
    }

    const total = studentInfoFirstGroupRows.value.length
    const { maxRowsMid, maxRowsLast } = studentInfoPrintLayout.value
    if (total <= maxRowsLast) return { maxRows: maxRowsLast, showSummary: true }
    return { maxRows: maxRowsMid, showSummary: false }
  })

  const studentInfoPrintBodyRows = computed(() => {
    const rows = studentInfoFirstGroupRows.value
    const maxRows = studentInfoFirstPageMeta.value.maxRows
    const normalized = rows.slice(0, maxRows).map((item: any) => {
      const classValue = String(item?.[FIELD_CLASS] ?? '').trim()
      const studentNo = String(item?.[FIELD_STUDENT_NO] ?? '').trim()
      const name = String(item?.[FIELD_NAME] ?? item?.[FIELD_NAME_FALLBACK] ?? '').trim()
      const examNo = String(item?.[FIELD_EXAM_NO] ?? item?.[FIELD_EXAM_NO_FALLBACK] ?? '').trim()
      const first = String(item?.[FIELD_FIRST] ?? item?.[FIELD_TYPE] ?? '').trim()
      const sub1 = String(item?.[FIELD_SUB1] ?? item?.[FIELD_SUB_ALT] ?? '').trim()
      const sub2 = String(item?.[FIELD_SUB2] ?? item?.[FIELD_SUB_ALT] ?? '').trim()
      const room = String(item?.[FIELD_ROOM] ?? '').trim()
      const roomNo = String(item?.[FIELD_ROOM_NO] ?? '').trim()
      const seatNo = String(item?.[FIELD_SEAT_NO] ?? item?.[FIELD_SEAT] ?? '').trim()

      if (config.table.includeSubjectFields) {
        return { class: classValue, studentNo, name, examNo, first, sub1, sub2, room, roomNo, seatNo }
      }

      return { class: classValue, studentNo, name, examNo, room, roomNo, seatNo }
    })

    if (sourceType.value === 'empty') {
      const blank = config.table.includeSubjectFields
        ? { class: '', studentNo: '', name: '', examNo: '', first: '', sub1: '', sub2: '', room: '', roomNo: '', seatNo: '' }
        : { class: '', studentNo: '', name: '', examNo: '', room: '', roomNo: '', seatNo: '' }

      while (normalized.length < maxRows) normalized.push({ ...blank })
    }

    return normalized
  })

  const studentInfoPrintSummaryRow = computed(() => {
    const colCount = studentInfoColumns.value.length
    const isExamroom = config.table.groupMode === 'examroom'
    const labelCol = isExamroom ? 'room' : 'class'

    const rawGroupKey = String(
      isExamroom ? (studentInfoFirstGroupRows.value?.[0]?.[FIELD_ROOM_NO] ?? '') : (studentInfoFirstGroupRows.value?.[0]?.[FIELD_CLASS] ?? '')
    ).trim()

    let label = ''
    if (isExamroom) {
      const roomName = String(studentInfoFirstGroupRows.value?.[0]?.[FIELD_ROOM] ?? '').trim()
      label = (roomName || rawGroupKey || FIELD_ROOM).trim()
    } else {
      label = rawGroupKey
    }

    const count = sourceType.value === 'empty' ? 0 : studentInfoFirstGroupRows.value.length

    const base: Record<string, string> = {}
    for (const col of studentInfoColumns.value) base[col.key] = ''
    base[labelCol] = `${label} \u8ba1\u6570`.trim()

    const keys = studentInfoColumns.value.map((col) => col.key)
    if (colCount >= 3) {
      base[keys[2]] = String(count)
    } else if (colCount >= 2) {
      base[keys[1]] = String(count)
    }

    return base
  })

  const examBagGroupedPages = computed(() => {
    const list = Array.isArray(previewData.value) ? previewData.value : []
    const bySubject = new Map<string, any[]>()
    const order: string[] = []

    for (const item of list) {
      const subject = String(item?.subject ?? '').trim()
      const key = subject || ''
      if (!bySubject.has(key)) {
        bySubject.set(key, [])
        order.push(key)
      }
      bySubject.get(key)!.push(item)
    }

    const capacity = 9
    const pages: Array<{ subject: string; items: any[] }> = []
    for (const subject of order) {
      const items = bySubject.get(subject) || []
      if (!items.length) {
        pages.push({ subject, items: [] })
        continue
      }
      for (let index = 0; index < items.length; index += capacity) {
        pages.push({ subject, items: items.slice(index, index + capacity) })
      }
    }

    return pages
  })

  const examBagPreviewList = computed(() => {
    if (sourceType.value === 'empty') {
      return Array(9).fill(null)
    }

    const firstPage = examBagGroupedPages.value[0]
    const items: any[] = (firstPage?.items || []).map((item: any) => ({
      subject: item.subject || '\u79d1\u76ee',
      room: item.room || '\u8003\u573a',
      count: item.count || 0
    }))

    while (items.length < 9) items.push(null)
    return items
  })

  const examBagPrintCells = computed(() => {
    const school = String(config.examBag.schoolName ?? '').trim()
    return examBagPreviewList.value.map((item: any) => {
      if (!item) {
        if (sourceType.value !== 'empty') return ''
        const safeSchool = school || 'xxx\u5b66\u6821'
        return `\u5b66\u6821\uff1a${safeSchool}\n\n\u79d1\u76ee\uff1a\n\n\u8003\u573a\uff1a\n\n\u5e94\u5230\uff1a\n\n\u5b9e\u5230\uff1a\n\n\u76d1\u8003\u6559\u5e08\uff1a\n\n\u8003\u8bd5\u60c5\u51b5\uff1a`
      }

      const subject = String(item?.subject ?? '').trim()
      const room = String(item?.room ?? '').trim()
      const count = String(item?.count ?? '').trim()
      const safeSchool = school || 'xxx\u5b66\u6821'
      return `\u5b66\u6821\uff1a${safeSchool}\n\n\u79d1\u76ee\uff1a${subject}\n\n\u8003\u573a\uff1a${room}\uff08${count}\u4eba\uff09\n\n\u5e94\u5230\uff1a\n\n\u5b9e\u5230\uff1a\n\n\u76d1\u8003\u6559\u5e08\uff1a\n\n\u8003\u8bd5\u60c5\u51b5\uff1a`
    })
  })

  const examBagPreviewFooterText = computed(() => {
    const pageNum = 1
    if (sourceType.value === 'empty') return `\u7b2c ${pageNum} \u9875\uff0c\u5171 1 \u9875`
    if (!examBagGroupedPages.value.length) return ''

    const totalPages = Math.max(1, examBagGroupedPages.value.length)
    const subject = String(examBagGroupedPages.value[0]?.subject ?? '').trim()
    const base = `\u7b2c ${pageNum} \u9875\uff0c\u5171 ${totalPages} \u9875`
    return subject ? `${base}\uff0c\u5f53\u524d\u79d1\u76ee\uff1a${subject}` : base
  })

  const getCornerStudentName = (item: any, subjectIndex: number): string => {
    if (!item) return ''
    if (item[FIELD_SUBJECT_DATA] && Array.isArray(item[FIELD_SUBJECT_DATA])) {
      return item[FIELD_SUBJECT_DATA][subjectIndex]?.[FIELD_NAME] || ''
    }
    return item[FIELD_NAME] || ''
  }

  const getCornerStudentExamNo = (item: any, subjectIndex: number): string => {
    if (!item) return ''
    if (item[FIELD_SUBJECT_DATA] && Array.isArray(item[FIELD_SUBJECT_DATA])) {
      return item[FIELD_SUBJECT_DATA][subjectIndex]?.[FIELD_EXAM_NO] || ''
    }
    return item[FIELD_EXAM_NO] || ''
  }

  const getCornerStudentClassNo = (item: any, subjectIndex: number): string => {
    if (!item) return ''
    if (item[FIELD_SUBJECT_DATA] && Array.isArray(item[FIELD_SUBJECT_DATA])) {
      return item[FIELD_SUBJECT_DATA][subjectIndex]?.[FIELD_CLASS_STUDENT] || ''
    }
    return item[FIELD_CLASS_STUDENT] || ''
  }

  const getTicketRoom = (item: any, subjectIndex: number): string => {
    if (!item) return ''
    if (item[FIELD_SUBJECT_DATA] && Array.isArray(item[FIELD_SUBJECT_DATA])) {
      return item[FIELD_SUBJECT_DATA][subjectIndex]?.[FIELD_ROOM] || ''
    }
    return item[FIELD_ROOM] || ''
  }

  const getTicketRoomNo = (item: any, subjectIndex: number): string => {
    if (!item) return ''
    if (item[FIELD_SUBJECT_DATA] && Array.isArray(item[FIELD_SUBJECT_DATA])) {
      return item[FIELD_SUBJECT_DATA][subjectIndex]?.[FIELD_ROOM_NO] || ''
    }
    return item[FIELD_ROOM_NO] || ''
  }

  const getTicketSeatNo = (item: any, subjectIndex: number): string => {
    if (!item) return ''
    if (item[FIELD_SUBJECT_DATA] && Array.isArray(item[FIELD_SUBJECT_DATA])) {
      return item[FIELD_SUBJECT_DATA][subjectIndex]?.[FIELD_SEAT_NO] || ''
    }
    return item[FIELD_SEAT_NO] || ''
  }

  const cornerPreview = computed(() => {
    const fallback = {
      [FIELD_ROOM]: '',
      [FIELD_ROOM_NO]: '',
      [FIELD_SEAT_NO]: '',
      [FIELD_NAME]: '',
      [FIELD_EXAM_NO]: '',
      [FIELD_CLASS_STUDENT]: ''
    }
    if (sourceType.value === 'empty') return fallback
    const first = displayData.value[0]
    if (!first) return fallback
    return getCornerPreviewData(first)
  })

  const cornerSubjectRowsForStyle = computed(() => {
    if (sourceType.value === 'empty') {
      const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
      return Array.from({ length: count }, () => '')
    }

    const first = displayData.value[0]
    if (first && first[FIELD_SUBJECT_DATA] && Array.isArray(first[FIELD_SUBJECT_DATA])) {
      return first[FIELD_SUBJECT_DATA].map((subject: any) => String(subject[FIELD_SUBJECT] ?? '').trim())
    }

    const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
    return Array.from({ length: count }, (_, index) => String(subjectRows.value[index]?.name ?? '').trim())
  })

  const cornerSubjectRows = computed(() => {
    if (sourceType.value === 'empty') {
      const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
      return Array.from({ length: count }, () => '')
    }

    const first = displayData.value[0]
    if (first && first[FIELD_SUBJECT_DATA] && Array.isArray(first[FIELD_SUBJECT_DATA])) {
      return first[FIELD_SUBJECT_DATA].map((subject: any) => String(subject[FIELD_SUBJECT] ?? '').trim())
    }

    const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
    return Array.from({ length: count }, (_, index) => String(subjectRows.value[index]?.name ?? '').trim())
  })

  const cornerTemplatesPerCol = computed(() => {
    const subjectCount = cornerSubjectRows.value.length
    if (subjectCount <= 3) return 5
    if (subjectCount <= 5) return 4
    if (subjectCount <= 9) return 3
    return 2
  })

  const itemsPerPage = computed(() => {
    if (activeTab.value === 'corner') {
      return cornerTemplatesPerCol.value * 3
    }
    if (activeTab.value === 'ticket') {
      const subjectCount = subjectRows.value.length
      if (subjectCount <= 3) return 15
      if (subjectCount <= 5) return 12
      if (subjectCount <= 9) return 9
      return 6
    }
    return 10
  })

  const previewTotalPages = computed(() => {
    if (activeTab.value !== 'corner' && activeTab.value !== 'ticket') return 0
    if (sourceType.value === 'empty') return 0
    const total = previewTotal.value > 0 ? previewTotal.value : previewData.value.length
    if (!total) return 0
    return Math.max(1, Math.ceil(total / itemsPerPage.value))
  })

  const printPreviewList = computed(() => {
    if (sourceType.value === 'empty') {
      if (activeTab.value === 'corner') {
        const blank = {
          [FIELD_ROOM]: '',
          [FIELD_ROOM_NO]: '',
          [FIELD_SEAT_NO]: '',
          [FIELD_NAME]: '',
          [FIELD_EXAM_NO]: '',
          [FIELD_CLASS_STUDENT]: ''
        }
        return Array.from({ length: itemsPerPage.value }, () => ({ ...blank }))
      }
      if (activeTab.value === 'ticket') {
        const blank = {
          [FIELD_ROOM]: '',
          [FIELD_ROOM_NO]: '',
          [FIELD_SEAT_NO]: '',
          [FIELD_NAME]: '',
          [FIELD_EXAM_NO]: '',
          [FIELD_CLASS]: '',
          [FIELD_STUDENT_NO]: ''
        }
        return Array.from({ length: itemsPerPage.value }, () => ({ ...blank }))
      }
    }

    const list = displayData.value.slice(0, itemsPerPage.value)
    if (activeTab.value === 'corner') {
      return list.map((item) => getCornerPreviewData(item))
    }
    if (activeTab.value === 'ticket') {
      return list.map((item) => getTicketPreviewData(item))
    }
    return []
  })

  const ticketPreview = computed(() => {
    const fallback = {
      [FIELD_ROOM]: '',
      [FIELD_ROOM_NO]: '',
      [FIELD_SEAT_NO]: '',
      [FIELD_NAME]: '',
      [FIELD_EXAM_NO]: '',
      [FIELD_CLASS]: '',
      [FIELD_STUDENT_NO]: ''
    }
    if (sourceType.value === 'empty') return fallback
    const first = displayData.value[0]
    if (!first) return fallback
    return getTicketPreviewData(first)
  })

  const ticketSubjectRows = computed(() => {
    if (sourceType.value === 'empty') {
      const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
      return Array.from({ length: count }, () => ({ name: '', time: '' }))
    }

    const first = displayData.value[0]
    if (first && first[FIELD_SUBJECT_DATA] && Array.isArray(first[FIELD_SUBJECT_DATA])) {
      return first[FIELD_SUBJECT_DATA].map((subject: any) => ({
        name: String(subject[FIELD_SUBJECT] ?? '').trim(),
        time: String(subject[FIELD_TIME] ?? '').trim()
      }))
    }

    const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
    return Array.from({ length: count }, (_, index) => ({
      name: String(subjectRows.value[index]?.name ?? '').trim(),
      time: String(subjectRows.value[index]?.time ?? '').trim()
    }))
  })

  const ticketSubjectRowsForPrint = computed(() => {
    if (previewMode.value === 'print' && sourceType.value === 'empty') {
      const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
      return Array.from({ length: count }, () => ({ name: '', time: '' }))
    }
    return ticketSubjectRows.value
  })

  const previewBadgeText = computed(() => {
    if (activeTab.value !== 'corner' && activeTab.value !== 'ticket') return ''
    if (previewMode.value === 'style') {
      if (sourceType.value === 'empty') return '\u9884\u89c8\uff1a\u6837\u5f0f\u53c2\u8003'
      if (previewTotal.value > 0) return `\u9884\u89c8\uff1a\u7b2c 1 \u6761\u8003\u751f / \u5171 ${previewTotal.value} \u6761`
      if (previewData.value.length > 0) return '\u9884\u89c8\uff1a\u7b2c 1 \u6761\u8003\u751f'
      return '\u9884\u89c8\uff1a\u672a\u52a0\u8f7d\u6570\u636e'
    }
    if (previewMode.value === 'print') {
      if (sourceType.value === 'empty') return ''
      const pages = previewTotalPages.value
      if (pages > 0) return `\u9884\u89c8\uff1a\u7b2c 1 \u9875 / \u5171 ${pages} \u9875`
      return '\u9884\u89c8\uff1a\u672a\u52a0\u8f7d\u6570\u636e'
    }
    return ''
  })

  const previewPrintFooterText = computed(() => {
    if (previewMode.value !== 'print') return ''
    if (activeTab.value !== 'corner' && activeTab.value !== 'ticket') return ''
    const pageNum = 1
    const totalPages = sourceType.value === 'empty' ? 1 : (previewTotalPages.value || 1)
    const first = printPreviewList.value?.[0] as any
    const base = `\u7b2c ${pageNum} \u9875\uff0c\u5171 ${totalPages} \u9875`
    if (activeTab.value === 'corner') {
      const room = String(first?.[FIELD_ROOM] ?? '').trim()
      return room ? `${base}\uff0c\u5f53\u524d\u8003\u573a\uff1a${room}` : base
    }
    const raw = String(first?.[FIELD_CLASS] ?? '').trim()
    const classText = raw && /^\d+$/.test(raw) ? `${raw}\u73ed` : raw
    return classText ? `${base}\uff0c\u5f53\u524d\u73ed\u7ea7\uff1a${classText}` : base
  })

  return {
    hasPreviewData,
    displayData,
    tablePreviewRows,
    studentInfoColumns,
    studentInfoPrintLayout,
    studentInfoFirstGroupRows,
    studentInfoFirstPageMeta,
    studentInfoPrintBodyRows,
    studentInfoPrintSummaryRow,
    examBagGroupedPages,
    examBagPreviewList,
    examBagPrintCells,
    examBagPreviewFooterText,
    getCornerStudentName,
    getCornerStudentExamNo,
    getCornerStudentClassNo,
    getTicketRoom,
    getTicketRoomNo,
    getTicketSeatNo,
    cornerPreview,
    cornerSubjectRowsForStyle,
    cornerSubjectRows,
    cornerTemplatesPerCol,
    itemsPerPage,
    previewTotalPages,
    printPreviewList,
    ticketPreview,
    ticketSubjectRows,
    ticketSubjectRowsForPrint,
    previewBadgeText,
    previewPrintFooterText
  }
}

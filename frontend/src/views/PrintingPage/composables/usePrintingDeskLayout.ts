import { computed, nextTick, reactive, ref, watch, type ComputedRef } from 'vue'
import { createUiFeedback, formatActionWarning } from '@/lib/uiFeedback'

type DeskConfig = {
  layoutName: string
  layoutRows: number
  layoutCols: number
  layoutPattern: string
  startPos: string
  customColCounts: number[] | null
}

type PrintingConfig = {
  desk: DeskConfig
}

type DeskEffectiveLayout = {
  layoutName: string
  rows: number
  cols: number
  capacity: number
  customColCounts: number[] | null
}

type UsePrintingDeskLayoutOptions = {
  config: PrintingConfig
  displayData: ComputedRef<any[]>
  hasPreviewData: ComputedRef<boolean>
  sourceType: ComputedRef<string> | { value: string }
  onAfterApply: () => Promise<void> | void
}

const FIELD_ROOM = '\u8003\u573a'
const FIELD_ROOM_NO = '\u8003\u573a\u53f7'
const FIELD_NAME = '\u8003\u751f\u59d3\u540d'
const FIELD_NAME_FALLBACK = '\u59d3\u540d'
const FIELD_EXAM_NO = '\u8003\u751f\u8003\u53f7'
const FIELD_EXAM_NO_FALLBACK = '\u8003\u53f7'
const FIELD_SEAT_NO = '\u5ea7\u4f4d\u53f7'
const CUSTOM_LAYOUT_NAME = '\u81ea\u5b9a\u4e49'
const DEFAULT_LAYOUT_NAME = '7\u884c\u00d76\u5217'
const DEFAULT_LAYOUT_PATTERN = 'S\u578b\u7ad6\u6392'
const LAYOUT_OPTIONS = [
  { name: '5\u884c\u00d76\u5217', rows: 5, cols: 6 },
  { name: '6\u884c\u00d75\u5217', rows: 6, cols: 5 },
  { name: '6\u884c\u00d77\u5217', rows: 6, cols: 7 },
  { name: DEFAULT_LAYOUT_NAME, rows: 7, cols: 6 },
  { name: '5\u884c\u00d79\u5217', rows: 5, cols: 9 },
  { name: '9\u884c\u00d75\u5217', rows: 9, cols: 5 }
] as const

function parseCustomCounts(text: string): number[] | null {
  const raw = String(text || '').trim().replace(/\uff0c/g, ',')
  if (!raw) return null
  const parts = raw.split(',').map((item) => item.trim()).filter(Boolean)
  const nums = parts.map((item) => parseInt(item, 10)).filter((item) => Number.isFinite(item) && item > 0)
  if (!nums.length) return null
  return nums
}

function getSeatMapping(
  rows: number,
  cols: number,
  pattern: string,
  startPos: 'left' | 'right',
  customColCounts: number[] | null
): Record<number, [number, number]> {
  const mapping: Record<number, [number, number]> = {}
  let currentSeat = 0

  const safeRows = Math.max(1, Math.floor(rows || 0))
  const safeCols = Math.max(1, Math.floor(cols || 0))
  const custom = Array.isArray(customColCounts) && customColCounts.length ? customColCounts : null

  const isValidPos = (row: number, actualCol: number) => {
    if (!custom) return true
    if (actualCol < 0 || actualCol >= custom.length) return false
    return row < custom[actualCol]
  }

  const getActualCol = (logicCol: number) => {
    if (startPos === 'left') return safeCols - 1 - logicCol
    return logicCol
  }

  if (pattern === 'Z\u578b\u6a2a\u6392') {
    for (let row = 0; row < safeRows; row++) {
      for (let col = 0; col < safeCols; col++) {
        const actualCol = getActualCol(col)
        if (isValidPos(row, actualCol)) mapping[currentSeat++] = [row, actualCol]
      }
    }
  } else if (pattern === 'S\u578b\u6a2a\u6392') {
    for (let row = 0; row < safeRows; row++) {
      const even = row % 2 === 0
      if (even) {
        for (let col = 0; col < safeCols; col++) {
          const actualCol = getActualCol(col)
          if (isValidPos(row, actualCol)) mapping[currentSeat++] = [row, actualCol]
        }
      } else {
        for (let col = safeCols - 1; col >= 0; col--) {
          const actualCol = getActualCol(col)
          if (isValidPos(row, actualCol)) mapping[currentSeat++] = [row, actualCol]
        }
      }
    }
  } else if (pattern === 'Z\u578b\u7ad6\u6392') {
    for (let col = 0; col < safeCols; col++) {
      const actualCol = getActualCol(col)
      for (let row = 0; row < safeRows; row++) {
        if (isValidPos(row, actualCol)) mapping[currentSeat++] = [row, actualCol]
      }
    }
  } else if (pattern === 'S\u578b\u7ad6\u6392') {
    for (let col = 0; col < safeCols; col++) {
      const even = col % 2 === 0
      const actualCol = getActualCol(col)
      if (even) {
        for (let row = 0; row < safeRows; row++) {
          if (isValidPos(row, actualCol)) mapping[currentSeat++] = [row, actualCol]
        }
      } else {
        for (let row = safeRows - 1; row >= 0; row--) {
          if (isValidPos(row, actualCol)) mapping[currentSeat++] = [row, actualCol]
        }
      }
    }
  }

  return mapping
}

export function usePrintingDeskLayout({
  config,
  displayData,
  hasPreviewData,
  sourceType,
  onAfterApply
}: UsePrintingDeskLayoutOptions) {
  const feedback = createUiFeedback()
  const deskLayoutOptions = LAYOUT_OPTIONS

  const firstRoomData = computed(() => {
    const list = displayData.value || []
    if (!Array.isArray(list) || list.length === 0) return []
    const first = list[0] || {}
    const key = first?.[FIELD_ROOM_NO] ?? first?.[FIELD_ROOM]
    if (key === undefined || key === null) return list
    return list.filter((item: any) => {
      const current = item?.[FIELD_ROOM_NO] ?? item?.[FIELD_ROOM]
      return String(current ?? '') === String(key)
    })
  })

  const deskEffectiveLayout = computed<DeskEffectiveLayout>(() => {
    const custom = config.desk.customColCounts
    if (Array.isArray(custom) && custom.length) {
      const cols = custom.length
      const rows = Math.max(...custom.map((value) => Math.max(0, value)))
      const capacity = custom.reduce((acc, value) => acc + Math.max(0, value || 0), 0)
      return {
        layoutName: CUSTOM_LAYOUT_NAME,
        rows: Math.max(1, rows),
        cols: Math.max(1, cols),
        capacity: Math.max(1, capacity),
        customColCounts: custom
      }
    }

    const rows = Math.max(1, Math.floor(config.desk.layoutRows || 0))
    const cols = Math.max(1, Math.floor(config.desk.layoutCols || 0))
    return {
      layoutName: config.desk.layoutName || `${rows}\u884c\u00d7${cols}\u5217`,
      rows,
      cols,
      capacity: rows * cols,
      customColCounts: null
    }
  })

  const buildDeskGrid = <T>(factory: () => T) => {
    const { rows, cols, customColCounts } = deskEffectiveLayout.value
    const grid = Array.from({ length: rows }, () => Array.from({ length: cols }, factory))
    const custom = customColCounts
    if (custom) {
      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          ;(grid[row][col] as any).valid = row < (custom[col] || 0)
        }
      }
    }
    return grid
  }

  const deskSeatGrid = computed(() => {
    const { rows, cols, capacity, customColCounts } = deskEffectiveLayout.value
    const grid = buildDeskGrid(() => ({ valid: true, student: null as any | null }))
    if (!hasPreviewData.value) return grid

    const mapping = getSeatMapping(rows, cols, config.desk.layoutPattern, config.desk.startPos === 'right' ? 'right' : 'left', customColCounts)
    const students = firstRoomData.value.slice(0, capacity)
    for (let index = 0; index < students.length; index++) {
      const pos = mapping[index]
      if (!pos) continue
      const [row, col] = pos
      if (row >= 0 && row < rows && col >= 0 && col < cols && grid[row][col].valid) {
        grid[row][col].student = students[index]
      }
    }
    return grid
  })

  const deskSeatNumberGrid = computed(() => {
    const { rows, cols, customColCounts } = deskEffectiveLayout.value
    const grid = buildDeskGrid(() => ({ valid: true, seatNo: null as number | null }))
    const mapping = getSeatMapping(rows, cols, config.desk.layoutPattern, config.desk.startPos === 'right' ? 'right' : 'left', customColCounts)
    const capacity = Object.keys(mapping).length
    for (let index = 0; index < capacity; index++) {
      const pos = mapping[index]
      if (!pos) continue
      const [row, col] = pos
      if (row >= 0 && row < rows && col >= 0 && col < cols && grid[row][col].valid) {
        grid[row][col].seatNo = index + 1
      }
    }
    return grid
  })

  const deskPrintGrid = computed(() => {
    const { rows, cols, capacity, customColCounts } = deskEffectiveLayout.value
    const grid = buildDeskGrid(() => ({ valid: true, student: null as any | null }))
    if (!hasPreviewData.value || sourceType.value === 'empty') return grid

    const mapping = getSeatMapping(rows, cols, config.desk.layoutPattern, config.desk.startPos === 'right' ? 'right' : 'left', customColCounts)
    const students = firstRoomData.value.slice(0, capacity)
    for (let index = 0; index < students.length; index++) {
      const pos = mapping[index]
      if (!pos) continue
      const [row, col] = pos
      if (row >= 0 && row < rows && col >= 0 && col < cols && grid[row][col].valid) {
        grid[row][col].student = students[index]
      }
    }
    return grid
  })

  function deskPrintCellText(row: number, col: number) {
    const cell = deskPrintGrid.value?.[row]?.[col]
    if (!cell || !cell.valid) return ''
    const student = cell.student || {}
    const name = String(student?.[FIELD_NAME] ?? student?.[FIELD_NAME_FALLBACK] ?? '')
    const examNo = String(student?.[FIELD_EXAM_NO] ?? student?.[FIELD_EXAM_NO_FALLBACK] ?? '')
    const room = String(student?.[FIELD_ROOM] ?? '')
    const roomNo = String(student?.[FIELD_ROOM_NO] ?? '')
    const seatNo = String(student?.[FIELD_SEAT_NO] ?? '')
    return `\u59d3\u540d\uff1a${name}\n\u8003\u53f7\uff1a${examNo}\n\u8003\u573a\uff1a${room}\n\u8003\u573a\u53f7\uff1a${roomNo}\n\u5ea7\u4f4d\u53f7\uff1a${seatNo}`
  }

  const deskLayoutSummary = computed(() => {
    const layoutName = String(config.desk.layoutName || deskEffectiveLayout.value.layoutName)
    const { rows, cols } = deskEffectiveLayout.value
    const pattern = String(config.desk.layoutPattern || '')
    const startPos = config.desk.startPos === 'right' ? '\u53f3\u624b\u4f4d' : '\u5de6\u624b\u4f4d'
    const layoutText = layoutName === CUSTOM_LAYOUT_NAME ? `${rows}\u884c\u00d7${cols}\u5217` : layoutName
    return `${layoutText} | ${pattern} | ${startPos}`
  })

  const showDeskLayoutDialog = ref(false)
  const deskLayoutDraft = reactive({
    layoutName: DEFAULT_LAYOUT_NAME,
    layoutRows: 7,
    layoutCols: 6,
    layoutPattern: DEFAULT_LAYOUT_PATTERN,
    startPos: 'left' as 'left' | 'right',
    customCountsText: ''
  })

  function openDeskLayoutDialog() {
    deskLayoutDraft.layoutName = String(config.desk.layoutName || DEFAULT_LAYOUT_NAME)
    deskLayoutDraft.layoutRows = Number(config.desk.layoutRows || 7)
    deskLayoutDraft.layoutCols = Number(config.desk.layoutCols || 6)
    deskLayoutDraft.layoutPattern = String(config.desk.layoutPattern || DEFAULT_LAYOUT_PATTERN)
    deskLayoutDraft.startPos = config.desk.startPos === 'right' ? 'right' : 'left'
    if (Array.isArray(config.desk.customColCounts) && config.desk.customColCounts.length) {
      deskLayoutDraft.layoutName = CUSTOM_LAYOUT_NAME
      deskLayoutDraft.customCountsText = config.desk.customColCounts.join(',')
      deskLayoutDraft.layoutRows = deskEffectiveLayout.value.rows
      deskLayoutDraft.layoutCols = deskEffectiveLayout.value.cols
    } else {
      deskLayoutDraft.customCountsText = ''
    }
    showDeskLayoutDialog.value = true
  }

  watch(
    () => deskLayoutDraft.layoutName,
    (name) => {
      if (name === CUSTOM_LAYOUT_NAME) return
      const option = deskLayoutOptions.find((item) => item.name === name)
      if (!option) return
      deskLayoutDraft.layoutRows = option.rows
      deskLayoutDraft.layoutCols = option.cols
      deskLayoutDraft.customCountsText = ''
    }
  )

  watch(
    () => deskLayoutDraft.customCountsText,
    (text) => {
      if (deskLayoutDraft.layoutName !== CUSTOM_LAYOUT_NAME) return
      const nums = parseCustomCounts(text)
      if (!nums) return
      deskLayoutDraft.layoutCols = nums.length
      deskLayoutDraft.layoutRows = Math.max(1, Math.max(...nums))
    }
  )

  async function applyDeskLayoutDraft() {
    if (deskLayoutDraft.layoutName === CUSTOM_LAYOUT_NAME) {
      const nums = parseCustomCounts(deskLayoutDraft.customCountsText)
      if (!nums) {
        feedback.warning(formatActionWarning('应用座位布局', '请输入有效的自定义每列人数'))
        return
      }
      config.desk.layoutName = CUSTOM_LAYOUT_NAME
      config.desk.customColCounts = nums
      config.desk.layoutCols = nums.length
      config.desk.layoutRows = Math.max(1, Math.max(...nums))
    } else {
      const option = deskLayoutOptions.find((item) => item.name === deskLayoutDraft.layoutName)
      if (option) {
        config.desk.layoutName = option.name
        config.desk.layoutRows = option.rows
        config.desk.layoutCols = option.cols
      } else {
        config.desk.layoutName = String(deskLayoutDraft.layoutName || '')
      }
      config.desk.customColCounts = null
    }

    config.desk.layoutPattern = deskLayoutDraft.layoutPattern
    config.desk.startPos = deskLayoutDraft.startPos
    showDeskLayoutDialog.value = false

    await nextTick()
    await onAfterApply()
  }

  return {
    deskLayoutOptions,
    deskEffectiveLayout,
    deskSeatGrid,
    deskSeatNumberGrid,
    deskPrintCellText,
    deskLayoutSummary,
    showDeskLayoutDialog,
    deskLayoutDraft,
    openDeskLayoutDialog,
    applyDeskLayoutDraft
  }
}

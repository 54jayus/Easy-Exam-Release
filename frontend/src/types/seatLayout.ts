export type SeatLayout = {
  layoutName: string
  layoutRows: number
  layoutCols: number
  layoutPattern: string
  startPos: 'left' | 'right'
  customColCounts: number[] | null
}

export type SeatLayoutConfig = {
  defaultLayout: SeatLayout
  roomOverrides: Record<string, SeatLayout>
}

export const DEFAULT_SEAT_LAYOUT: SeatLayout = {
  layoutName: '7行×6列',
  layoutRows: 7,
  layoutCols: 6,
  layoutPattern: 'S型竖排',
  startPos: 'left',
  customColCounts: null,
}

export const SEAT_LAYOUT_OPTIONS = [
  { name: '5行×6列', rows: 5, cols: 6 },
  { name: '6行×5列', rows: 6, cols: 5 },
  { name: '6行×7列', rows: 6, cols: 7 },
  { name: '7行×6列', rows: 7, cols: 6 },
  { name: '5行×9列', rows: 5, cols: 9 },
  { name: '9行×5列', rows: 9, cols: 5 },
] as const

export function normalizeSeatLayout(value?: Partial<SeatLayout> | null): SeatLayout {
  const result = { ...DEFAULT_SEAT_LAYOUT, ...(value || {}) }
  const custom = Array.isArray(result.customColCounts)
    ? result.customColCounts.map((item) => Math.max(0, Math.floor(Number(item) || 0))).filter((_, index, array) => index < array.length)
    : null
  if (custom?.some(Boolean)) {
    result.layoutName = '自定义'
    result.layoutCols = custom.length
    result.layoutRows = Math.max(...custom)
    result.customColCounts = custom
  } else {
    result.layoutRows = Math.max(1, Math.floor(Number(result.layoutRows) || 7))
    result.layoutCols = Math.max(1, Math.floor(Number(result.layoutCols) || 6))
    result.customColCounts = null
  }
  result.startPos = result.startPos === 'right' ? 'right' : 'left'
  return result
}

export function normalizeSeatLayoutConfig(value?: Partial<SeatLayoutConfig> | null): SeatLayoutConfig {
  const overrides: Record<string, SeatLayout> = {}
  for (const [roomNo, layout] of Object.entries(value?.roomOverrides || {})) {
    overrides[String(roomNo)] = normalizeSeatLayout(layout)
  }
  return { defaultLayout: normalizeSeatLayout(value?.defaultLayout), roomOverrides: overrides }
}

export function parseCustomColCounts(text: string): number[] | null {
  const values = String(text || '').trim().replace(/，/g, ',').split(',')
    .map((item) => Math.floor(Number(item.trim())))
    .filter((item) => Number.isFinite(item) && item > 0)
  return values.length ? values : null
}

export function getSeatMapping(layoutValue: Partial<SeatLayout>): Record<number, [number, number]> {
  const layout = normalizeSeatLayout(layoutValue)
  const mapping: Record<number, [number, number]> = {}
  let seat = 1
  const valid = (row: number, col: number) => !layout.customColCounts || row < (layout.customColCounts[col] || 0)
  const actualCol = (logicalCol: number) => layout.startPos === 'left' ? layout.layoutCols - 1 - logicalCol : logicalCol
  const add = (row: number, logicalCol: number) => {
    const col = actualCol(logicalCol)
    if (valid(row, col)) mapping[seat++] = [row, col]
  }
  if (layout.layoutPattern === 'Z型横排') {
    for (let row = 0; row < layout.layoutRows; row++) for (let col = 0; col < layout.layoutCols; col++) add(row, col)
  } else if (layout.layoutPattern === 'S型横排') {
    for (let row = 0; row < layout.layoutRows; row++) {
      if (row % 2 === 0) for (let col = 0; col < layout.layoutCols; col++) add(row, col)
      else for (let col = layout.layoutCols - 1; col >= 0; col--) add(row, col)
    }
  } else if (layout.layoutPattern === 'Z型竖排') {
    for (let col = 0; col < layout.layoutCols; col++) for (let row = 0; row < layout.layoutRows; row++) add(row, col)
  } else {
    for (let col = 0; col < layout.layoutCols; col++) {
      if (col % 2 === 0) for (let row = 0; row < layout.layoutRows; row++) add(row, col)
      else for (let row = layout.layoutRows - 1; row >= 0; row--) add(row, col)
    }
  }
  return mapping
}

export function mirrorSeatLayout(layoutValue: Partial<SeatLayout>, mirrored = false): SeatLayout {
  const layout = normalizeSeatLayout(layoutValue)
  if (!mirrored) return layout
  return {
    ...layout,
    startPos: layout.startPos === 'right' ? 'left' : 'right',
  }
}

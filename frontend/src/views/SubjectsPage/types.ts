export interface Subject {
  name: string
  exam_date: string
  exam_time: string
  duration_minutes: number
  remark: string
}

export type UiLogLevel = 'info' | 'success' | 'warning' | 'error'

export interface UiLogEntry {
  time: string
  level: UiLogLevel
  msg: string
}

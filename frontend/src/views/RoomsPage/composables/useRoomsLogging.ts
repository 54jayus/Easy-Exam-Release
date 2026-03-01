import { ref } from 'vue'
import dayjs from 'dayjs'
import type { UiLogLevel } from './useRoomsState'

export interface LogEntry {
  time: string
  level: UiLogLevel
  msg: string
}

export function useRoomsLogging() {
  const logs = ref<LogEntry[]>([])

  const pushLog = (level: UiLogLevel, msg: string) => {
    logs.value.unshift({
      time: dayjs().format('HH:mm:ss'),
      level,
      msg
    })
  }

  const logInfo = (msg: string) => pushLog('info', msg)
  const logSuccess = (msg: string) => pushLog('success', msg)
  const logWarning = (msg: string) => pushLog('warning', msg)
  const logError = (msg: string) => pushLog('error', msg)

  const logFromText = (msg: string) => {
    const m = String(msg || '')
    if (m.includes('失败') || m.includes('异常') || m.includes('错误')) {
      return logError(m)
    }
    if (m.includes('警告')) {
      return logWarning(m)
    }
    if (m.includes('成功') || m.includes('完成')) {
      return logSuccess(m)
    }
    return logInfo(m)
  }

  const clearLogs = () => {
    logs.value = []
  }

  return {
    logs,
    pushLog,
    logInfo,
    logSuccess,
    logWarning,
    logError,
    logFromText,
    clearLogs
  }
}

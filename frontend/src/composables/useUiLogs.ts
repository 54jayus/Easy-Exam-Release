import { ref } from 'vue'
import dayjs from 'dayjs'
import { pythonBackend } from '@/lib/pythonBackend'

export type UiLogLevel = 'info' | 'success' | 'warning' | 'error'

export interface UiLogEntry {
  time: string
  level: UiLogLevel
  msg: string
}

type AttachBackendLogsOptions = {
  rpcErrorPrefix?: string
  stdoutPrefix?: string
  stderrPrefix?: string
  maxLineLength?: number
}

export function useUiLogs() {
  const showLogs = ref(false)
  const logs = ref<UiLogEntry[]>([])

  const pushLog = (level: UiLogLevel, msg: string) => {
    logs.value.unshift({ time: dayjs().format('HH:mm:ss'), level, msg })
  }

  const logInfo = (msg: string) => pushLog('info', msg)
  const logSuccess = (msg: string) => pushLog('success', msg)
  const logWarning = (msg: string) => pushLog('warning', msg)
  const logError = (msg: string) => pushLog('error', msg)

  const logFromText = (msg: string) => {
    const text = String(msg || '')
    if (text.includes('失败') || text.includes('异常') || text.includes('错误')) return logError(text)
    if (text.includes('警告')) return logWarning(text)
    if (text.includes('成功') || text.includes('完成')) return logSuccess(text)
    return logInfo(text)
  }

  const clearLogs = () => {
    logs.value = []
  }

  const attachBackendLogs = (options: AttachBackendLogsOptions = {}) =>
    pythonBackend.onLog((msg, type) => {
      const maxLineLength = Math.max(20, Number(options.maxLineLength ?? 300) || 300)
      const rpcErrorPrefix = options.rpcErrorPrefix ?? '后端 RPC 失败'
      const stdoutPrefix = options.stdoutPrefix ?? '后端stdout'
      const stderrPrefix = options.stderrPrefix ?? '后端stderr'

      if (type === 'stdout') {
        try {
          const obj = JSON.parse(msg)
          if (obj.id !== undefined && (obj.result !== undefined || obj.error !== undefined)) {
            if (obj.error) {
              logError(`${rpcErrorPrefix}：${String(obj.error)}`)
            }
            return
          }
        } catch {}
      }

      const displayMsg = msg.length > maxLineLength ? `${msg.slice(0, maxLineLength)}...` : msg
      pushLog(type === 'stderr' ? 'warning' : 'info', `${type === 'stderr' ? stderrPrefix : stdoutPrefix}：${displayMsg}`)
    })

  return {
    showLogs,
    logs,
    pushLog,
    logInfo,
    logSuccess,
    logWarning,
    logError,
    logFromText,
    clearLogs,
    attachBackendLogs,
  }
}

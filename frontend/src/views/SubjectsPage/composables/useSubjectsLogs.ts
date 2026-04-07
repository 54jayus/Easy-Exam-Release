import { ref } from 'vue'
import dayjs from 'dayjs'
import { pythonBackend } from '@/lib/pythonBackend'
import type { UiLogEntry, UiLogLevel } from '../types'

export function useSubjectsLogs() {
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

  const attachBackendLogs = () =>
    pythonBackend.onLog((msg, type) => {
      if (type === 'stdout') {
        try {
          const obj = JSON.parse(msg)
          if (obj.id !== undefined && (obj.result !== undefined || obj.error !== undefined)) {
            if (obj.error) {
              logError(`后端 RPC 失败：${String(obj.error)}`)
            }
            return
          }
        } catch {}
      }

      const displayMsg = msg.length > 300 ? `${msg.slice(0, 300)}...` : msg
      pushLog(type === 'stderr' ? 'warning' : 'info', `后端${type === 'stderr' ? 'stderr' : 'stdout'}：${displayMsg}`)
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
    attachBackendLogs,
  }
}

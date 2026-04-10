import { ElMessage, ElMessageBox } from 'element-plus'

type FeedbackLevel = 'info' | 'success' | 'warning' | 'error'

type UiLogHandlers = Partial<{
  logInfo: (msg: string) => void
  logSuccess: (msg: string) => void
  logWarning: (msg: string) => void
  logError: (msg: string) => void
}>

type NotifyOptions = {
  toast?: boolean
  toastMessage?: string
  log?: boolean
  logMessage?: string
}

type ConfirmOptions = {
  message: string
  title: string
  type?: 'success' | 'warning' | 'info' | 'error'
  confirmButtonText?: string
  cancelButtonText?: string
  closeOnClickModal?: boolean
}

const loggerByLevel: Record<FeedbackLevel, keyof UiLogHandlers> = {
  info: 'logInfo',
  success: 'logSuccess',
  warning: 'logWarning',
  error: 'logError',
}

const toastByLevel: Record<FeedbackLevel, (message: string) => void> = {
  info: (message) => ElMessage.info(message),
  success: (message) => ElMessage.success(message),
  warning: (message) => ElMessage.warning(message),
  error: (message) => ElMessage.error(message),
}

export const normalizeMessage = (value: unknown): string => {
  if (value instanceof Error) return value.message || value.name || '未知错误'
  if (typeof value === 'string') return value.trim() || '未知错误'
  if (value === null || value === undefined) return '未知错误'
  return String(value)
}

export const formatActionStart = (action: string) => `开始${action}`

export const formatActionProgress = (action: string, detail?: string) =>
  detail ? `正在${action}：${detail}` : `正在${action}`

export const formatActionSuccess = (action: string, detail?: string) =>
  detail ? `已${action}：${detail}` : `已${action}`

export const formatActionWarning = (action: string, detail: string) =>
  `${action}提示：${detail}`

export const formatActionError = (action: string, error: unknown) =>
  `${action}失败：${normalizeMessage(error)}`

export function createUiFeedback(logHandlers: UiLogHandlers = {}) {
  const notify = (level: FeedbackLevel, message: string, options: NotifyOptions = {}) => {
    const logEnabled = options.log ?? true
    const toastEnabled = options.toast ?? level !== 'info'
    const logMessage = options.logMessage ?? message
    const toastMessage = options.toastMessage ?? message

    if (logEnabled) {
      const loggerName = loggerByLevel[level]
      const logger = logHandlers[loggerName]
      logger?.(logMessage)
    }
    if (toastEnabled) {
      toastByLevel[level](toastMessage)
    }
  }

  return {
    info(message: string, options?: NotifyOptions) {
      notify('info', message, options)
    },
    success(message: string, options?: NotifyOptions) {
      notify('success', message, options)
    },
    warning(message: string, options?: NotifyOptions) {
      notify('warning', message, options)
    },
    error(message: string, options?: NotifyOptions) {
      notify('error', message, options)
    },
    confirm(options: ConfirmOptions) {
      return ElMessageBox.confirm(options.message, options.title, {
        type: options.type ?? 'warning',
        confirmButtonText: options.confirmButtonText ?? '确定',
        cancelButtonText: options.cancelButtonText ?? '取消',
        closeOnClickModal: options.closeOnClickModal,
      })
    },
    confirmWarning(options: ConfirmOptions) {
      return this.confirm({ ...options, type: 'warning' })
    },
    alertError(title: string, message: string, options: { logMessage?: string } = {}) {
      if (options.logMessage) {
        logHandlers.logError?.(options.logMessage)
      }
      return ElMessageBox.alert(message, title, { type: 'error' })
    },
  }
}

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

export type LogEntry = {
  level: LogLevel
  scope: string
  message: string
  data?: unknown
}

function nowIso(): string {
  return new Date().toISOString()
}

function safeJson(value: unknown): string {
  try {
    return JSON.stringify(value)
  } catch {
    return '"[无法序列化]"'
  }
}

export function log(entry: LogEntry): void {
  const ts = nowIso()
  const prefix = `[${ts}] [${entry.level.toUpperCase()}] [${entry.scope}] ${entry.message}`

  if (window.electron?.ipcRenderer?.send) {
    try {
      window.electron.ipcRenderer.send('renderer-log', entry)
    } catch {}
  }

  const line = entry.data === undefined ? prefix : `${prefix} ${safeJson(entry.data)}`
  if (entry.level === 'error') console.error(line)
  else if (entry.level === 'warn') console.warn(line)
  else console.log(line)
}

export function createLogger(scope: string) {
  const s = scope.trim() || 'app'
  return {
    debug(message: string, data?: unknown) {
      log({ level: 'debug', scope: s, message, data })
    },
    info(message: string, data?: unknown) {
      log({ level: 'info', scope: s, message, data })
    },
    warn(message: string, data?: unknown) {
      log({ level: 'warn', scope: s, message, data })
    },
    error(message: string, data?: unknown) {
      log({ level: 'error', scope: s, message, data })
    },
  }
}

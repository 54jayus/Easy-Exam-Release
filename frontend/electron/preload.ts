import { ipcRenderer, contextBridge } from 'electron'

const ALLOWED_INVOKE_CHANNELS = [
  'spawn_python', 'write_python', 'kill_python',
  'backend_project_root', 'app_exe_dir',
  'open_path', 'open_external',
  'dialog:open', 'dialog:save',
  'open-devtools',
  'update:getCurrentVersion', 'update:getHistory', 'update:check',
  'update:startDownload', 'update:pauseDownload', 'update:installDownloaded',
  'reset-tray-tip',
] as const

const ALLOWED_ON_CHANNELS = [
  'python-stdout', 'python-stderr', 'python-exit', 'python-error',
  'main-process-message',
  'update-progress', 'update-downloaded', 'update-error',
  'tray-dialog-open',
] as const

const ALLOWED_SEND_CHANNELS = ['renderer-log', 'tray-dialog-response'] as const

type InvokeChannel = typeof ALLOWED_INVOKE_CHANNELS[number]
type OnChannel = typeof ALLOWED_ON_CHANNELS[number]
type SendChannel = typeof ALLOWED_SEND_CHANNELS[number]

contextBridge.exposeInMainWorld('electron', {
  ipcRenderer: {
    invoke(channel: InvokeChannel, ...args: any[]) {
      if (!(ALLOWED_INVOKE_CHANNELS as readonly string[]).includes(channel)) {
        throw new Error(`IPC invoke channel not allowed: ${channel}`)
      }
      return ipcRenderer.invoke(channel, ...args)
    },
    on(channel: OnChannel, listener: (event: any, ...args: any[]) => void) {
      if (!(ALLOWED_ON_CHANNELS as readonly string[]).includes(channel)) {
        throw new Error(`IPC on channel not allowed: ${channel}`)
      }
      ipcRenderer.on(channel, listener)
      return () => ipcRenderer.removeListener(channel, listener)
    },
    off(channel: OnChannel, listener: (...args: any[]) => void) {
      ipcRenderer.removeListener(channel, listener)
    },
    send(channel: SendChannel, ...args: any[]) {
      if (!(ALLOWED_SEND_CHANNELS as readonly string[]).includes(channel)) {
        throw new Error(`IPC send channel not allowed: ${channel}`)
      }
      ipcRenderer.send(channel, ...args)
    },
  },
})

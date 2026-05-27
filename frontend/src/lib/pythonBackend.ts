import { isElectron } from "./env"
import { createLogger } from "./logger"
import type { RpcMethods } from "../types/rpc"

type RpcOk<T> = { ok: true; result: T; id?: string | number }
type RpcErr = { ok: false; error: string; id?: string | number }
type RpcReply<T> = RpcOk<T> | RpcErr

export class PythonBackendClient {
  private child: { pid: number; kill(): Promise<void>; write(data: string | number[]): Promise<void> } | null =
    null
  private command: string | null = null
  private starting: Promise<void> | null = null
  private buffer = ""
  private stderrBuffer = ""
  private lastStderr = ""
  private backendRoot: string | null = null
  private exeDir: string | null = null
  private pending = new Map<string, { resolve: (v: any) => void; reject: (e: Error) => void; timeoutId?: ReturnType<typeof setTimeout> }>()
  private seq = 0
  private logListeners: ((msg: string, type: 'stdout' | 'stderr') => void)[] = []
  private logger = createLogger('pythonBackend')
  // Track IPC listeners so we can remove them on stop() to prevent leaks
  private _stdoutListener: ((e: any, data: string) => void) | null = null
  private _stderrListener: ((e: any, data: string) => void) | null = null
  private _exitListener: ((e: any, data: any) => void) | null = null
  private _errorListener: ((e: any, msg: string) => void) | null = null

  onLog(listener: (msg: string, type: 'stdout' | 'stderr') => void): () => void {
    this.logListeners.push(listener)
    return () => {
      this.logListeners = this.logListeners.filter(l => l !== listener)
    }
  }

  private emitLog(msg: string, type: 'stdout' | 'stderr'): void {
    for (const listener of this.logListeners) {
      try {
        listener(msg, type)
      } catch (e) {
        this.logger.error('日志回调执行失败', e)
      }
    }
  }

  private async getBackendRoot(): Promise<string> {
    if (this.backendRoot) return this.backendRoot
    let root = ""
    if (isElectron()) {
      root = await (window as any).electron.ipcRenderer.invoke("backend_project_root")
    }
    this.backendRoot = root
    return root
  }

  private async getExeDir(): Promise<string> {
    if (this.exeDir) return this.exeDir
    let dir = ""
    if (isElectron()) {
      dir = await (window as any).electron.ipcRenderer.invoke("app_exe_dir")
    }
    this.exeDir = dir
    return dir
  }

  async start(): Promise<void> {
    if (!isElectron()) {
      throw new Error("仅在 Electron 桌面端可用")
    }
    if (this.child) return
    if (this.starting) return this.starting

    this.starting = (async () => {
      const root = await this.getBackendRoot()
      const exeDir = await this.getExeDir()

      const tryStart = async (commandName: string, isSidecar: boolean) => {
        this.stderrBuffer = ""
        this.lastStderr = ""
        
        if (isElectron()) {
          // Electron Implementation
          const electron = (window as any).electron
          
          // Register IPC listeners with proper tracking to allow cleanup on stop()
          this._registerIpcListeners(electron)

          const env: Record<string, string> = {
            PYTHONUNBUFFERED: "1",
            PYTHONUTF8: "1",
            PYTHONIOENCODING: "utf-8",
          }
          env.PYTHONPATH = root
          if (exeDir && exeDir.trim()) {
             env.EXAMFLOW_APP_DIR = exeDir
             env.EXAMDESK_APP_DIR = exeDir
          }
          
          // Determine python command
          let cmd = commandName
          let args: string[] = []
          
          if (isSidecar) {
             // In Electron sidecar usually means bundled executable
             // For now assuming same name or path
             // TODO: Handle sidecar path logic for Electron if needed
             cmd = commandName
          } else {
             cmd = 'python'
             args = ["-m", "backend"]
          }

          const result = await electron.ipcRenderer.invoke('spawn_python', {
             command: cmd,
             args,
             options: {
                cwd: root,
                env
             }
          })

          if (result.error) {
             throw new Error(result.error)
          }

          this.child = {
             pid: result.pid,
             kill: async () => { await electron.ipcRenderer.invoke('kill_python') },
             write: async (data: any) => { 
                let d = data
                if (typeof data !== 'string' && !Array.isArray(data)) {
                   // payload could be something else?
                }
                if (Array.isArray(data)) {
                   d = new TextDecoder().decode(new Uint8Array(data))
                }
                await electron.ipcRenderer.invoke('write_python', d) 
             }
          }
        }
      }

      const candidates = [
        { name: "engine", sidecar: true },
      ]

      let lastError: unknown = null
      for (const c of candidates) {
        try {
          await tryStart(c.name, c.sidecar)
          return
        } catch (e) {
          lastError = e
        }
      }
      throw lastError instanceof Error ? lastError : new Error(String(lastError))
    })().finally(() => {
      this.starting = null
    })

    return this.starting
  }

  private _registerIpcListeners(electron: any): void {
    this._removeIpcListeners(electron)
    this._stdoutListener = (_: any, data: string) => this.onStdout(data)
    this._stderrListener = (_: any, data: string) => this.onStderr(data)
    this._exitListener = (_: any, e: any) => {
      const extra = this.lastStderr ? `\n\nstderr:\n${this.lastStderr}` : ""
      const err = new Error(`后端进程已退出（code=${e.code}, signal=${e.signal ?? "null"}）${extra}`)
      for (const [, p] of this.pending) p.reject(err)
      this.pending.clear()
      this.child = null
    }
    this._errorListener = (_: any, msg: string) => {
      const err = new Error(msg)
      for (const [, p] of this.pending) p.reject(err)
      this.pending.clear()
      this.child = null
    }
    electron.ipcRenderer.on('python-stdout', this._stdoutListener)
    electron.ipcRenderer.on('python-stderr', this._stderrListener)
    electron.ipcRenderer.on('python-exit', this._exitListener)
    electron.ipcRenderer.on('python-error', this._errorListener)
  }

  private _removeIpcListeners(electron: any): void {
    if (this._stdoutListener) electron.ipcRenderer.off('python-stdout', this._stdoutListener)
    if (this._stderrListener) electron.ipcRenderer.off('python-stderr', this._stderrListener)
    if (this._exitListener) electron.ipcRenderer.off('python-exit', this._exitListener)
    if (this._errorListener) electron.ipcRenderer.off('python-error', this._errorListener)
    this._stdoutListener = null
    this._stderrListener = null
    this._exitListener = null
    this._errorListener = null
  }

  async stop(): Promise<void> {
    if (isElectron()) {
      this._removeIpcListeners((window as any).electron)
    }
    const child = this.child
    this.child = null
    this.command = null
    this.buffer = ""

    // 关键修复：清理所有监听器
    this.logListeners = []

    for (const [, p] of this.pending) p.reject(new Error("后端连接已关闭"))
    this.pending.clear()
    if (child) await child.kill()
  }

  async request<M extends keyof RpcMethods>(
    method: M,
    ...args: RpcMethods[M]["params"] extends Record<string, never>
      ? [params?: RpcMethods[M]["params"], timeoutMs?: number]
      : [params: RpcMethods[M]["params"], timeoutMs?: number]
  ): Promise<RpcMethods[M]["result"]> {
    const [params = {} as RpcMethods[M]["params"], timeoutMs = 120_000] = args

    await this.start()
    if (!this.child) throw new Error("后端未启动")

    const id = String(++this.seq)
    const payload = JSON.stringify({ id, method, params }, undefined, 0) + "\n"

    const p = new Promise<RpcMethods[M]["result"]>((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        const item = this.pending.get(id)
        if (!item) return
        // 关键修复：清理 Map 条目
        this.pending.delete(id)
        reject(new Error("后端请求超时"))
      }, timeoutMs)

      // 保存 resolve, reject 和 timeoutId
      this.pending.set(id, { resolve, reject, timeoutId })
    })

    await this.child.write(payload)
    return p
  }

  private onStdout(chunk: string): void {
    this.buffer += chunk
    while (true) {
      const idx = this.buffer.indexOf("\n")
      if (idx < 0) break
      const line = this.buffer.slice(0, idx).trim()
      this.buffer = this.buffer.slice(idx + 1)
      if (!line) continue
      
      // Try to parse as JSON first to see if it's an RPC message
      // But we emit it as log regardless, or maybe filter? 
      // User wants to see what's happening, so logging everything is safer.
      this.emitLog(line, 'stdout')
      this.onLine(line)
    }
  }

  private onStderr(_chunk: string): void {
    this.emitLog(_chunk, 'stderr')
    this.stderrBuffer += _chunk
    const lines = this.stderrBuffer.split(/\r?\n/).filter((l) => l.trim().length > 0)
    const tail = lines.slice(-40).join("\n")
    this.lastStderr = tail
  }

  private onLine(line: string): void {
    let msg: RpcReply<any>
    try {
      msg = JSON.parse(line)
    } catch {
      return
    }
    const id = msg.id
    if (id == null) return
    const pending = this.pending.get(String(id))
    if (!pending) return

    // 关键修复：清理 timeout
    if (pending.timeoutId) {
      clearTimeout(pending.timeoutId)
    }

    // 清理 Map 条目
    this.pending.delete(String(id))

    if (msg.ok) pending.resolve(msg.result)
    else {
      const rawError: any = msg.error
      const message =
        typeof rawError === 'string'
          ? rawError
          : (rawError?.message || rawError?.code || JSON.stringify(rawError))
      const error = new Error(message) as Error & {
        code?: string | number
        details?: Record<string, unknown>
        raw?: unknown
      }
      if (rawError && typeof rawError === 'object') {
        error.code = rawError.code
        error.details = rawError.details
        error.raw = rawError
      }
      pending.reject(error)
    }
  }
}

export const pythonBackend = new PythonBackendClient()

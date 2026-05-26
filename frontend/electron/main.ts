import { app, BrowserWindow, ipcMain, shell, dialog, Menu, globalShortcut } from 'electron'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawn, type ChildProcess } from 'node:child_process'
import fs from 'node:fs'

// Set stdout/stderr encoding to UTF-8 for Windows
if (process.platform === 'win32') {
  if (process.stdout.setDefaultEncoding) {
    process.stdout.setDefaultEncoding('utf-8')
  }
  if (process.stderr.setDefaultEncoding) {
    process.stderr.setDefaultEncoding('utf-8')
  }
}

const __dirname = path.dirname(fileURLToPath(import.meta.url))

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

const logPath = app.isPackaged
  ? path.join(path.dirname(app.getPath('exe')), 'debug.log')
  : path.join(process.cwd(), 'debug.log')

const LOG_MAX_BYTES = 5 * 1024 * 1024
const LOG_BACKUPS = 3

type RuntimeConfig = {
  EXAM_PYTHON_MODE?: string
  EXAM_CONDA_ENV?: string
  EXAM_CONDA_EXE?: string
  EXAM_PYTHON_EXE?: string
}

function getProjectRoot(): string {
  return path.resolve(__dirname, '../..')
}

function parseEnvFile(filePath: string): RuntimeConfig {
  const result: RuntimeConfig = {}
  if (!fs.existsSync(filePath)) return result
  const text = fs.readFileSync(filePath, 'utf-8')
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const eqIndex = line.indexOf('=')
    if (eqIndex <= 0) continue
    const key = line.slice(0, eqIndex).trim()
    let value = line.slice(eqIndex + 1).trim()
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    }
    ;(result as Record<string, string>)[key] = value
  }
  return result
}

function loadRuntimeConfig(): RuntimeConfig {
  const projectRoot = getProjectRoot()
  const localPath = path.join(projectRoot, '.env.runtime.local')
  const examplePath = path.join(projectRoot, '.env.runtime.example')
  if (fs.existsSync(localPath)) return parseEnvFile(localPath)
  return parseEnvFile(examplePath)
}

function resolveDevPythonCommand(): { command: string; argsPrefix: string[]; source: string } {
  const config = loadRuntimeConfig()
  const explicitPython = String(config.EXAM_PYTHON_EXE || '').trim()
  if (explicitPython) {
    return { command: explicitPython, argsPrefix: [], source: 'EXAM_PYTHON_EXE' }
  }

  const mode = String(config.EXAM_PYTHON_MODE || '').trim().toLowerCase()
  const condaEnv = String(config.EXAM_CONDA_ENV || '').trim()
  if (mode === 'conda' || condaEnv) {
    if (!condaEnv) {
      throw new Error('运行环境配置缺少 EXAM_CONDA_ENV')
    }
    const condaExe = String(config.EXAM_CONDA_EXE || 'conda').trim() || 'conda'
    return {
      command: condaExe,
      argsPrefix: ['run', '--no-capture-output', '-n', condaEnv, 'python'],
      source: 'conda',
    }
  }

  return { command: 'python', argsPrefix: [], source: 'PATH:python' }
}

function rotateLogsIfNeeded() {
  try {
    const stat = fs.existsSync(logPath) ? fs.statSync(logPath) : null
    if (!stat || stat.size <= LOG_MAX_BYTES) return

    for (let i = LOG_BACKUPS - 1; i >= 1; i--) {
      const src = `${logPath}.${i}`
      const dst = `${logPath}.${i + 1}`
      if (fs.existsSync(src)) {
        try {
          fs.renameSync(src, dst)
        } catch {}
      }
    }

    try {
      fs.renameSync(logPath, `${logPath}.1`)
    } catch {}
  } catch {}
}

function safeJson(value: unknown): string {
  try {
    return JSON.stringify(value)
  } catch {
    return '"[unserializable]"'
  }
}

function redactSecrets(input: unknown, depth = 0): unknown {
  if (depth > 6) return '[max_depth]'
  if (input == null) return input
  if (typeof input !== 'object') return input
  if (Array.isArray(input)) return input.slice(0, 50).map((v) => redactSecrets(v, depth + 1))

  const obj = input as Record<string, unknown>
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(obj)) {
    const key = k.toLowerCase()
    const isSecret =
      key.includes('apikey') ||
      key.includes('api_key') ||
      key.includes('token') ||
      key.includes('secret') ||
      key.includes('password') ||
      key.includes('license')
    out[k] = isSecret ? '[redacted]' : redactSecrets(v, depth + 1)
  }
  return out
}

function parseJsonLine(line: string): any | null {
  try {
    return JSON.parse(line)
  } catch {
    return null
  }
}

function shouldIgnorePythonStderrLine(line: string): boolean {
  const normalized = String(line || '').trim()
  if (!normalized) return true
  return normalized.includes('numexpr.utils: NumExpr defaulting to') && normalized.includes('threads')
}

function logToFileLine(line: string) {
  try {
    rotateLogsIfNeeded()
    fs.appendFileSync(logPath, line + '\n')
  } catch (e) {
    console.error('写入日志失败:', e)
  }
}

function log(level: LogLevel, scope: string, message: string, data?: unknown) {
  const ts = new Date().toISOString()
  const base = `[${ts}] [${level.toUpperCase()}] [${scope}] ${message}`
  const line = data === undefined ? base : `${base} ${safeJson(redactSecrets(data))}`
  logToFileLine(line)

  const consoleLine = data === undefined ? base : `${base} ${safeJson(data)}`
  if (level === 'error') console.error(consoleLine)
  else if (level === 'warn') console.warn(consoleLine)
  else console.log(consoleLine)
}

process.on('uncaughtException', (err) => {
  log('error', 'main', '未捕获异常', { message: err?.message, stack: err?.stack })
})

process.on('unhandledRejection', (reason: any) => {
  log('error', 'main', '未处理的 Promise 拒绝', { reason: typeof reason === 'string' ? reason : reason?.message ?? String(reason) })
})

// The built directory structure
//
// ├─┬─ dist
// │ └─ index.html
// ├─┬─ dist-electron
// │ ├─ main.js
// │ └─ preload.js
// └─ dist-electron/index.js (if using vite-plugin-electron default)

process.env.DIST = path.join(__dirname, '../dist')
process.env.VITE_PUBLIC = app.isPackaged ? process.env.DIST : path.join(process.env.DIST, '../public')

let win: BrowserWindow | null

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']

function createWindow() {
  log('info', 'window', '开始创建主窗口', {
    isPackaged: app.isPackaged,
    dist: process.env.DIST,
    vitePublic: process.env.VITE_PUBLIC,
    devServerUrl: VITE_DEV_SERVER_URL || null,
  })

  win = new BrowserWindow({
    width: 1200,
    height: 800,
    autoHideMenuBar: true,
    icon: path.join(process.env.VITE_PUBLIC, 'icon.png'), // Try to use existing icon
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
      webSecurity: false,
    },
  })

  // Test active push message to Renderer-process.
  win.webContents.on('did-finish-load', () => {
    log('info', 'window', '主窗口页面加载完成')
    win?.webContents.send('main-process-message', (new Date).toLocaleString())
  })

  win.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL, isMainFrame) => {
    log('error', 'window', '页面加载失败', {
      errorCode,
      errorDescription,
      validatedURL,
      isMainFrame,
    })
  })

  win.webContents.on('did-fail-provisional-load', (_event, errorCode, errorDescription, validatedURL, isMainFrame) => {
    log('error', 'window', '页面预加载失败', {
      errorCode,
      errorDescription,
      validatedURL,
      isMainFrame,
    })
  })

  win.webContents.on('render-process-gone', (_event, details) => {
    log('error', 'window', '渲染进程退出', details)
  })

  win.webContents.on('console-message', (_event, level, message, line, sourceId) => {
    const mappedLevel: LogLevel = level >= 3 ? 'error' : level === 2 ? 'warn' : 'info'
    log(mappedLevel, 'renderer-console', message, { line, sourceId })
  })

  win.once('ready-to-show', () => {
    log('info', 'window', '主窗口 ready-to-show')
  })

  if (VITE_DEV_SERVER_URL) {
    log('info', 'window', '加载开发服务器页面', { url: VITE_DEV_SERVER_URL })
    win.loadURL(VITE_DEV_SERVER_URL).catch((error) => {
      log('error', 'window', 'loadURL 失败', { message: error instanceof Error ? error.message : String(error) })
    })
  } else {
    const indexPath = path.join(process.env.DIST, 'index.html')
    log('info', 'window', '加载本地页面', { indexPath })
    win.loadFile(indexPath).catch((error) => {
      log('error', 'window', 'loadFile 失败', {
        indexPath,
        message: error instanceof Error ? error.message : String(error),
      })
    })
  }

  win.on('closed', () => {
    log('info', 'window', '主窗口已关闭')
    win = null
  })

  // Enable right-click context menu
  win.webContents.on('context-menu', (event, params) => {
    const menu = Menu.buildFromTemplate([
      { label: '复制', role: 'copy', enabled: params.editFlags.canCopy },
      { label: '粘贴', role: 'paste', enabled: params.editFlags.canPaste },
      { label: '剪切', role: 'cut', enabled: params.editFlags.canCut },
      { type: 'separator' },
      { label: '全选', role: 'selectAll', enabled: params.editFlags.canSelectAll },
    ])
    menu.popup()
  })
}

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    // Ensure python process is killed
    if (pythonProcess) {
      pythonProcess.kill()
    }
  }
})

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.whenReady().then(() => {
  log('info', 'main', 'Electron 已 ready', {
    isPackaged: app.isPackaged,
    exePath: app.getPath('exe'),
    userData: app.getPath('userData'),
  })
  Menu.setApplicationMenu(null)
  createWindow()

  globalShortcut.register('CommandOrControl+Shift+I', () => {
    const focused = BrowserWindow.getFocusedWindow()
    if (focused) focused.webContents.toggleDevTools()
  })
})

// --- IPC Handlers ---

// Replicate backend_project_root
ipcMain.handle('backend_project_root', () => {
  // In dev: frontend -> root is ../ (one level up)
  // In prod: resources/.. depending on packaging.
  if (!app.isPackaged) {
    return path.resolve(process.cwd(), '../')
  } else {
    // In production, return resources directory or fallback to app directory
    // Ensure we don't pass undefined to path methods
    return (process as any).resourcesPath || path.dirname(app.getPath('exe'))
  }
})

// Replicate app_exe_dir
ipcMain.handle('app_exe_dir', () => {
  return path.dirname(app.getPath('exe'))
})

// Replicate open_path
ipcMain.handle('open_path', async (_, p) => {
  try {
    const stat = await fs.promises.stat(p)
    if (stat.isFile()) {
      shell.showItemInFolder(p)
    } else {
      shell.openPath(p)
    }
  } catch (e) {
    log('error', 'open_path', '打开路径失败', { path: p, error: e instanceof Error ? e.message : String(e) })
  }
})

// Open external URL
ipcMain.handle('open_external', async (_, url) => {
  try {
    await shell.openExternal(url)
  } catch (e) {
    log('error', 'open_external', '打开外部链接失败', { url, error: e instanceof Error ? e.message : String(e) })
  }
})

// Python Process Management
let pythonProcess: ChildProcess | null = null

ipcMain.handle('spawn_python', (_, { command, args, options }) => {
  log('info', 'python', '收到启动请求', { command, args })
  
  let finalCommand = command
  let finalArgs = args || []

  if (command === 'engine') {
    if (app.isPackaged) {
      // In production, engine is at resources/engine/engine.exe
      // process.resourcesDir points to the resources folder (e.g. win-unpacked/resources)
      const resourcesPath = (process as any).resourcesPath || path.join(path.dirname(app.getPath('exe')), 'resources')
      // Note: On Windows, the binary is engine.exe inside the engine folder
      // Structure: resources/engine/engine.exe
      finalCommand = path.join(resourcesPath, 'engine', 'engine.exe')
      const engineCwd = path.join(resourcesPath, 'engine')
      options = { ...(options || {}), cwd: engineCwd }
    } else {
      const resolved = resolveDevPythonCommand()
      finalCommand = resolved.command
      finalArgs = [...resolved.argsPrefix, '-m', 'backend', ...finalArgs]
      log('info', 'python', '开发环境运行配置已生效', {
        source: resolved.source,
        command: finalCommand,
        args: finalArgs,
      })
    }
  }

  log('info', 'python', '解析启动命令', { command: finalCommand, args: finalArgs })

  // Reuse existing process if running
  if (pythonProcess && !pythonProcess.killed) {
    log('info', 'python', '后端进程已在运行，复用现有进程', { pid: pythonProcess.pid })
    return { pid: pythonProcess.pid }
  }

  // Clean up existing process if any (zombie)
  if (pythonProcess) {
    try {
      pythonProcess.kill()
    } catch (e) {}
  }

  try {
    const finalEnv = { ...process.env, ...options?.env }
    if (!finalEnv.EXAMFLOW_DATA_DIR && !finalEnv.EXAMDESK_DATA_DIR) {
      const userData = app.getPath('userData')
      finalEnv.EXAMFLOW_DATA_DIR = userData
      finalEnv.EXAMDESK_DATA_DIR = userData
    }
    const finalOptions = { ...options, env: finalEnv }

    const cmd = spawn(finalCommand, finalArgs, finalOptions)
    pythonProcess = cmd
    const pid = cmd.pid

    const sendToAll = (channel: string, data: any) => {
      if (win && !win.isDestroyed()) win.webContents.send(channel, data)
    }

    cmd.stdout?.on('data', (data) => {
      const chunk = data.toString('utf-8')
      sendToAll('python-stdout', chunk)
      const lines = chunk.split(/\r?\n/)
      for (const raw of lines) {
        const line = raw.trim()
        if (!line) continue
        const parsed = parseJsonLine(line)
        if (parsed && typeof parsed === 'object' && 'ok' in parsed && 'id' in parsed) {
          log('debug', 'python', 'RPC 响应', { id: (parsed as any).id, ok: (parsed as any).ok, error: (parsed as any).error })
        } else {
          log('debug', 'python', '标准输出', line.length > 2000 ? line.slice(0, 2000) + '…' : line)
        }
      }
    })

    cmd.stderr?.on('data', (data) => {
      const chunk = data.toString('utf-8')
      sendToAll('python-stderr', chunk)
      const lines = chunk.split(/\r?\n/)
      for (const raw of lines) {
        const line = raw.trim()
        if (!line) continue
        if (shouldIgnorePythonStderrLine(line)) continue
        log('warn', 'python', '标准错误', line.length > 2000 ? line.slice(0, 2000) + '…' : line)
      }
    })

    cmd.on('close', (code, signal) => {
      log('warn', 'python', '后端进程已退出', { pid, code, signal })
      sendToAll('python-exit', { code, signal })
      if (pythonProcess === cmd) {
        pythonProcess = null
      }
    })

    cmd.on('error', (err) => {
      log('error', 'python', '后端进程错误', { pid, message: err.message })
      sendToAll('python-error', err.message)
    })

    log('info', 'python', '后端进程已启动', { pid })
    return { pid }
  } catch (e: any) {
    log('error', 'python', '启动后端失败', { message: e?.message ?? String(e) })
    return { error: e.message }
  }
})

ipcMain.handle('kill_python', () => {
  if (pythonProcess) {
    pythonProcess.kill()
    pythonProcess = null
  }
  return true
})

ipcMain.handle('write_python', (_, data) => {
    if (pythonProcess && pythonProcess.stdin) {
      const payload = typeof data === 'string' ? data : String(data)
      const line = payload.trim()
      const parsed = parseJsonLine(line)
      if (parsed && typeof parsed === 'object') {
        log('debug', 'python', 'RPC 请求', {
          id: (parsed as any).id,
          method: (parsed as any).method,
          params: (parsed as any).params,
        })
      } else {
        log('debug', 'python', '写入标准输入', { bytes: Buffer.byteLength(payload, 'utf8') })
      }
      pythonProcess.stdin.write(data, 'utf-8')
    }
  })

ipcMain.on('renderer-log', (_event, entry: any) => {
  const level: LogLevel = entry?.level === 'debug' || entry?.level === 'info' || entry?.level === 'warn' || entry?.level === 'error' ? entry.level : 'info'
  const scope = typeof entry?.scope === 'string' && entry.scope.trim() ? entry.scope : 'renderer'
  const message = typeof entry?.message === 'string' ? entry.message : safeJson(entry?.message)
  log(level, scope, message, entry?.data)
})

  ipcMain.handle('dialog:open', async (_, options) => {
    try {
      const properties: ('openFile' | 'openDirectory' | 'multiSelections')[] = ['openFile']
      if (options?.multiple) {
        properties.push('multiSelections')
      }
      if (options?.directory) {
        properties.push('openDirectory')
        const idx = properties.indexOf('openFile')
        if (idx > -1) properties.splice(idx, 1)
      }

      // Use the main window 'win' if available, otherwise fallback to focused window
      // Passing undefined/null as first arg is valid for non-modal dialogs in Electron,
      // but providing the window makes it modal and attached.
      const parentWindow = win || BrowserWindow.getFocusedWindow()

      // Ensure we don't pass null if types are strict, although Electron handles undefined.
      // If parentWindow is null, showOpenDialog will treat it as no parent.
      const result = await dialog.showOpenDialog(parentWindow as BrowserWindow, {
        properties,
        filters: options?.filters,
        defaultPath: options?.defaultPath,
        title: options?.title,
      })

      if (result.canceled) return null
      return options?.multiple ? result.filePaths : result.filePaths[0]
    } catch (error) {
      log('error', 'dialog', '打开文件对话框失败', { error: error instanceof Error ? error.message : String(error) })
      throw error
    }
  })

  ipcMain.handle('dialog:save', async (_, options) => {
    try {
      const parentWindow = win || BrowserWindow.getFocusedWindow() || undefined
      const result = await dialog.showSaveDialog(parentWindow as BrowserWindow, {
        filters: options?.filters,
        defaultPath: options?.defaultPath,
        title: options?.title
      })

      if (result.canceled) return null
      return result.filePath
    } catch (error) {
      log('error', 'dialog', '保存文件对话框失败', { error: error instanceof Error ? error.message : String(error) })
      throw error
    }
  })

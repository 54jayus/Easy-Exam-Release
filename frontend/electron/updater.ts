import { app, type BrowserWindow, shell } from 'electron'
import fs from 'node:fs'
import path from 'node:path'
import { spawn } from 'node:child_process'

const MOCK_UPDATE_ENABLED = ['1', 'true', 'yes', 'on'].includes(
  String(process.env.EASY_EXAM_MOCK_UPDATE || '').trim().toLowerCase()
)
const MOCK_UPDATE_VERSION = String(process.env.EASY_EXAM_MOCK_UPDATE_VERSION || '3.5.0001').trim() || '3.5.0001'
const MOCK_UPDATE_RELEASE_DATE =
  String(process.env.EASY_EXAM_MOCK_UPDATE_DATE || '2026-06-01').trim() || '2026-06-01'
const MOCK_UPDATE_NOTES = [
  '新增更新弹窗交互优化，支持更清晰的状态提示与历史版本查看。',
  '改进下载进度展示与完成反馈，便于演示完整更新流程。',
  '优化安装前确认文案与异常提示，让更新操作更易理解。',
]
const MOCK_UPDATE_URL = `mock://easy-exam/EasyExam-Setup-${MOCK_UPDATE_VERSION}.exe`
const MOCK_DOWNLOAD_PROGRESS_STEP_COUNT = 60
const MOCK_DOWNLOAD_TOTAL_DURATION_MS = 60 * 1000

import { compareVersions, buildMockDownloadProgressSteps } from '../src/lib/versionUtils'

const UPDATE_FEED_URLS = [
  'https://54jayus.github.io/Easy-Exam-Release/update/win/latest.json',
  'https://raw.githubusercontent.com/54jayus/Easy-Exam-Release/main/update/win/latest.json',
] as const

const HISTORY_FEED_URLS = [
  'https://54jayus.github.io/Easy-Exam-Release/update/win/history.json',
  'https://raw.githubusercontent.com/54jayus/Easy-Exam-Release/main/update/win/history.json',
] as const

export type UpdateCheckReason = 'manual' | 'startup'

export type UpdateManifest = {
  enabled: boolean
  version: string
  releaseDate: string
  notes: string[]
  mandatory: boolean
  url: string
  sha256?: string
  size?: number
}

export type UpdateCheckResult = {
  currentVersion: string
  latestVersion: string | null
  hasUpdate: boolean
  enabled: boolean
  releaseDate: string | null
  notes: string[]
  mandatory: boolean
  url: string | null
  downloadedFilePath: string | null
  errorMessage?: string | null
}

export type UpdateHistoryEntry = {
  version: string
  title: string
  releaseDate: string
  notes: string[]
  url: string
  releasePageUrl?: string
  sha256?: string
  size?: number
}

export type DownloadPreparation = {
  version: string
  releaseDate?: string | null
  notes?: string[]
  mandatory?: boolean
  url: string
}

type UpdateProgressPayload = {
  version: string
  receivedBytes: number
  totalBytes: number | null
  percent: number | null
}

type UpdateDownloadedPayload = {
  version: string
  filePath: string
}

type UpdaterOptions = {
  getWindow: () => BrowserWindow | null
  log: (level: 'debug' | 'info' | 'warn' | 'error', scope: string, message: string, data?: unknown) => void
  prepareForInstall: () => Promise<void> | void
}


function normalizeManifest(input: any): UpdateManifest {
  return {
    enabled: input?.enabled === true,
    version: typeof input?.version === 'string' ? input.version.trim() : '',
    releaseDate: typeof input?.releaseDate === 'string' ? input.releaseDate.trim() : '',
    notes: Array.isArray(input?.notes)
      ? input.notes.map((item: unknown) => String(item ?? '').trim()).filter(Boolean)
      : [],
    mandatory: input?.mandatory === true,
    url: typeof input?.url === 'string' ? input.url.trim() : '',
    sha256: typeof input?.sha256 === 'string' ? input.sha256.trim() : undefined,
    size: typeof input?.size === 'number' && Number.isFinite(input.size) ? input.size : undefined,
  }
}

function normalizeHistoryEntry(input: any): UpdateHistoryEntry | null {
  const version = typeof input?.version === 'string' ? input.version.trim() : ''
  if (!version) return null
  return {
    version,
    title: typeof input?.title === 'string' && input.title.trim() ? input.title.trim() : `Easy Exam.v${version}`,
    releaseDate: typeof input?.releaseDate === 'string' ? input.releaseDate.trim() : '',
    notes: Array.isArray(input?.notes)
      ? input.notes.map((item: unknown) => String(item ?? '').trim()).filter(Boolean)
      : [],
    url: typeof input?.url === 'string' ? input.url.trim() : '',
    releasePageUrl:
      typeof input?.releasePageUrl === 'string' && input.releasePageUrl.trim()
        ? input.releasePageUrl.trim()
        : undefined,
    sha256: typeof input?.sha256 === 'string' && input.sha256.trim() ? input.sha256.trim() : undefined,
    size: typeof input?.size === 'number' && Number.isFinite(input.size) ? input.size : undefined,
  }
}

function sanitizeFileName(fileName: string): string {
  const cleaned = fileName.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_').trim()
  return cleaned || 'EasyExam-Setup.exe'
}

function isMockUpdateUrl(url: string): boolean {
  return String(url || '').trim().toLowerCase().startsWith('mock://')
}

function createMockManifest(): UpdateManifest {
  return {
    enabled: true,
    version: MOCK_UPDATE_VERSION,
    releaseDate: MOCK_UPDATE_RELEASE_DATE,
    notes: [...MOCK_UPDATE_NOTES],
    mandatory: false,
    url: MOCK_UPDATE_URL,
    size: 24 * 1024 * 1024,
  }
}

function createMockHistoryEntry(): UpdateHistoryEntry {
  return {
    version: MOCK_UPDATE_VERSION,
    title: `Easy Exam.v${MOCK_UPDATE_VERSION}`,
    releaseDate: MOCK_UPDATE_RELEASE_DATE,
    notes: [...MOCK_UPDATE_NOTES],
    url: MOCK_UPDATE_URL,
    releasePageUrl: 'https://example.invalid/easy-exam/mock-release',
    size: 24 * 1024 * 1024,
  }
}

export class AppUpdater {
  private latestManifest: UpdateManifest | null = null
  private downloadedFilePath: string | null = null
  private activeDownload: Promise<UpdateCheckResult> | null = null
  private abortController: AbortController | null = null
  private pausedState: {
    receivedBytes: number
    totalBytes: number | null
    tempPath: string
    targetPath: string
  } | null = null

  constructor(private readonly options: UpdaterOptions) {}

  getCurrentVersion(): string {
    return app.getVersion()
  }

  async check(reason: UpdateCheckReason = 'manual'): Promise<UpdateCheckResult> {
    this.options.log('info', 'updater', '开始检查更新', {
      reason,
      feedUrls: MOCK_UPDATE_ENABLED ? ['mock://easy-exam/update'] : UPDATE_FEED_URLS,
      mock: MOCK_UPDATE_ENABLED,
    })

    const manifest = MOCK_UPDATE_ENABLED ? createMockManifest() : await this.fetchManifest()
    this.latestManifest = manifest
    const currentVersion = this.getCurrentVersion()

    if (!manifest.enabled) {
      this.downloadedFilePath = null
      return {
        currentVersion,
        latestVersion: manifest.version || null,
        hasUpdate: false,
        enabled: false,
        releaseDate: manifest.releaseDate || null,
        notes: manifest.notes,
        mandatory: manifest.mandatory,
        url: manifest.url || null,
        downloadedFilePath: null,
      }
    }

    if (!manifest.version) {
      throw new Error('更新信息缺少版本号')
    }

    const hasUpdate = compareVersions(manifest.version, currentVersion) > 0
    const existingDownload = hasUpdate ? await this.resolveExistingDownload(manifest) : null
    this.downloadedFilePath = existingDownload

    const result = {
      currentVersion,
      latestVersion: manifest.version,
      hasUpdate,
      enabled: true,
      releaseDate: manifest.releaseDate || null,
      notes: manifest.notes,
      mandatory: manifest.mandatory,
      url: manifest.url || null,
      downloadedFilePath: existingDownload,
    }

    this.options.log('info', 'updater', '更新检查完成', result)
    return result
  }

  async getHistory(): Promise<UpdateHistoryEntry[]> {
    this.options.log('info', 'updater', '开始拉取历史更新记录', {
      feedUrls: HISTORY_FEED_URLS,
      mock: MOCK_UPDATE_ENABLED,
    })

    let releases: unknown[] = []
    if (!MOCK_UPDATE_ENABLED) {
      const payload = await this.fetchJsonWithFallback(HISTORY_FEED_URLS, '历史更新记录')
      releases = Array.isArray(payload?.releases) ? payload.releases : []
    } else {
      try {
        const payload = await this.fetchJsonWithFallback(HISTORY_FEED_URLS, '历史更新记录')
        releases = Array.isArray(payload?.releases) ? payload.releases : []
      } catch (error) {
        this.options.log('warn', 'updater', '模拟更新模式下拉取远程历史记录失败，将仅展示模拟版本', {
          message: error instanceof Error ? error.message : String(error),
        })
      }
    }

    const history = releases
      .map((entry) => normalizeHistoryEntry(entry))
      .filter((entry): entry is UpdateHistoryEntry => Boolean(entry))

    if (!MOCK_UPDATE_ENABLED) {
      return history
    }

    const mockEntry = createMockHistoryEntry()
    return [mockEntry, ...history.filter((entry) => entry.version !== mockEntry.version)]
  }

  private async fetchManifest(): Promise<UpdateManifest> {
    return normalizeManifest(await this.fetchJsonWithFallback(UPDATE_FEED_URLS, '更新信息'))
  }

  async startDownload(): Promise<UpdateCheckResult> {
    if (this.activeDownload) {
      return this.activeDownload
    }

    const task = this.downloadInternal()
    this.activeDownload = task
    try {
      return await task
    } finally {
      this.activeDownload = null
      this.abortController = null
    }
  }

  pauseDownload(): void {
    this.options.log('info', 'updater', '暂停下载')
    this.abortController?.abort()
    this.abortController = null
    this.activeDownload = null
  }

  isPaused(): boolean {
    return this.pausedState !== null
  }

  getPausedProgress(): number | null {
    if (!this.pausedState || !this.pausedState.totalBytes) return null
    return Math.round((this.pausedState.receivedBytes / this.pausedState.totalBytes) * 1000) / 10
  }

  private async resumeDownload(initial: UpdateCheckResult): Promise<UpdateCheckResult> {
    const paused = this.pausedState!
    this.pausedState = null

    const { receivedBytes, tempPath, targetPath } = paused
    const url = this.latestManifest!.url

    this.options.log('info', 'updater', '恢复下载', {
      version: this.latestManifest!.version,
      url,
      receivedBytes,
      tempPath,
    })

    this.abortController = new AbortController()
    let writer: fs.WriteStream | null = null
    try {
      const response = await fetch(url, {
        cache: 'no-store',
        signal: this.abortController.signal,
        headers: { Range: `bytes=${receivedBytes}-` },
      })

      // Server may return 206 (Partial Content) or 200 (full content, ignore Range)
      if (response.status === 416) {
        // Range not satisfiable — file is likely complete
        await fs.promises.rename(tempPath, targetPath)
        this.downloadedFilePath = targetPath
        this.emitDownloaded({ version: this.latestManifest!.version, filePath: targetPath })
        return { ...initial, downloadedFilePath: targetPath }
      }

      if (!response.ok || !response.body) {
        throw new Error(`安装包下载失败（HTTP ${response.status}）`)
      }

      const totalBytesHeader = response.headers.get('content-length')
      const contentLength = totalBytesHeader ? Number.parseInt(totalBytesHeader, 10) : NaN
      const isPartial = response.status === 206

      // Total bytes = already received + remaining from server (if partial)
      const total = isPartial
        ? (Number.isFinite(contentLength) ? receivedBytes + contentLength : null)
        : (Number.isFinite(contentLength) ? contentLength : null)

      let currentBytes = receivedBytes

      // If server returned full content (200), overwrite temp file; otherwise append
      writer = fs.createWriteStream(tempPath, { flags: isPartial ? 'a' : 'w' })
      const reader = response.body.getReader()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        if (!value) continue
        await new Promise<void>((resolve, reject) => {
          writer!.write(Buffer.from(value), (error) => {
            if (error) reject(error)
            else resolve()
          })
        })
        currentBytes += value.byteLength
        const percent = total ? Math.min(100, Math.round((currentBytes / total) * 1000) / 10) : null
        this.emitProgress({
          version: this.latestManifest!.version,
          receivedBytes: currentBytes,
          totalBytes: total,
          percent,
        })
      }

      await new Promise<void>((resolve, reject) => {
        writer!.end((error?: Error | null) => {
          if (error) reject(error)
          else resolve()
        })
      })
      writer = null

      await fs.promises.rename(tempPath, targetPath)
      this.downloadedFilePath = targetPath
      this.emitDownloaded({ version: this.latestManifest!.version, filePath: targetPath })
      this.options.log('info', 'updater', '恢复下载完成', {
        version: this.latestManifest!.version,
        targetPath,
      })

      return { ...initial, downloadedFilePath: targetPath }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        if (writer) {
          await new Promise<void>((resolve) => writer!.end(() => resolve()))
        }
        let newReceivedBytes = receivedBytes
        try {
          const stat = await fs.promises.stat(tempPath)
          newReceivedBytes = stat.size
        } catch {}
        this.pausedState = {
          receivedBytes: newReceivedBytes,
          totalBytes: total ?? null,
          tempPath,
          targetPath,
        }
        this.options.log('info', 'updater', '下载已暂停', {
          receivedBytes: newReceivedBytes,
          tempPath,
        })
        throw new Error('DOWNLOAD_PAUSED')
      }
      writer?.destroy()
      await fs.promises.rm(tempPath, { force: true }).catch(() => undefined)
      this.emitError(error)
      throw error
    }
  }

  primeManifest(input: DownloadPreparation): UpdateManifest {
    const manifest = normalizeManifest({
      enabled: true,
      version: input.version,
      releaseDate: input.releaseDate || '',
      notes: Array.isArray(input.notes) ? input.notes : [],
      mandatory: input.mandatory === true,
      url: input.url,
    })
    this.latestManifest = manifest
    return manifest
  }

  async installDownloaded(): Promise<{ launched: true; filePath: string }> {
    if (!this.downloadedFilePath || !fs.existsSync(this.downloadedFilePath)) {
      throw new Error('未找到已下载的安装包，请先下载更新')
    }

    if (this.latestManifest && isMockUpdateUrl(this.latestManifest.url)) {
      this.options.log('info', 'updater', '模拟更新模式：跳过真实安装程序启动', {
        filePath: this.downloadedFilePath,
      })
      return { launched: true, filePath: this.downloadedFilePath }
    }

    await this.options.prepareForInstall()

    try {
      const child = spawn(this.downloadedFilePath, [], {
        detached: true,
        stdio: 'ignore',
        windowsHide: false,
      })
      child.unref()
    } catch (error) {
      const fallbackError = await shell.openPath(this.downloadedFilePath)
      if (fallbackError) {
        throw new Error(`启动安装包失败：${fallbackError}`)
      }
    }

    setTimeout(() => {
      app.quit()
    }, 120)

    return { launched: true, filePath: this.downloadedFilePath }
  }

  buildCheckFailureResult(error?: unknown): UpdateCheckResult {
    const message = error instanceof Error ? error.message : error ? String(error) : null
    return {
      currentVersion: this.getCurrentVersion(),
      latestVersion: this.latestManifest?.version || null,
      hasUpdate: false,
      enabled: this.latestManifest?.enabled ?? false,
      releaseDate: this.latestManifest?.releaseDate || null,
      notes: this.latestManifest?.notes || [],
      mandatory: this.latestManifest?.mandatory ?? false,
      url: this.latestManifest?.url || null,
      downloadedFilePath: this.downloadedFilePath,
      errorMessage: message,
    }
  }

  private async downloadInternal(): Promise<UpdateCheckResult> {
    const initial = await this.ensureLatestManifest()
    if (!initial.hasUpdate || !this.latestManifest) {
      return initial
    }
    if (!this.latestManifest.url) {
      throw new Error('更新配置不完整，缺少安装包下载地址')
    }

    const existingDownload = await this.resolveExistingDownload(this.latestManifest)
    if (existingDownload) {
      this.downloadedFilePath = existingDownload
      this.pausedState = null
      this.emitDownloaded({ version: this.latestManifest.version, filePath: existingDownload })
      return {
        ...initial,
        downloadedFilePath: existingDownload,
      }
    }

    // Resume from paused state if available
    if (this.pausedState && !isMockUpdateUrl(this.latestManifest.url)) {
      return this.resumeDownload(initial)
    }
    this.pausedState = null

    if (isMockUpdateUrl(this.latestManifest.url)) {
      return this.simulateDownload(initial, this.latestManifest)
    }

    const updatesDir = this.getUpdatesDir()
    await fs.promises.mkdir(updatesDir, { recursive: true })

    const fileName = this.getDownloadFileName(this.latestManifest)
    const targetPath = path.join(updatesDir, fileName)
    const tempPath = `${targetPath}.download`

    this.options.log('info', 'updater', '开始下载更新包', {
      version: this.latestManifest.version,
      url: this.latestManifest.url,
      targetPath,
    })

    this.abortController = new AbortController()
    let writer: fs.WriteStream | null = null
    try {
      const response = await fetch(this.latestManifest.url, {
        cache: 'no-store',
        signal: this.abortController.signal,
      })
      if (!response.ok || !response.body) {
        throw new Error(`安装包下载失败（HTTP ${response.status}）`)
      }

      const totalBytesHeader = response.headers.get('content-length')
      const totalBytes = totalBytesHeader ? Number.parseInt(totalBytesHeader, 10) : NaN
      const total = Number.isFinite(totalBytes) ? totalBytes : null
      let receivedBytes = 0

      writer = fs.createWriteStream(tempPath)
      const reader = response.body.getReader()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        if (!value) continue
        await new Promise<void>((resolve, reject) => {
          writer!.write(Buffer.from(value), (error) => {
            if (error) reject(error)
            else resolve()
          })
        })
        receivedBytes += value.byteLength
        const percent = total ? Math.min(100, Math.round((receivedBytes / total) * 1000) / 10) : null
        this.emitProgress({
          version: this.latestManifest.version,
          receivedBytes,
          totalBytes: total,
          percent,
        })
      }

      await new Promise<void>((resolve, reject) => {
        writer!.end((error?: Error | null) => {
          if (error) reject(error)
          else resolve()
        })
      })
      writer = null

      await fs.promises.rename(tempPath, targetPath)
      this.downloadedFilePath = targetPath
      this.emitDownloaded({ version: this.latestManifest.version, filePath: targetPath })
      this.options.log('info', 'updater', '更新包下载完成', {
        version: this.latestManifest.version,
        targetPath,
      })

      return {
        ...initial,
        downloadedFilePath: targetPath,
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Pause: close writer gracefully to preserve partial file
        if (writer) {
          await new Promise<void>((resolve) => writer!.end(() => resolve()))
        }
        // Get the actual size of the partial file
        let receivedBytes = 0
        try {
          const stat = await fs.promises.stat(tempPath)
          receivedBytes = stat.size
        } catch {}
        const totalBytesHeader = undefined // total is known from the download
        this.pausedState = {
          receivedBytes,
          totalBytes: null, // will be resolved from manifest on resume
          tempPath,
          targetPath,
        }
        // Try to get total from manifest
        if (this.latestManifest?.size) {
          this.pausedState.totalBytes = this.latestManifest.size
        }
        this.options.log('info', 'updater', '下载已暂停', {
          receivedBytes,
          tempPath,
        })
        throw new Error('DOWNLOAD_PAUSED')
      }
      writer?.destroy()
      await fs.promises.rm(tempPath, { force: true }).catch(() => undefined)
      this.emitError(error)
      throw error
    }
  }

  private async ensureLatestManifest(): Promise<UpdateCheckResult> {
    if (!this.latestManifest) {
      return this.check('manual')
    }

    const currentVersion = this.getCurrentVersion()
    const hasUpdate =
      this.latestManifest.enabled &&
      compareVersions(this.latestManifest.version, currentVersion) > 0
    const existingDownload = hasUpdate ? await this.resolveExistingDownload(this.latestManifest) : null
    this.downloadedFilePath = existingDownload

    return {
      currentVersion,
      latestVersion: this.latestManifest.version || null,
      hasUpdate,
      enabled: this.latestManifest.enabled,
      releaseDate: this.latestManifest.releaseDate || null,
      notes: this.latestManifest.notes,
      mandatory: this.latestManifest.mandatory,
      url: this.latestManifest.url || null,
      downloadedFilePath: existingDownload,
    }
  }

  private async resolveExistingDownload(manifest: UpdateManifest): Promise<string | null> {
    if (!manifest.url) return null
    const targetPath = path.join(this.getUpdatesDir(), this.getDownloadFileName(manifest))
    try {
      await fs.promises.access(targetPath, fs.constants.F_OK)
      return targetPath
    } catch {
      return null
    }
  }

  private getUpdatesDir(): string {
    return path.join(app.getPath('userData'), 'updates')
  }

  private getDownloadFileName(manifest: UpdateManifest): string {
    try {
      const url = new URL(manifest.url)
      const pathname = url.pathname.split('/').pop() || ''
      return sanitizeFileName(pathname)
    } catch {
      return sanitizeFileName(`EasyExam-Setup-${manifest.version}.exe`)
    }
  }

  private async simulateDownload(
    initial: UpdateCheckResult,
    manifest: UpdateManifest
  ): Promise<UpdateCheckResult> {
    const updatesDir = this.getUpdatesDir()
    await fs.promises.mkdir(updatesDir, { recursive: true })

    const targetPath = path.join(updatesDir, this.getDownloadFileName(manifest))
    const tempPath = `${targetPath}.download`
    const totalBytes = manifest.size ?? 24 * 1024 * 1024

    // Support resume: check for existing partial file
    let startBytes = 0
    try {
      const stat = await fs.promises.stat(tempPath)
      startBytes = stat.size
    } catch {}

    const startPercent = totalBytes > 0 ? (startBytes / totalBytes) * 100 : 0
    const progressSteps = buildMockDownloadProgressSteps(MOCK_DOWNLOAD_PROGRESS_STEP_COUNT)
    const stepDelay = Math.max(
      1,
      Math.round(MOCK_DOWNLOAD_TOTAL_DURATION_MS / progressSteps.length)
    )

    this.abortController = new AbortController()

    this.options.log('info', 'updater', '模拟更新模式：开始生成下载进度', {
      version: manifest.version,
      targetPath,
      startBytes,
    })

    try {
      for (const percent of progressSteps) {
        if (percent < startPercent) continue
        const receivedBytes = Math.round((totalBytes * percent) / 100)
        this.emitProgress({
          version: manifest.version,
          receivedBytes,
          totalBytes,
          percent,
        })
        await new Promise((resolve, reject) => {
          const timer = setTimeout(resolve, stepDelay)
          this.abortController!.signal.addEventListener('abort', () => {
            clearTimeout(timer)
            reject(new DOMException('Aborted', 'AbortError'))
          }, { once: true })
        })
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Write partial mock file for resume
        await fs.promises.writeFile(tempPath, `mock-partial:${manifest.version}`, 'utf8')
        this.pausedState = {
          receivedBytes: startBytes,
          totalBytes,
          tempPath,
          targetPath,
        }
        this.options.log('info', 'updater', '模拟下载已暂停')
        throw new Error('DOWNLOAD_PAUSED')
      }
      throw error
    }

    await fs.promises.writeFile(
      targetPath,
      [
        'This is a mock update package for Easy Exam UI preview.',
        `version=${manifest.version}`,
        `releaseDate=${manifest.releaseDate}`,
      ].join('\n'),
      'utf8'
    )

    // Clean up temp file on completion
    await fs.promises.rm(tempPath, { force: true }).catch(() => undefined)

    this.downloadedFilePath = targetPath
    this.emitDownloaded({ version: manifest.version, filePath: targetPath })
    this.options.log('info', 'updater', '模拟更新模式：下载流程完成', {
      version: manifest.version,
      targetPath,
    })

    return {
      ...initial,
      downloadedFilePath: targetPath,
    }
  }

  private emitProgress(payload: UpdateProgressPayload) {
    this.options.getWindow()?.webContents.send('update-progress', payload)
  }

  private emitDownloaded(payload: UpdateDownloadedPayload) {
    this.options.getWindow()?.webContents.send('update-downloaded', payload)
  }

  private emitError(error: unknown) {
    const message = error instanceof Error ? error.message : String(error)
    this.options.log('error', 'updater', '更新流程失败', { message })
    this.options.getWindow()?.webContents.send('update-error', { message })
  }

  private async fetchJsonWithFallback(feedUrls: readonly string[], label: string): Promise<any> {
    let lastError: unknown = null

    for (const feedUrl of feedUrls) {
      try {
        const response = await fetch(feedUrl, {
          cache: 'no-store',
          headers: { Accept: 'application/json' },
        })
        if (!response.ok) {
          throw new Error(`${label}请求失败（HTTP ${response.status}）`)
        }
        this.options.log('info', 'updater', `${label}请求成功`, { feedUrl })
        return await response.json()
      } catch (error) {
        lastError = error
        this.options.log('warn', 'updater', `${label}请求失败，准备尝试下一个地址`, {
          feedUrl,
          message: error instanceof Error ? error.message : String(error),
        })
      }
    }

    throw lastError instanceof Error ? lastError : new Error(`${label}请求失败`)
  }
}

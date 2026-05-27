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

function compareVersions(a: string, b: string): number {
  const left = String(a || '')
    .split('.')
    .map((part) => Number.parseInt(part, 10) || 0)
  const right = String(b || '')
    .split('.')
    .map((part) => Number.parseInt(part, 10) || 0)
  const maxLength = Math.max(left.length, right.length)
  for (let index = 0; index < maxLength; index += 1) {
    const leftValue = left[index] ?? 0
    const rightValue = right[index] ?? 0
    if (leftValue > rightValue) return 1
    if (leftValue < rightValue) return -1
  }
  return 0
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
    }
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
      this.emitDownloaded({ version: this.latestManifest.version, filePath: existingDownload })
      return {
        ...initial,
        downloadedFilePath: existingDownload,
      }
    }

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

    let writer: fs.WriteStream | null = null
    try {
      const response = await fetch(this.latestManifest.url, { cache: 'no-store' })
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
    const checkpoints = [8, 21, 39, 56, 74, 91, 100]
    const totalBytes = manifest.size ?? 24 * 1024 * 1024

    this.options.log('info', 'updater', '模拟更新模式：开始生成下载进度', {
      version: manifest.version,
      targetPath,
    })

    for (const percent of checkpoints) {
      const receivedBytes = Math.round((totalBytes * percent) / 100)
      this.emitProgress({
        version: manifest.version,
        receivedBytes,
        totalBytes,
        percent,
      })
      await new Promise((resolve) => setTimeout(resolve, 220))
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

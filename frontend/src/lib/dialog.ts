import { isElectron } from './env'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createLogger } from './logger'

const logger = createLogger('dialog')

export interface DialogFilter {
  name: string
  extensions: string[]
}

export interface OpenDialogOptions {
  title?: string
  defaultPath?: string
  filters?: DialogFilter[]
  multiple?: boolean
  directory?: boolean
  recursive?: boolean
}

export interface SaveDialogOptions {
  title?: string
  defaultPath?: string
  filters?: DialogFilter[]
}

export async function open(options: OpenDialogOptions = {}): Promise<null | string | string[]> {
  try {
    if (isElectron()) {
      const result = await (window as any).electron.ipcRenderer.invoke('dialog:open', options)
      return result
    } else {
      logger.warn('无法打开系统对话框：当前不是 Electron 环境', { action: 'dialog.open' })
      alert('环境检测失败：不是 Electron 环境')
    }
  } catch (err) {
    logger.error('打开文件对话框失败', err)
    alert(`打开文件失败：${err}`)
  }
  return null
}

export async function save(options: SaveDialogOptions = {}): Promise<null | string> {
  try {
    if (isElectron()) {
      const result = await (window as any).electron.ipcRenderer.invoke('dialog:save', options)
      return result
    } else {
      logger.warn('无法打开系统对话框：当前不是 Electron 环境', { action: 'dialog.save' })
      alert('环境检测失败：不是 Electron 环境')
    }
  } catch (err) {
    logger.error('保存文件对话框失败', err)
    alert(`保存文件失败：${err}`)
  }
  return null
}

export async function openPath(p: string): Promise<void> {
  if (!p) return
  try {
    if (isElectron()) {
      await (window as any).electron.ipcRenderer.invoke('open_path', p)
    }
  } catch {}
}

export async function confirmOpenInFolder(filePath: string, options?: { title?: string; message?: string }): Promise<void> {
  if (!filePath) return
  const title = options?.title ?? '导出成功'
  const message = options?.message ?? '是否打开文件所在文件夹？'
  try {
    await ElMessageBox.confirm(message, title, {
      type: 'success',
      confirmButtonText: '打开文件夹',
      cancelButtonText: '不打开',
      closeOnClickModal: false,
    })
  } catch {
    return
  }
  await openPath(filePath)
}

export type SaveAndRunOptions<T> = {
  dialog: SaveDialogOptions
  run: (filePath: string) => Promise<T>
  isCancelled?: (result: T) => boolean
  successText?: string
  errorText?: string
  revealPath?: (result: T, selectedPath: string) => string | null | undefined
  openFolderPrompt?: boolean
  openFolderTitle?: string
  openFolderMessage?: string
  onLog?: (msg: string) => void
}

export async function saveAndRun<T>(options: SaveAndRunOptions<T>): Promise<{ selectedPath: string; result: T } | null> {
  const selectedPath = await save(options.dialog)
  if (!selectedPath) {
    options.onLog?.('已取消保存')
    return null
  }

  options.onLog?.(`已选择保存路径：${selectedPath}`)

  try {
    const result = await options.run(selectedPath)
    if (options.isCancelled?.(result)) {
      options.onLog?.('操作已取消')
      return null
    }
    const err = (result as any)?.error
    if (typeof err === 'string' && err.trim()) {
      ElMessage.error(err)
      options.onLog?.(`保存失败：${err}`)
      return { selectedPath, result }
    }

    if (options.successText) ElMessage.success(options.successText)
    options.onLog?.(`保存成功：${selectedPath}`)

    const shouldPrompt = options.openFolderPrompt !== false
    if (shouldPrompt) {
      const reveal = options.revealPath?.(result, selectedPath) ?? selectedPath
      if (reveal) {
        await confirmOpenInFolder(reveal, { title: options.openFolderTitle, message: options.openFolderMessage })
      }
    }

    return { selectedPath, result }
  } catch (e: any) {
    const text = e instanceof Error ? e.message : String(e)
    const msg = options.errorText ? `${options.errorText}：${text}` : `保存失败：${text}`
    ElMessage.error(msg)
    options.onLog?.(`保存异常：${text}`)
    return null
  }
}

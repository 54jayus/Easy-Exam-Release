import { computed, reactive, type Ref } from 'vue'
import { open } from '@/lib/dialog'
import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionError, formatActionWarning } from '@/lib/uiFeedback'

type StorageLike = {
  getJsonCache<T>(key: string, fallback: T): T
  setJsonCache(key: string, value: unknown): void
  removeCache(key: string): void
}

type SaveConfigPayload = {
  config: unknown
  commonConfig: unknown
  totalCount: number
  sourceType: string
}

type UsePrintingFileSourceOptions = {
  storage: StorageLike
  activeTab: Ref<string>
  sourceType: Ref<string>
  dataPath: Ref<string>
  headers: Ref<string[]>
  previewData: Ref<any[]>
  previewTotal: Ref<number>
  showMappingDialog: Ref<boolean>
  getSaveConfigPayload: () => SaveConfigPayload
}

type FilePreviewCache = {
  dataPath: string
  headers: string[]
  mapping: Record<string, string>
  data: any[]
  total: number
}

const FILE_PREVIEW_CACHE_ROW_LIMIT = 20

function emptyFilePreviewCache(): FilePreviewCache {
  return {
    dataPath: '',
    headers: [],
    mapping: {},
    data: [],
    total: 0,
  }
}

export function usePrintingFileSource({
  storage,
  activeTab,
  sourceType,
  dataPath,
  headers,
  previewData,
  previewTotal,
  showMappingDialog,
  getSaveConfigPayload,
}: UsePrintingFileSourceOptions) {
  const feedback = createUiFeedback()
  const mapping = reactive<Record<string, string>>({})
  const requiredFields = {
    '考场号': { label: '考场号', required: true },
    '考场': { label: '考场名称', required: true },
    '座位号': { label: '座位号', required: true },
    '考生姓名': { label: '姓名', required: true },
    '考生考号': { label: '考号', required: true },
    '班级': { label: '班级', required: true },
    '学号': { label: '学号', required: true },
    '首选': { label: '首选', required: false },
    '再选1': { label: '再选1', required: false },
    '再选2': { label: '再选2', required: false },
  } as const

  const filePreviewCache = reactive<FilePreviewCache>(
    storage.getJsonCache<FilePreviewCache>('filePreview_v1', emptyFilePreviewCache())
  )

  const dataFileName = computed(() => dataPath.value.split(/[\\/]/).pop())

  function slicePreviewDataForCache(data: unknown): any[] {
    if (!Array.isArray(data)) return []
    return data.slice(0, FILE_PREVIEW_CACHE_ROW_LIMIT)
  }

  function persistFilePreviewCache() {
    storage.setJsonCache('filePreview_v1', {
      dataPath: filePreviewCache.dataPath,
      headers: filePreviewCache.headers.slice(),
      mapping: { ...filePreviewCache.mapping },
      data: slicePreviewDataForCache(filePreviewCache.data),
      total: filePreviewCache.total,
    })
  }

  function clearMapping() {
    for (const key of Object.keys(mapping)) delete mapping[key]
  }

  function snapshotMapping(): Record<string, string> {
    const snapshot: Record<string, string> = {}
    for (const key of Object.keys(mapping)) {
      const value = mapping[key]
      if (typeof value === 'string' && value.trim()) snapshot[key] = value
    }
    return snapshot
  }

  function applyMappingSnapshot(snapshot: Record<string, string>) {
    clearMapping()
    for (const [key, value] of Object.entries(snapshot || {})) {
      const normalizedKey = key === '选科1' ? '再选1' : key === '选科2' ? '再选2' : key
      mapping[normalizedKey] = String(value ?? '')
    }
  }

  function cacheCurrentFileState() {
    filePreviewCache.dataPath = dataPath.value
    filePreviewCache.headers = headers.value.slice()
    filePreviewCache.mapping = snapshotMapping()
    filePreviewCache.data = slicePreviewDataForCache(previewData.value)
    filePreviewCache.total = previewTotal.value
    persistFilePreviewCache()
  }

  async function syncClearedFileSelectionToBackend() {
    try {
      const payload = getSaveConfigPayload()
      await pythonBackend.request('printing.saveConfig', {
        config: payload.config,
        commonConfig: payload.commonConfig,
        totalCount: payload.totalCount,
        sourceType: payload.sourceType,
        dataPath: '',
        headers: [],
        mapping: {},
        data: [],
        previewTotal: 0,
      })
    } catch (error) {
      console.error('Failed to clear backend printing file selection:', error)
    }
  }

  function resetFileState() {
    dataPath.value = ''
    headers.value = []
    previewData.value = []
    previewTotal.value = 0
    showMappingDialog.value = false
    clearMapping()
    Object.assign(filePreviewCache, emptyFilePreviewCache())
    storage.removeCache('filePreview_v1')
  }

  async function clearSelectedFile() {
    resetFileState()
    await syncClearedFileSelectionToBackend()
  }

  function autoMapFields() {
    clearMapping()
    const legacyAliases: Record<string, string[]> = {
      '再选1': ['选科1'],
      '再选2': ['选科2'],
    }
    for (const key in requiredFields) {
      if (headers.value.includes(key)) {
        mapping[key] = key
      } else {
        const aliases = legacyAliases[key] || []
        const match = headers.value.find(
          (header) => aliases.includes(header) || header.includes(key) || key.includes(header)
        )
        if (match) mapping[key] = match
      }
    }
  }

  function isMappingComplete() {
    for (const [key, field] of Object.entries(requiredFields)) {
      if (field.required && !mapping[key]) return false
    }
    return true
  }

  async function loadPreview() {
    if (!dataPath.value) return
    try {
      const response = await pythonBackend.request<any>('printing.previewData', {
        path: dataPath.value,
        mapping,
        type: activeTab.value,
      })
      if (response.data) {
        previewData.value = response.data
        previewTotal.value = response.total
        if (sourceType.value === 'file') cacheCurrentFileState()
      } else if (response.error) {
        feedback.error(formatActionError('加载打印预览', response.error))
      }
    } catch (error) {
      feedback.error(formatActionError('加载打印预览', error))
    }
  }

  async function handleSelectFile() {
    const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }] })
    if (!path) return

    sourceType.value = 'file'
    dataPath.value = String(path)

    if (activeTab.value === 'exam_bag_label') {
      headers.value = []
      clearMapping()
      showMappingDialog.value = false
      try {
        const response = await pythonBackend.request<any>('printing.previewData', {
          path,
          mapping: {},
          type: activeTab.value,
        })
        if (response.data) {
          previewData.value = response.data
          previewTotal.value = response.total
        } else if (response.error) {
          feedback.error(formatActionError('加载打印预览', response.error))
        }
      } catch (error) {
        feedback.error(formatActionError('加载打印预览', error))
      }
      return
    }

    try {
      const response = await pythonBackend.request<any>('printing.readHeaders', { path })
      if (response.headers) {
        headers.value = response.headers
        if (filePreviewCache.dataPath === String(path) && Object.keys(filePreviewCache.mapping).length) {
          applyMappingSnapshot(filePreviewCache.mapping)
          if (isMappingComplete()) {
            showMappingDialog.value = false
            await loadPreview()
          } else {
            showMappingDialog.value = true
          }
        } else {
          autoMapFields()
          showMappingDialog.value = true
        }
      } else if (response.error) {
        feedback.error(formatActionError('读取打印数据文件', response.error))
      }
    } catch (error) {
      feedback.error(formatActionError('读取打印数据文件', error))
    }
  }

  function openMappingDialog() {
    if (!dataPath.value) return
    showMappingDialog.value = true
  }

  async function handleConfirmMapping() {
    for (const [key, field] of Object.entries(requiredFields)) {
      if (field.required && !mapping[key]) {
        feedback.warning(formatActionWarning('字段映射', `请映射必填字段：${field.label}`))
        return
      }
    }

    showMappingDialog.value = false
    sourceType.value = 'file'
    await loadPreview()
  }

  function restoreFileStateFromPrintingState(state: any) {
    if (!(state && state.sourceType === 'file' && state.dataPath)) return false

    sourceType.value = 'file'
    dataPath.value = state.dataPath
    headers.value = state.headers || []
    previewData.value = state.data || []
    previewTotal.value = state.total || 0

    if (state.mapping) {
      applyMappingSnapshot(state.mapping)
    }

    Object.assign(filePreviewCache, {
      dataPath: state.dataPath,
      headers: state.headers || [],
      mapping: state.mapping || {},
      data: slicePreviewDataForCache(state.data || []),
      total: state.total || 0,
    })
    persistFilePreviewCache()
    return true
  }

  function applyCachedFileState() {
    if (filePreviewCache.dataPath) {
      dataPath.value = filePreviewCache.dataPath
      headers.value = filePreviewCache.headers.slice()
      applyMappingSnapshot(filePreviewCache.mapping)
      previewData.value = filePreviewCache.data.slice()
      previewTotal.value = filePreviewCache.total
      return
    }

    previewData.value = []
    previewTotal.value = 0
  }

  return {
    dataFileName,
    mapping,
    requiredFields,
    filePreviewCache,
    clearSelectedFile,
    resetFileState,
    cacheCurrentFileState,
    applyCachedFileState,
    restoreFileStateFromPrintingState,
    openMappingDialog,
    autoMapFields,
    handleConfirmMapping,
    isMappingComplete,
    loadPreview,
    handleSelectFile,
  }
}

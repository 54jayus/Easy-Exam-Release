import { ref, type ComputedRef, type Ref } from 'vue'
import { saveAndRun } from '@/lib/dialog'
import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionSuccess, formatActionWarning } from '@/lib/uiFeedback'
import type { SubjectRow } from './usePrintingSubjects'

type TabOption = {
  id: string
  name: string
}

type DeskEffectiveLayout = {
  rows: number
  cols: number
}

type UsePrintingGenerateOptions = {
  activeTab: Ref<string>
  sourceType: Ref<string>
  dataPath: Ref<string>
  previewData: Ref<any[]>
  showMappingDialog: Ref<boolean>
  mapping: Record<string, string>
  isMappingComplete: () => boolean
  commonConfig: {
    exportXlsx: boolean
    exportPdf: boolean
  }
  config: any
  totalCount: Ref<number>
  isGaokaoMode: ComputedRef<boolean>
  subjectRows: Ref<SubjectRow[]>
  deskEffectiveLayout: ComputedRef<DeskEffectiveLayout>
  tabs: TabOption[]
}

const GAOKAO_SUBJECTS = ['语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物'] as const

export function usePrintingGenerate({
  activeTab,
  sourceType,
  dataPath,
  previewData,
  showMappingDialog,
  mapping,
  isMappingComplete,
  commonConfig,
  config,
  totalCount,
  isGaokaoMode,
  subjectRows,
  deskEffectiveLayout,
  tabs,
}: UsePrintingGenerateOptions) {
  const generating = ref(false)
  const feedback = createUiFeedback()

  function getEditableSubjectNames() {
    return subjectRows.value.map((row) => String(row.name ?? '').trim()).filter(Boolean)
  }

  function getSubjectNames() {
    return isGaokaoMode.value ? [...GAOKAO_SUBJECTS] : subjectRows.value.map((row) => row.name)
  }

  function getSubjectTimes() {
    return isGaokaoMode.value ? ['', '', '', '', '', '', '', ''] : subjectRows.value.map((row) => row.time)
  }

  function buildSpecificConfig() {
    if (activeTab.value === 'corner') {
      return {
        title: config.corner.title,
        subjects: getSubjectNames(),
      }
    }

    if (activeTab.value === 'desk') {
      return {
        ...config.desk,
        layoutRows: deskEffectiveLayout.value.rows,
        layoutCols: deskEffectiveLayout.value.cols,
      }
    }

    if (activeTab.value === 'ticket') {
      return {
        title: config.ticket.title,
        subjects: getSubjectNames(),
        subjectTimes: getSubjectTimes(),
      }
    }

    if (activeTab.value === 'table') return config.table
    if (activeTab.value === 'roll_call') return config.rollCall
    if (activeTab.value === 'exam_bag_label') {
      return {
        ...config.examBag,
        subjects: getEditableSubjectNames(),
      }
    }
    return {}
  }

  function buildDefaultFileName() {
    let tabName = tabs.find((tab) => tab.id === activeTab.value)?.name || '生成结果'
    if (activeTab.value === 'table') {
      const mode = String(config.table.groupMode || 'class')
      tabName = mode === 'examroom' ? '考生信息表（考场）' : '考生信息表（班级）'
    }

    const bothFormats = Boolean(commonConfig.exportXlsx) && Boolean(commonConfig.exportPdf)
    const defaultExt = bothFormats ? '' : (commonConfig.exportPdf ? 'pdf' : 'xlsx')
    return {
      bothFormats,
      defaultFileName: defaultExt ? `${tabName}.${defaultExt}` : tabName,
    }
  }

  async function confirmOptionalSubjectColumns() {
    if (activeTab.value !== 'table') return true
    if (sourceType.value !== 'file') return true
    if (!config.table.includeSubjectFields) return true

    const missing = ['首选', '选科1', '选科2'].filter((key) => !mapping[key])
    if (!missing.length) return true

    try {
      await feedback.confirmWarning({
        message: `已勾选“包含选科列”，但未映射字段：${missing.join('、')}。\n继续生成将导致这些列为空。\n是否继续？`,
        title: '字段映射提示',
        confirmButtonText: '继续生成',
        cancelButtonText: '取消',
        closeOnClickModal: false,
      })
      return true
    } catch {
      return false
    }
  }

  async function runGenerate(outputPath: string) {
    generating.value = true
    try {
      const configPayload = {
        ...commonConfig,
        ...buildSpecificConfig(),
        totalCount: totalCount.value,
        numTemplates: totalCount.value,
      }

      const confirmFlags: Record<string, boolean> = {}
      let result: any = await pythonBackend.request('printing.generate', {
        type: activeTab.value,
        sourceType: sourceType.value,
        dataPath: dataPath.value,
        mapping,
        outputPath,
        config: configPayload,
        confirmFlags,
      })

      while (true) {
        if (result?.error) throw String(result.error)
        if (!result?.confirm) break

        const confirm = result.confirm
        try {
          await feedback.confirm({
            message: String(confirm.message || ''),
            title: String(confirm.title || '提示'),
            type: confirm.level === 'warning' || confirm.level === 'question' ? 'warning' : 'info',
            confirmButtonText: '继续生成',
            cancelButtonText: '取消',
            closeOnClickModal: false,
          })
        } catch {
          return { cancelled: true }
        }

        if (confirm.code === 'deskSort' || confirm.title === '排序警告') confirmFlags.deskSort = true
        if (confirm.code === 'deskOverflow' || confirm.title === '人数超限提示') confirmFlags.deskOverflow = true

        result = await pythonBackend.request('printing.generate', {
          type: activeTab.value,
          sourceType: sourceType.value,
          dataPath: dataPath.value,
          mapping,
          outputPath,
          config: configPayload,
          confirmFlags,
        })
      }

      const paths = result?.paths
      if (Array.isArray(paths) && paths.length > 1) {
        const fileNames = paths.map((path: string) => path.split(/[\\/]/).pop()).join('、')
        feedback.success(formatActionSuccess('生成打印文件', fileNames))
      } else {
        feedback.success(formatActionSuccess('生成打印文件'))
      }

      return result
    } finally {
      generating.value = false
    }
  }

  async function handleGenerate() {
    if (sourceType.value === 'file' && (!dataPath.value || previewData.value.length === 0)) {
      return feedback.warning(formatActionWarning('生成打印文件', '请先加载数据'))
    }
    if (sourceType.value === 'schedule' && previewData.value.length === 0) {
      return feedback.warning(formatActionWarning('生成打印文件', '请先加载考场编排数据'))
    }
    if (activeTab.value !== 'exam_bag_label' && sourceType.value === 'file' && !isMappingComplete()) {
      showMappingDialog.value = true
      return feedback.warning(formatActionWarning('生成打印文件', '请先完成字段映射'))
    }
    if (!(await confirmOptionalSubjectColumns())) return

    const exportXlsx = Boolean(commonConfig.exportXlsx)
    const exportPdf = Boolean(commonConfig.exportPdf)
    if (!exportXlsx && !exportPdf) {
      return feedback.warning(formatActionWarning('生成打印文件', '请至少选择一种输出格式（Excel 或 PDF）'))
    }

    const { bothFormats, defaultFileName } = buildDefaultFileName()

    await saveAndRun({
      dialog: {
        defaultPath: defaultFileName,
        filters: bothFormats
          ? [{ name: '所有文件', extensions: ['*'] }]
          : [
              ...(exportXlsx ? [{ name: 'Excel', extensions: ['xlsx'] }] : []),
              ...(exportPdf ? [{ name: 'PDF', extensions: ['pdf'] }] : []),
            ],
      },
      run: runGenerate,
      errorText: '生成失败',
      openFolderTitle: '生成成功',
      isCancelled: (result) => Boolean((result as any)?.cancelled),
      revealPath: (result, selectedPath) => {
        const paths = (result as any)?.paths
        if (Array.isArray(paths) && paths.length) return String(paths[0])
        return selectedPath
      },
    })
  }

  return {
    generating,
    handleGenerate,
  }
}

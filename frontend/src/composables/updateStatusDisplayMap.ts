import type { ComputedRef, Ref } from 'vue'
import { computed } from 'vue'
import type { UpdateStatus } from '@/types/appUpdate'

export type UpdateMode = 'forceActive' | 'forcePending' | 'normal'

export type StatusDisplayEntry = {
  tooltip: string
  title: string
  description: string
  chipText: string
  chipClass: string
  panelClass: string
  titleClass: string
}

export type StatusDisplayMap = Record<UpdateMode, Record<UpdateStatus, StatusDisplayEntry>>

const STATUS_DISPLAY_MAP: StatusDisplayMap = {
  forceActive: {
    idle: {
      tooltip: '检测到必须更新版本',
      title: '请先完成版本升级',
      description: '当前版本需要先升级后才能继续使用。',
      chipText: '已锁定',
      chipClass: 'bg-slate-100 text-slate-500',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    checking: {
      tooltip: '检测到必须更新版本',
      title: '正在验证必须安装的版本',
      description: '正在连接更新源并确认必须安装的目标版本。',
      chipText: '校验中',
      chipClass: 'bg-orange-100 text-orange-700',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    available: {
      tooltip: '检测到必须更新版本',
      title: '检测到必须更新版本',
      description: '检测到新版本后，必须完成下载和安装，软件才可继续使用。',
      chipText: '必须更新',
      chipClass: 'bg-rose-100 text-rose-700',
      panelClass: 'border-rose-100 bg-rose-50/70',
      titleClass: 'text-rose-700',
    },
    downloading: {
      tooltip: '正在下载必须安装的新版本',
      title: '必须更新包下载中',
      description: '安装包会下载到本机更新缓存目录，完成后可直接启动安装。',
      chipText: '强更下载中',
      chipClass: 'bg-rose-100 text-rose-700',
      panelClass: 'border-rose-100 bg-rose-50/70',
      titleClass: 'text-rose-700',
    },
    paused: {
      tooltip: '检测到必须更新版本',
      title: '请先完成版本升级',
      description: '下载已暂停，可稍后继续下载或直接安装已有进度。',
      chipText: '已锁定',
      chipClass: 'bg-slate-100 text-slate-500',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    downloaded: {
      tooltip: '必须安装新版本后才能继续使用',
      title: '安装包已准备完成',
      description: '安装新版本后，当前的强制更新限制会自动解除。',
      chipText: '等待安装',
      chipClass: 'bg-rose-100 text-rose-700',
      panelClass: 'border-rose-100 bg-rose-50/70',
      titleClass: 'text-rose-700',
    },
    up_to_date: {
      tooltip: '检测到必须更新版本',
      title: '请先完成版本升级',
      description: '当前版本需要先升级后才能继续使用。',
      chipText: '已锁定',
      chipClass: 'bg-slate-100 text-slate-500',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    error: {
      tooltip: '强制更新检查失败，点击重试',
      title: '强制更新暂时不可用',
      description: '请重新检查更新；如果问题持续存在，请确认网络或更新源配置。',
      chipText: '需重试',
      chipClass: 'bg-rose-50 text-rose-600',
      panelClass: 'border-amber-100 bg-amber-50/80',
      titleClass: 'text-amber-700',
    },
  },
  forcePending: {
    idle: {
      tooltip: '已检测到必须更新版本，将于下次启动生效',
      title: '已记录必须更新要求',
      description: '已检测到必须更新版本，下次启动后会限制进入软件。',
      chipText: '已记录',
      chipClass: 'bg-slate-100 text-slate-500',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    checking: {
      tooltip: '已检测到必须更新版本，将于下次启动生效',
      title: '正在确认必须安装的版本',
      description: '正在连接更新源并确认必须安装的目标版本。',
      chipText: '校验中',
      chipClass: 'bg-orange-100 text-orange-700',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    available: {
      tooltip: '已检测到必须更新版本，将于下次启动生效',
      title: '检测到必须更新版本（下次启动生效）',
      description: '当前会话仍可继续使用；重启软件后需要先完成升级。',
      chipText: '下次强更',
      chipClass: 'bg-rose-100 text-rose-700',
      panelClass: 'border-rose-100 bg-rose-50/70',
      titleClass: 'text-rose-700',
    },
    downloading: {
      tooltip: '正在下载必须更新包，下次启动会生效',
      title: '必须更新包下载中',
      description: '更新包会下载到本机更新缓存目录，完成后下次启动可直接安装。',
      chipText: '准备升级',
      chipClass: 'bg-rose-100 text-rose-700',
      panelClass: 'border-rose-100 bg-rose-50/70',
      titleClass: 'text-rose-700',
    },
    paused: {
      tooltip: '已检测到必须更新版本，将于下次启动生效',
      title: '已记录必须更新要求',
      description: '下载已暂停，可稍后继续；重启软件后需要先完成升级。',
      chipText: '已记录',
      chipClass: 'bg-slate-100 text-slate-500',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    downloaded: {
      tooltip: '已下载必须更新包，下次启动需先安装',
      title: '更新包已准备完成',
      description: '当前会话仍可继续使用；下次启动前请先安装新版本。',
      chipText: '待重启安装',
      chipClass: 'bg-rose-100 text-rose-700',
      panelClass: 'border-rose-100 bg-rose-50/70',
      titleClass: 'text-rose-700',
    },
    up_to_date: {
      tooltip: '已检测到必须更新版本，将于下次启动生效',
      title: '已记录必须更新要求',
      description: '已检测到必须更新版本，下次启动后会限制进入软件。',
      chipText: '已记录',
      chipClass: 'bg-slate-100 text-slate-500',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    error: {
      tooltip: '必须更新信息待确认',
      title: '必须更新信息待确认',
      description: '必须更新要求已记录，但本次检查失败；当前会话仍可继续使用。',
      chipText: '待确认',
      chipClass: 'bg-rose-50 text-rose-600',
      panelClass: 'border-amber-100 bg-amber-50/80',
      titleClass: 'text-amber-700',
    },
  },
  normal: {
    idle: {
      tooltip: '检查更新',
      title: '尚未执行更新检查',
      description: '启动后会静默检测更新，你也可以手动点击图标检查。',
      chipText: '空闲',
      chipClass: 'bg-slate-100 text-slate-500',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    checking: {
      tooltip: '正在检查更新',
      title: '正在检查最新版本',
      description: '正在连接更新源并比对版本信息。',
      chipText: '检查中',
      chipClass: 'bg-slate-100 text-slate-600',
      panelClass: 'border-slate-200 bg-slate-50',
      titleClass: 'text-slate-700',
    },
    available: {
      tooltip: '发现新版本，点击查看详情',
      title: '发现新版本',
      description: '可以开始下载最新安装包，下载完成后即可直接安装。',
      chipText: '可更新',
      chipClass: 'bg-primary-100 text-primary-700',
      panelClass: 'border-primary-100 bg-primary-50/70',
      titleClass: 'text-primary-700',
    },
    downloading: {
      tooltip: '正在下载更新包',
      title: '更新包下载中',
      description: '更新包将下载到本机更新缓存目录，下载完成后可直接启动安装。',
      chipText: '下载中',
      chipClass: 'bg-primary-100 text-primary-700',
      panelClass: 'border-primary-100 bg-primary-50/70',
      titleClass: 'text-primary-700',
    },
    paused: {
      tooltip: '下载已暂停，点击查看详情',
      title: '下载已暂停',
      description: '下载已暂停，可稍后继续下载。',
      chipText: '已暂停',
      chipClass: 'bg-primary-100 text-primary-700',
      panelClass: 'border-primary-100 bg-primary-50/70',
      titleClass: 'text-primary-700',
    },
    downloaded: {
      tooltip: '更新包已准备好，点击立即安装',
      title: '更新包已下载完成',
      description: '安装时将关闭当前软件，请先确认当前工作已保存。',
      chipText: '可安装',
      chipClass: 'bg-primary-100 text-primary-700',
      panelClass: 'border-primary-100 bg-primary-50/70',
      titleClass: 'text-primary-700',
    },
    up_to_date: {
      tooltip: '当前已是最新版本',
      title: '当前已是最新版本',
      description: '暂时没有比当前版本更高的正式更新。',
      chipText: '已最新',
      chipClass: 'bg-emerald-50 text-emerald-600',
      panelClass: 'border-emerald-100 bg-emerald-50/80',
      titleClass: 'text-emerald-600',
    },
    error: {
      tooltip: '更新检查失败，点击重试',
      title: '更新流程遇到问题',
      description: '你可以稍后重新检查，或确认网络和更新源配置是否正常。',
      chipText: '异常',
      chipClass: 'bg-rose-50 text-rose-600',
      panelClass: 'border-rose-100 bg-rose-50/80',
      titleClass: 'text-rose-600',
    },
  },
}

/** Mock 预演模式下 description 的覆盖映射 */
const MOCK_DESCRIPTION_OVERRIDES: Partial<Record<UpdateStatus, string>> = {
  available: '当前是开发者预演模式，可直接演示新版本提示与下载入口。',
  downloading: '正在本地模拟下载进度，不会访问真实更新源或安装包。',
  paused: '模拟下载已暂停，可点击继续恢复下载进度。',
  downloaded: '可以继续查看安装确认交互，真实安装程序不会被启动。',
}

export function createStatusDisplayComputed(params: {
  updateStatus: Ref<UpdateStatus>
  isForceUpdateMode: ComputedRef<boolean>
  forceUpdateActive: Ref<boolean>
  forceUpdatePending: Ref<boolean>
  backgroundDownloadActive: Ref<boolean>
  updateDownloadUrl: Ref<string>
  mockUpdatePreviewActive: Ref<boolean>
}) {
  const resolveMode = (): UpdateMode => {
    if (params.forceUpdateActive.value) return 'forceActive'
    if (params.forceUpdatePending.value) return 'forcePending'
    return 'normal'
  }

  const getEntry = (): StatusDisplayEntry => {
    const mode = resolveMode()
    return STATUS_DISPLAY_MAP[mode][params.updateStatus.value]
  }

  const updateTooltip = computed(() => {
    const entry = getEntry()
    // normal 模式下 downloading 状态根据 backgroundDownloadActive 切换
    if (!params.isForceUpdateMode.value && params.updateStatus.value === 'downloading') {
      return params.backgroundDownloadActive.value ? '正在后台下载更新包' : entry.tooltip
    }
    return entry.tooltip
  })

  const updateStatusTitle = computed(() => {
    const entry = getEntry()
    if (!params.isForceUpdateMode.value && params.updateStatus.value === 'downloading') {
      return params.backgroundDownloadActive.value ? '更新包后台下载中' : entry.title
    }
    return entry.title
  })

  const updateStatusDescription = computed(() => {
    const status = params.updateStatus.value

    // forceActive/forcePending 模式下，available 状态且无下载地址时的特殊文案
    if (params.forceUpdateActive.value && status === 'available' && !params.updateDownloadUrl.value) {
      return '检测到必须更新版本，但当前更新源没有可下载的安装包地址。'
    }
    if (params.forceUpdatePending.value && status === 'available' && !params.updateDownloadUrl.value) {
      return '已检测到必须更新版本，但当前更新源没有可下载的安装包地址。'
    }

    // Mock 预演模式覆盖
    if (params.mockUpdatePreviewActive.value && MOCK_DESCRIPTION_OVERRIDES[status]) {
      return MOCK_DESCRIPTION_OVERRIDES[status]!
    }

    // normal 模式下 available 状态且无下载地址
    if (!params.isForceUpdateMode.value && status === 'available' && !params.updateDownloadUrl.value) {
      return '检测到新版本，但当前更新源缺少下载地址，请稍后再试。'
    }

    const entry = getEntry()
    // normal 模式下 downloading 状态根据 backgroundDownloadActive 切换
    if (!params.isForceUpdateMode.value && status === 'downloading') {
      return params.backgroundDownloadActive.value
        ? '更新包正在后台下载，你可以继续使用软件；下载完成后会提示安装。'
        : entry.description
    }
    return entry.description
  })

  const updateStatusChipText = computed(() => {
    const entry = getEntry()
    if (!params.isForceUpdateMode.value && params.updateStatus.value === 'downloading') {
      return params.backgroundDownloadActive.value ? '后台下载中' : entry.chipText
    }
    return entry.chipText
  })

  const updateStatusChipClass = computed(() => getEntry().chipClass)
  const updateStatusPanelClass = computed(() => getEntry().panelClass)
  const updateStatusTitleClass = computed(() => getEntry().titleClass)

  return {
    updateTooltip,
    updateStatusTitle,
    updateStatusDescription,
    updateStatusChipText,
    updateStatusChipClass,
    updateStatusPanelClass,
    updateStatusTitleClass,
  }
}

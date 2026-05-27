<template>
  <div class="flex h-screen w-full bg-surface-50 overflow-hidden font-sans text-slate-900">
    <aside class="w-64 flex-shrink-0 bg-primary-900 flex flex-col transition-[width,transform] duration-300 relative z-20 shadow-2xl">
      <div class="h-20 flex items-center px-6 bg-primary-950/30 backdrop-blur-sm border-b border-white/5">
        <div class="flex items-center gap-3">
          <div
            class="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center shadow-lg shadow-primary-900/50"
            @click="handleLogoTap"
          >
            <img src="/logo.svg" alt="Easy Exam" class="w-8 h-8" />
          </div>
          <div>
            <h1 class="text-white font-bold tracking-tight text-base">Easy Exam</h1>
            <div class="flex items-center gap-2">
              <p class="text-primary-300 text-xs">v{{ currentVersion }}</p>
              <span
                v-if="developerMode"
                class="px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-100 text-[10px] border border-amber-300/40 tracking-wide"
              >
                开发者模式
              </span>
            </div>
          </div>
        </div>
      </div>

      <transition name="fade-slide">
        <div
          v-if="!licenseStore.checked"
          class="px-4 py-2 bg-primary-800/60 text-primary-300 text-xs flex items-center gap-2 border-b border-white/5"
        >
          <svg class="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
          </svg>
          正在连接后端...
        </div>
      </transition>

      <nav class="flex-1 py-6 px-3 space-y-1 overflow-y-auto custom-scrollbar">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-4 py-3 rounded-xl transition-[background-color,color,box-shadow] duration-200 group relative overflow-hidden"
          :class="[
            $route.path.startsWith(item.path) ? 'bg-primary-600 text-white shadow-lg shadow-primary-900/20' : 'text-primary-200 hover:bg-white/5 hover:text-white',
            isNavItemDisabled(item.path) ? 'pointer-events-none opacity-50 cursor-not-allowed' : ''
          ]"
        >
          <component :is="item.icon" class="w-5 h-5 transition-transform duration-200 group-hover:scale-110" />
          <span class="font-medium text-sm tracking-wide">{{ item.label }}</span>
          <div v-if="$route.path.startsWith(item.path)" class="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white/20 rounded-l-full" />
        </router-link>
      </nav>

      <div class="px-3 pb-2 flex gap-1.5">
        <el-tooltip content="将当前所有数据（科目、教师、考场、排班等）导出为备份文件" placement="right" :show-after="300">
          <el-button
            class="flex-1 !text-primary-300 !border-white/10 !bg-white/5 hover:!bg-white/10 hover:!text-white !text-[11px] !h-7 !px-1.5 !min-w-0"
            @click="handleExportState"
          >
            <el-icon class="mr-0.5 !text-[11px]"><Download /></el-icon>
            导出备份
          </el-button>
        </el-tooltip>
        <el-tooltip content="从备份文件恢复数据，将覆盖当前所有数据" placement="right" :show-after="300">
          <el-button
            class="flex-1 !text-primary-300 !border-white/10 !bg-white/5 hover:!bg-white/10 hover:!text-white !text-[11px] !h-7 !px-1.5 !min-w-0"
            @click="handleImportState"
          >
            <el-icon class="mr-0.5 !text-[11px]"><Upload /></el-icon>
            导入备份
          </el-button>
        </el-tooltip>
      </div>

      <div class="p-4 bg-primary-950/30 border-t border-white/5">
        <div class="flex items-center gap-3 px-2">
          <div class="w-9 h-9 rounded-full bg-slate-200 border-2 border-primary-700 flex items-center justify-center overflow-hidden">
            <img :src="userProfile.avatar" :alt="userProfile.name" class="w-full h-full" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-white truncate">{{ userProfile.name }}</p>
            <p class="text-xs text-primary-400 truncate">{{ userProfile.email }}</p>
          </div>
          <div class="flex items-center gap-1">
            <el-tooltip :content="updateTooltip" placement="top" :show-after="200">
              <el-button
                link
                class="relative !p-0"
                :class="updateButtonClass"
                @click="handleUpdateIconClick"
              >
                <el-icon v-if="updateStatus === 'checking'" class="animate-spin"><Loading /></el-icon>
                <el-icon v-else><Download /></el-icon>
                <span
                  v-if="showUpdateBadge"
                  class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-amber-400 ring-2 ring-primary-900 animate-pulse"
                />
              </el-button>
            </el-tooltip>
            <el-button link class="!text-primary-400 hover:!text-white" @click="showSettings = true">
              <el-icon><Setting /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col relative z-10 overflow-hidden">
      <header class="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/60 flex items-center justify-between px-8 z-20">
        <div class="flex items-center gap-4">
          <h2 class="text-lg font-bold text-slate-800">{{ pageTitle }}</h2>
        </div>

        <div v-if="showWizard" class="hidden md:flex items-center gap-2">
          <div v-for="(step, index) in workflowSteps" :key="step.path" class="flex items-center">
            <div
              class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold transition-[background-color,color] duration-200"
              :class="getStepClass(step.path)"
            >
              <div class="w-2 h-2 rounded-full transition-colors duration-200" :class="getDotClass(step.path)" />
              {{ step.label }}
            </div>
            <div v-if="index < workflowSteps.length - 1" class="w-8 h-px bg-slate-200 mx-2" />
          </div>
        </div>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1 bg-slate-50 text-slate-600 rounded-full text-xs font-medium border border-slate-200">
            <el-icon class="text-slate-400"><Clock /></el-icon>
            {{ currentDateTime }}
          </div>
        </div>
      </header>

      <div class="flex-1 overflow-y-auto custom-scrollbar pt-6 px-6 md:pt-8 md:px-8">
        <router-view v-slot="{ Component, route: currentRoute }">
          <keep-alive :include="keepAliveInclude">
            <component
              :is="Component"
              v-if="currentRoute.meta.keepAlive"
              :key="getKeepAliveKey(currentRoute)"
            />
          </keep-alive>

          <transition name="fade-slide" mode="out-in">
            <component
              :is="Component"
              v-if="!currentRoute.meta.keepAlive"
              :key="currentRoute.fullPath"
            />
          </transition>
        </router-view>
      </div>
    </main>

    <ForceUpdateOverlay
      :active="forceUpdateActive"
      :current-version="currentVersion"
      :latest-version="latestVersion"
      :release-date="releaseDate"
      :notes="notes"
      :visible-notes="visibleNotes"
      :show-all-notes="showAllNotes"
      :show-history-panel="showHistoryPanel"
      :history-loading="historyLoading"
      :history-error="historyError"
      :update-history="updateHistory"
      :update-status="updateStatus"
      :update-status-title="updateStatusTitle"
      :update-status-description="updateStatusDescription"
      :update-status-message="updateStatusMessage"
      :update-status-title-class="updateStatusTitleClass"
      :update-status-panel-class="updateStatusPanelClass"
      :update-status-chip-text="updateStatusChipText"
      :update-status-chip-class="updateStatusChipClass"
      :download-progress="downloadProgress"
      :can-download="canDownload"
      :force-update-meta="forceUpdateMeta"
      @check="retryForceUpdateCheck"
      @download="startUpdateDownload"
      @install="installDownloadedUpdate"
      @toggle-notes="toggleShowAllNotes"
      @toggle-history="toggleHistoryPanel"
      @retry-history="loadUpdateHistory(true)"
      @open-release-page="openReleasePage"
    />

    <el-dialog
      v-model="showSettings"
      title="用户设置"
      width="480px"
      align-center
      destroy-on-close
      class="rounded-2xl"
    >
      <div class="flex flex-col gap-6 py-2">
        <div class="flex flex-col gap-3">
          <label class="text-sm font-bold text-slate-700">选择头像</label>
          <div class="grid grid-cols-5 gap-3">
            <div
              v-for="seed in avatarSeeds"
              :key="seed"
              class="aspect-square rounded-full border-2 cursor-pointer transition-[transform,border-color] duration-200 hover:scale-110 overflow-hidden relative"
              :class="userProfile.avatarSeed === seed ? 'border-primary-500 ring-2 ring-primary-200 ring-offset-2' : 'border-slate-200 hover:border-primary-300'"
              @click="selectAvatar(seed)"
            >
              <img :src="getAvatarUrl(seed)" class="w-full h-full bg-slate-50" />
              <div v-if="userProfile.avatarSeed === seed" class="absolute inset-0 bg-primary-500/20 flex items-center justify-center">
                <el-icon class="text-white drop-shadow-md"><Check /></el-icon>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-sm font-bold text-slate-700">用户名</label>
            <el-input v-model="userProfile.name" placeholder="请输入用户名" />
          </div>
          <div class="space-y-1.5">
            <label class="text-sm font-bold text-slate-700">工作邮箱</label>
            <el-input v-model="userProfile.email" placeholder="请输入工作邮箱" />
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <el-button @click="showSettings = false">关闭</el-button>
          <el-button type="primary" @click="saveSettings">保存更改</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showDevDialog"
      title="开发者选项"
      width="420px"
      align-center
      destroy-on-close
    >
      <div class="space-y-4 py-2">
        <div class="text-sm text-slate-600 leading-relaxed">
          开发者模式仅用于调试和问题排查，请勿在正式环境长期开启。
        </div>
        <div class="flex items-center justify-between mt-2">
          <span class="text-sm text-slate-700">开发者模式</span>
          <el-switch
            v-model="developerMode"
            active-text="开启"
            inactive-text="关闭"
          />
        </div>
        <transition name="fade-slide">
          <div v-if="developerMode" class="border-t border-slate-100 pt-3 mt-3 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex flex-col">
                <span class="text-sm text-slate-700">展示二次均衡明细</span>
                <span class="text-[10px] text-slate-400">优化完成后自动弹出详细对比数据</span>
              </div>
              <el-switch v-model="showOptimizationDetails" size="small" />
            </div>
            <div class="rounded-2xl border border-dashed border-primary-200 bg-primary-50/70 px-4 py-3">
              <div class="flex items-start justify-between gap-3">
                <div class="space-y-1">
                  <div class="text-sm font-semibold text-primary-700">更新弹窗预演</div>
                  <div class="text-[11px] leading-5 text-primary-600/80">
                    不发布真实版本也能演示“发现新版本、下载进度、安装确认”整套交互。
                  </div>
                </div>
                <span
                  class="rounded-full px-2 py-0.5 text-[10px] font-medium"
                  :class="updatePreviewBadgeClass"
                >
                  {{ updatePreviewBadgeText }}
                </span>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                <el-button type="primary" size="small" @click="activateMockUpdatePreview">
                  模拟新版本更新
                </el-button>
                <el-button type="danger" size="small" @click="activateMockForceUpdatePreview">
                  模拟强制更新
                </el-button>
                <el-button
                  size="small"
                  :disabled="!isAnyUpdatePreviewActive"
                  @click="resetMockUpdatePreview()"
                >
                  恢复真实更新状态
                </el-button>
              </div>
            </div>
          </div>
        </transition>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <el-button @click="showDevDialog = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <UpdateDialog
      v-if="!forceUpdateActive"
      v-model="showUpdateDialog"
      :current-version="currentVersion"
      :latest-version="latestVersion"
      :release-date="releaseDate"
      :notes="notes"
      :visible-notes="visibleNotes"
      :show-all-notes="showAllNotes"
      :show-history-panel="showHistoryPanel"
      :history-loading="historyLoading"
      :history-error="historyError"
      :update-history="updateHistory"
      :update-status="updateStatus"
      :update-status-title="updateStatusTitle"
      :update-status-description="updateStatusDescription"
      :update-status-message="updateStatusMessage"
      :update-status-title-class="updateStatusTitleClass"
      :update-status-panel-class="updateStatusPanelClass"
      :update-status-chip-text="updateStatusChipText"
      :update-status-chip-class="updateStatusChipClass"
      :download-progress="downloadProgress"
      :can-download="canDownload"
      @close="closeUpdateDialog"
      @check="handleManualUpdateCheck"
      @download="startUpdateDownload"
      @install="installDownloadedUpdate"
      @toggle-notes="toggleShowAllNotes"
      @toggle-history="toggleHistoryPanel"
      @retry-history="loadUpdateHistory(true)"
      @open-release-page="openReleasePage"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Notebook,
  User,
  School,
  Printer,
  QuestionFilled,
  Setting,
  DataBoard,
  Key,
  Check,
  Clock,
  Download,
  Upload,
  Loading,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import ForceUpdateOverlay from '@/components/update/ForceUpdateOverlay.vue'
import UpdateDialog from '@/components/update/UpdateDialog.vue'
import { useAppUpdate } from '@/composables/useAppUpdate'
import { useAppCacheControl, resetFrontendCaches } from '@/composables/useAppCacheControl'
import { open, saveAndRun } from '@/lib/dialog'
import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionError, formatActionSuccess } from '@/lib/uiFeedback'
import { useLicenseStore } from '@/stores/license'
import type { BackendUpdateGuardStatus } from '@/types/appUpdate'

dayjs.locale('zh-cn')

const route = useRoute()
const router = useRouter()
const licenseStore = useLicenseStore()
const { frontendResetEpoch } = useAppCacheControl()
const feedback = createUiFeedback()

const {
  currentVersion,
  updateStatus,
  latestVersion,
  releaseDate,
  notes,
  downloadProgress,
  updateDownloadUrl,
  updateStatusMessage,
  showUpdateDialog,
  showHistoryPanel,
  historyLoading,
  historyError,
  updateHistory,
  showAllNotes,
  mockUpdatePreviewActive,
  mockForceUpdatePreviewActive,
  forceUpdateActive,
  forceUpdateMeta,
  showUpdateBadge,
  updateTooltip,
  updateButtonClass,
  updateStatusTitle,
  updateStatusDescription,
  updateStatusChipText,
  updateStatusChipClass,
  updateStatusPanelClass,
  updateStatusTitleClass,
  visibleNotes,
  handleManualUpdateCheck,
  handleUpdateIconClick,
  retryForceUpdateCheck,
  startUpdateDownload,
  installDownloadedUpdate,
  toggleHistoryPanel,
  loadUpdateHistory,
  openReleasePage,
  applyBackendUpdateGuardStatus,
  activateMockUpdatePreview,
  activateMockForceUpdatePreview,
  resetMockUpdatePreview,
  closeUpdateDialog,
  toggleShowAllNotes,
  resetUpdateUiState,
} = useAppUpdate()

const canDownload = computed(() => Boolean(updateDownloadUrl.value))
const isAnyUpdatePreviewActive = computed(
  () => mockUpdatePreviewActive.value || mockForceUpdatePreviewActive.value
)
const updatePreviewBadgeText = computed(() => {
  if (mockForceUpdatePreviewActive.value) return '强更预演中'
  if (mockUpdatePreviewActive.value) return '普通预演中'
  return '未启动'
})
const updatePreviewBadgeClass = computed(() => {
  if (mockForceUpdatePreviewActive.value) {
    return 'bg-rose-100 text-rose-700'
  }
  if (mockUpdatePreviewActive.value) {
    return 'bg-primary-100 text-primary-700'
  }
  return 'bg-white text-slate-500 border border-slate-200'
})

const currentDateTime = ref(dayjs().format('YYYY年MM月DD日 dddd HH:mm'))
const showSettings = ref(false)
const avatarSeeds = ['Admin', 'Felix', 'Aneka', 'Zack', 'Milo', 'Bandit', 'Tinker', 'Cali', 'Coco', 'Bear']
const showDevDialog = ref(false)
const developerMode = ref(localStorage.getItem('developer_mode') === 'true')
const showOptimizationDetails = ref(localStorage.getItem('show_optimization_details') === 'true')

const createDefaultUserProfile = () => ({
  name: '管理员',
  email: '',
  avatarSeed: 'Cali',
  avatar: 'https://api.dicebear.com/9.x/notionists/svg?seed=Cali&backgroundColor=e1f5fe,ffecb3,ffe082,ffcdd2,f8bbd0,e1bee7,d1c4e9,c5cae9,bbdefb,b3e5fc,b2ebf2,b2dfdb,c8e6c9,dcedc8,f0f4c3,fff9c4'
})

const userProfile = reactive(createDefaultUserProfile())

const getAvatarUrl = (seed: string) => `https://api.dicebear.com/9.x/notionists/svg?seed=${seed}&backgroundColor=e1f5fe,ffecb3,ffe082,ffcdd2,f8bbd0,e1bee7,d1c4e9,c5cae9,bbdefb,b3e5fc,b2ebf2,b2dfdb,c8e6c9,dcedc8,f0f4c3,fff9c4`

const selectAvatar = (seed: string) => {
  userProfile.avatarSeed = seed
  userProfile.avatar = getAvatarUrl(seed)
}

const saveSettings = () => {
  localStorage.setItem('user_profile', JSON.stringify(userProfile))
  showSettings.value = false
  ElMessage.success('用户设置已保存')
}

let devTapTimer: any = null
const devTapCount = ref(0)

const buildStateExportFilename = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `考试数据备份_${year}-${month}-${day}_${hours}-${minutes}.examstate`
}

const handleExportState = async () => {
  await saveAndRun({
    dialog: {
      title: '导出数据备份',
      filters: [{ name: 'Exam State Files', extensions: ['examstate'] }],
      defaultPath: buildStateExportFilename(),
    },
    run: async (path) => {
      return await pythonBackend.request('system.exportState', { path })
    },
    successText: '数据备份已保存',
    errorText: '导出数据备份失败',
    openFolderTitle: '数据备份导出成功',
  })
}

const handleImportState = async () => {
  const selected = await open({
    title: '导入数据备份',
    multiple: false,
    filters: [
      { name: 'Exam State Files', extensions: ['examstate'] },
      { name: 'JSON Files', extensions: ['json'] },
    ],
  })
  if (!selected || Array.isArray(selected)) return

  try {
    await feedback.confirmWarning({
      message: '导入后将覆盖当前系统全部数据，是否继续？',
      title: '导入数据备份',
      confirmButtonText: '继续导入',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await pythonBackend.request('system.importState', { path: selected })
    resetFrontendCaches()
    await router.replace('/')
    feedback.success(formatActionSuccess('导入数据备份'))
  } catch (error: any) {
    feedback.error(formatActionError('导入数据备份', error))
  }
}

const handleLogoTap = () => {
  devTapCount.value += 1
  if (devTapCount.value === 1) {
    if (devTapTimer) clearTimeout(devTapTimer)
    devTapTimer = setTimeout(() => {
      devTapCount.value = 0
      devTapTimer = null
    }, 1500)
  }
  if (devTapCount.value >= 5) {
    devTapCount.value = 0
    if (devTapTimer) {
      clearTimeout(devTapTimer)
      devTapTimer = null
    }
    showDevDialog.value = true
  }
}

const syncBackendUpdateGuard = async (forceRefresh = false) => {
  try {
    const status = await pythonBackend.request(
      forceRefresh ? 'system.refreshUpdateGuard' : 'system.getUpdateGuardStatus',
      {}
    ) as BackendUpdateGuardStatus
    applyBackendUpdateGuardStatus(status, {
      message: status.locked
        ? '后端已启用强制更新门禁，请先完成升级后再继续使用软件。'
        : undefined,
    })
  } catch (error) {
    console.warn('读取后端更新门禁状态失败', error)
  }
}

const enforceProtectedRoute = () => {
  if (forceUpdateActive.value) {
    if (route.path !== '/dashboard') {
      void router.replace('/dashboard')
    }
    return
  }

  if (licenseStore.checked && !licenseStore.valid && route.path !== '/registration') {
    void router.replace('/registration')
  }
}

watch(
  [() => licenseStore.checked, () => licenseStore.valid, () => forceUpdateActive.value, () => route.path],
  () => {
    enforceProtectedRoute()
  }
)

watch(developerMode, (value) => {
  localStorage.setItem('developer_mode', value ? 'true' : 'false')
  if (!value && isAnyUpdatePreviewActive.value) {
    void resetMockUpdatePreview(true)
  }
})

watch(showOptimizationDetails, (value) => {
  localStorage.setItem('show_optimization_details', value ? 'true' : 'false')
})

watch(frontendResetEpoch, () => {
  Object.assign(userProfile, createDefaultUserProfile())
  showSettings.value = false
  showDevDialog.value = false
  developerMode.value = false
  showOptimizationDetails.value = false
  resetUpdateUiState()
})

onMounted(() => {
  setInterval(() => {
    currentDateTime.value = dayjs().format('YYYY年MM月DD日 dddd HH:mm')
  }, 60000)

  const saved = localStorage.getItem('user_profile')
  if (saved) {
    try {
      const profile = JSON.parse(saved)
      Object.assign(userProfile, profile)
    } catch (error) {
      console.error('Failed to load profile', error)
    }
  }

  void syncBackendUpdateGuard(false)
})

const navItems = [
  { path: '/dashboard', label: '工作台', icon: DataBoard },
  { path: '/subjects', label: '科目设置', icon: Notebook },
  { path: '/proctoring', label: '监考编排', icon: User },
  { path: '/rooms', label: '考场编排', icon: School },
  { path: '/printing', label: '资料打印', icon: Printer },
  { path: '/registration', label: '软件注册', icon: Key },
  { path: '/help', label: '帮助中心', icon: QuestionFilled },
]

const workflowSteps = [
  { path: '/subjects', label: '科目设置' },
  { path: '/proctoring', label: '监考编排' },
  { path: '/rooms', label: '考场编排' },
  { path: '/printing', label: '资料打印' },
]

const pageTitle = computed(() => {
  const item = navItems.find((entry) => route.path.startsWith(entry.path))
  return item ? item.label : 'Easy Exam'
})

const showWizard = computed(() =>
  workflowSteps.some((step) => route.path.startsWith(step.path))
)

const keepAliveInclude = ['PrintingPage', 'RegistrationPage']

function getKeepAliveKey(currentRoute: any) {
  const baseKey = String(currentRoute.name || currentRoute.path)
  if (currentRoute.meta?.preserveOnAppReset) return baseKey
  return `${baseKey}:${frontendResetEpoch.value}`
}

function isNavItemDisabled(path: string) {
  if (forceUpdateActive.value) {
    return true
  }
  if (!licenseStore.valid && path !== '/registration') {
    return true
  }
  return false
}

function getStepClass(path: string) {
  if (route.path.startsWith(path)) {
    return 'bg-primary-50 text-primary-700 ring-1 ring-primary-200'
  }
  const currentIndex = workflowSteps.findIndex((step) => route.path.startsWith(step.path))
  const stepIndex = workflowSteps.findIndex((step) => step.path === path)
  if (stepIndex < currentIndex) {
    return 'text-slate-500 bg-slate-50'
  }
  return 'text-slate-400'
}

function getDotClass(path: string) {
  if (route.path.startsWith(path)) return 'bg-primary-500'
  const currentIndex = workflowSteps.findIndex((step) => route.path.startsWith(step.path))
  const stepIndex = workflowSteps.findIndex((step) => step.path === path)
  if (stepIndex < currentIndex) return 'bg-slate-400'
  return 'bg-slate-200'
}
</script>

<style>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-slide-enter-active {
  transition: all 0.3s ease-out;
}

.fade-slide-leave-active {
  transition: all 0.15s ease-in;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>

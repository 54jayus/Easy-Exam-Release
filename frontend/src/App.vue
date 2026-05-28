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
                <!-- Background download mini ring -->
                <svg
                  v-if="backgroundDownloadActive"
                  class="absolute inset-[-3px] w-[calc(100%+6px)] h-[calc(100%+6px)] -rotate-90 pointer-events-none"
                  viewBox="0 0 36 36"
                >
                  <circle
                    cx="18" cy="18" r="16"
                    fill="none"
                    stroke="rgba(255,255,255,0.15)"
                    stroke-width="2.5"
                  />
                  <circle
                    cx="18" cy="18" r="16"
                    fill="none"
                    stroke="#fbbf24"
                    stroke-width="2.5"
                    stroke-linecap="round"
                    :stroke-dasharray="`${downloadProgress * 1.005} 100.5`"
                    class="transition-all duration-300"
                  />
                </svg>
                <!-- Badge: downloading (amber pulse) or ready (green solid) -->
                <span
                  v-if="showUpdateBadge && !backgroundDownloadActive"
                  class="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full ring-2 ring-primary-900 animate-pulse"
                  :class="updateStatus === 'downloaded' ? 'bg-emerald-400' : 'bg-amber-400'"
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
      width="500px"
      align-center
      destroy-on-close
      class="dev-dialog"
    >
      <template #header>
        <div class="flex items-center gap-2.5 -mb-1">
          <div class="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
            <el-icon class="text-amber-600" :size="16"><Setting /></el-icon>
          </div>
          <div>
            <div class="text-base font-bold text-slate-800">开发者选项</div>
            <div class="text-xs text-slate-400 font-normal">仅用于调试与问题排查</div>
          </div>
        </div>
      </template>

      <div class="space-y-5 py-1">
        <!-- Warning Banner -->
        <div class="flex items-start gap-3 px-4 py-3 rounded-xl bg-amber-50 border border-amber-200/80">
          <el-icon class="text-amber-500 mt-0.5 flex-shrink-0" :size="16"><Warning /></el-icon>
          <p class="text-xs text-amber-700 leading-relaxed">
            开发者模式包含调试功能，可能影响系统稳定性。请勿在正式考试环境长期开启，使用完毕后建议及时关闭。
          </p>
        </div>

        <!-- Section: General -->
        <div class="rounded-xl border border-slate-200/80 overflow-hidden">
          <div class="px-4 py-3 bg-slate-50/80 border-b border-slate-100">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <el-icon class="text-slate-500" :size="14"><Setting /></el-icon>
                <span class="text-sm font-semibold text-slate-700">通用</span>
              </div>
              <el-switch
                v-model="developerMode"
                active-text="开启"
                inactive-text="关闭"
                size="small"
              />
            </div>
          </div>

          <transition name="fade-slide">
            <div v-if="developerMode" class="divide-y divide-slate-100">
              <!-- DevTools -->
              <div class="flex items-center justify-between px-4 py-3">
                <div class="flex items-center gap-3">
                  <div class="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center">
                    <el-icon class="text-indigo-500" :size="14"><Monitor /></el-icon>
                  </div>
                  <div>
                    <span class="text-sm text-slate-700 font-medium">开发者工具</span>
                    <span class="block text-[11px] text-slate-400">打开 Chromium DevTools 控制台</span>
                  </div>
                </div>
                <el-button size="small" type="primary" plain @click="openDevTools">
                  打开
                </el-button>
              </div>

              <!-- Optimization details -->
              <div class="flex items-center justify-between px-4 py-3">
                <div class="flex items-center gap-3">
                  <div class="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center">
                    <el-icon class="text-emerald-500" :size="14"><View /></el-icon>
                  </div>
                  <div>
                    <span class="text-sm text-slate-700 font-medium">二次均衡明细</span>
                    <span class="block text-[11px] text-slate-400">优化完成后弹出详细对比数据</span>
                  </div>
                </div>
                <el-switch v-model="showOptimizationDetails" size="small" />
              </div>
            </div>
          </transition>

          <div v-if="!developerMode" class="px-4 py-6 text-center">
            <p class="text-sm text-slate-400">开启开发者模式以查看调试选项</p>
          </div>
        </div>

        <!-- Section: Update Preview -->
        <transition name="fade-slide">
          <div v-if="developerMode" class="rounded-xl border border-slate-200/80 overflow-hidden">
            <div class="px-4 py-3 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <el-icon class="text-slate-500" :size="14"><Download /></el-icon>
                <span class="text-sm font-semibold text-slate-700">更新弹窗预演</span>
              </div>
              <span
                class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold tracking-wide"
                :class="updatePreviewBadgeClass"
              >
                {{ updatePreviewBadgeText }}
              </span>
            </div>
            <div class="px-4 py-3 space-y-3">
              <p class="text-xs text-slate-500 leading-relaxed">
                不发布真实版本也能演示"发现新版本 → 下载进度 → 安装确认"整套交互流程。
              </p>
              <div class="flex gap-2">
                <el-button type="primary" size="small" class="flex-1" @click="activateMockUpdatePreview">
                  模拟更新
                </el-button>
                <el-button type="danger" size="small" class="flex-1" @click="activateMockForceUpdatePreview">
                  模拟强制更新
                </el-button>
                <el-button
                  size="small"
                  class="flex-1"
                  :disabled="!isAnyUpdatePreviewActive"
                  @click="resetMockUpdatePreview()"
                >
                  恢复真实状态
                </el-button>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <template #footer>
        <div class="flex items-center justify-between">
          <el-button
            size="small"
            :icon="Refresh"
            :disabled="!developerMode"
            @click="resetDevOptions"
          >
            重置默认
          </el-button>
          <el-button @click="showDevDialog = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <BackgroundDownloadBar
      :visible="showBgDownloadBar"
      :progress="downloadProgress"
      :version="latestVersion"
      :is-ready="bgDownloadReady"
      :is-paused="bgDownloadPaused"
      @install="installDownloadedUpdate"
      @pause="pauseUpdateDownload"
      @resume="startBackgroundUpdateDownload"
      @dismiss="handleBgBarDismiss"
    />

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
      @pause="pauseUpdateDownload"
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
  Warning,
  Monitor,
  Refresh,
  View,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import BackgroundDownloadBar from '@/components/update/BackgroundDownloadBar.vue'
import ForceUpdateOverlay from '@/components/update/ForceUpdateOverlay.vue'
import UpdateDialog from '@/components/update/UpdateDialog.vue'
import { useAppUpdate } from '@/composables/useAppUpdate'
import { useAppCacheControl, resetFrontendCaches } from '@/composables/useAppCacheControl'
import { open, saveAndRun } from '@/lib/dialog'
import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionError, formatActionSuccess } from '@/lib/uiFeedback'
import { useLicenseStore } from '@/stores/license'

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
  backgroundDownloadActive,
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
  startBackgroundUpdateDownload,
  pauseUpdateDownload,
  installDownloadedUpdate,
  toggleHistoryPanel,
  loadUpdateHistory,
  openReleasePage,
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

const bgDownloadReady = computed(() =>
  !backgroundDownloadActive.value && updateStatus.value === 'downloaded' && !showUpdateDialog.value
)
const bgDownloadPaused = computed(() =>
  updateStatus.value === 'paused' && !showUpdateDialog.value
)
const bgDownloadBarDismissed = ref(false)
const showBgDownloadBar = computed(() =>
  ((backgroundDownloadActive.value && !showUpdateDialog.value) || bgDownloadReady.value || bgDownloadPaused.value) && !bgDownloadBarDismissed.value
)
const handleBgBarDismiss = () => {
  bgDownloadBarDismissed.value = true
}

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

const openDevTools = () => {
  window.electron?.ipcRenderer.invoke('open-devtools')
}

const resetDevOptions = () => {
  developerMode.value = false
  showOptimizationDetails.value = false
  if (isAnyUpdatePreviewActive.value) {
    void resetMockUpdatePreview(true)
  }
  ElMessage.success('开发者选项已重置')
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

watch(backgroundDownloadActive, (active) => {
  if (active) bgDownloadBarDismissed.value = false
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

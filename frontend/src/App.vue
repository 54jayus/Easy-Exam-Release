<template>
  <div class="flex h-screen w-full bg-surface-50 overflow-hidden font-sans text-slate-900">
    <!-- Immersive Sidebar -->
    <aside class="w-64 flex-shrink-0 bg-primary-900 flex flex-col transition-[width,transform] duration-300 relative z-20 shadow-2xl">
      <!-- Brand -->
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

      <!-- Backend Loading Indicator -->
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

      <!-- Navigation -->
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
          
          <!-- Active Indicator -->
          <div v-if="$route.path.startsWith(item.path)" class="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white/20 rounded-l-full"></div>
        </router-link>
      </nav>

      <!-- Data Backup / Restore -->
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

      <!-- User Profile / Footer -->
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
              <button
                type="button"
                class="relative h-9 w-9 rounded-full border transition-all duration-200 flex items-center justify-center"
                :class="updateButtonClass"
                @click="handleUpdateIconClick"
              >
                <el-icon :class="updateIconClass"><RefreshRight /></el-icon>
                <span
                  v-if="showUpdateBadge"
                  class="absolute right-1.5 top-1.5 h-2.5 w-2.5 rounded-full bg-rose-400 ring-2 ring-primary-950/70 animate-pulse"
                />
              </button>
            </el-tooltip>
            <el-button link class="!text-primary-400 hover:!text-white" @click="showSettings = true">
              <el-icon><Setting /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col relative z-10 overflow-hidden">
      <!-- Top Bar with Step Wizard -->
      <header class="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/60 flex items-center justify-between px-8 z-20">
        <!-- Breadcrumb / Page Title -->
        <div class="flex items-center gap-4">
          <h2 class="text-lg font-bold text-slate-800">{{ pageTitle }}</h2>
        </div>

        <!-- Step Wizard (Only visible on workflow pages) -->
        <div v-if="showWizard" class="hidden md:flex items-center gap-2">
           <div v-for="(step, index) in workflowSteps" :key="step.path" class="flex items-center">
             <div
               class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold transition-[background-color,color] duration-200"
               :class="getStepClass(step.path)"
             >
               <div class="w-2 h-2 rounded-full transition-colors duration-200" :class="getDotClass(step.path)"></div>
               {{ step.label }}
             </div>
             <div v-if="index < workflowSteps.length - 1" class="w-8 h-px bg-slate-200 mx-2"></div>
           </div>
        </div>

        <!-- System Status / Date Time -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1 bg-slate-50 text-slate-600 rounded-full text-xs font-medium border border-slate-200">
            <el-icon class="text-slate-400"><Clock /></el-icon>
            {{ currentDateTime }}
          </div>
        </div>
      </header>

      <!-- Scrollable Content -->
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

    <!-- User Settings Dialog -->
    <el-dialog
      v-model="showSettings"
      title="用户设置"
      width="480px"
      align-center
      destroy-on-close
      class="rounded-2xl"
    >
      <div class="flex flex-col gap-6 py-2">
        <!-- Avatar Selection -->
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

        <!-- Form Fields -->
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
          </div>
        </transition>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <el-button @click="showDevDialog = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showUpdateDialog"
      title="软件更新"
      width="540px"
      align-center
      class="rounded-2xl"
    >
      <div class="space-y-5 py-1 max-h-[calc(80vh-160px)] overflow-y-auto pr-1 custom-scrollbar">
        <template v-if="updateStatus === 'up_to_date'">
          <div class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 flex items-center gap-3">
            <div class="w-9 h-9 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
              <el-icon class="text-white text-base"><Check /></el-icon>
            </div>
            <div>
              <div class="text-sm font-semibold text-emerald-800">当前已是最新版本</div>
              <div class="mt-0.5 text-xs text-emerald-600">
                v{{ currentVersion }}{{ releaseDate ? ` · 发布于 ${releaseDate}` : '' }}
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div class="text-xs font-medium text-slate-500">当前版本</div>
              <div class="mt-1 text-lg font-bold text-slate-900">v{{ currentVersion }}</div>
            </div>
            <div class="rounded-2xl border border-primary-100 bg-primary-50 px-4 py-3">
              <div class="text-xs font-medium text-primary-500">最新版本</div>
              <div class="mt-1 text-lg font-bold text-primary-700">
                {{ latestVersion ? `v${latestVersion}` : '暂无可用更新' }}
              </div>
              <div v-if="releaseDate" class="mt-1 text-xs text-primary-500">发布时间：{{ releaseDate }}</div>
            </div>
          </div>
        </template>

        <div class="rounded-2xl border px-4 py-3" :class="updateStatusPanelClass">
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="text-sm font-semibold" :class="updateStatusTitleClass">{{ updateStatusTitle }}</div>
              <div class="mt-1 text-xs text-slate-500">{{ updateStatusDescription }}</div>
            </div>
            <div
              class="rounded-full px-3 py-1 text-xs font-semibold"
              :class="updateStatusChipClass"
            >
              {{ updateStatusChipText }}
            </div>
          </div>
          <div v-if="updateStatus === 'downloading'" class="mt-4 space-y-2">
            <el-progress :percentage="downloadProgress" :stroke-width="10" :show-text="false" />
            <div class="text-right text-xs text-slate-500">已下载 {{ downloadProgress.toFixed(1) }}%</div>
          </div>
          <div v-if="updateStatusMessage" class="mt-3 text-xs text-slate-500">
            {{ updateStatusMessage }}
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white px-4 py-4">
          <div class="text-sm font-semibold text-slate-800 mb-3">更新内容</div>
          <ul v-if="notes.length" class="space-y-2 text-sm text-slate-600">
            <li v-for="item in visibleNotes" :key="item" class="flex items-start gap-2">
              <span class="mt-1 h-1.5 w-1.5 rounded-full bg-primary-400 flex-shrink-0" />
              <span>{{ item }}</span>
            </li>
          </ul>
          <div v-else class="text-sm text-slate-500">当前版本暂未提供额外更新说明。</div>
          <div class="mt-3 flex items-center justify-between">
            <el-button
              v-if="notes.length > 4"
              link
              class="!px-0 !text-primary-600 !text-xs"
              @click="showAllNotes = !showAllNotes"
            >
              {{ showAllNotes ? '▴ 收起' : `▾ 展开全部 ${notes.length} 条` }}
            </el-button>
            <span v-else />
            <el-button link class="!px-0 !text-primary-600 !text-xs" @click="toggleHistoryPanel">
              {{ showHistoryPanel ? '收起历史记录' : '查看历史更新' }}
            </el-button>
          </div>
        </div>

        <transition name="fade-slide">
          <div
            v-if="showHistoryPanel"
            class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4"
          >
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-slate-800">历史更新记录</div>
                <div class="mt-1 text-xs text-slate-500">可在软件内快速查看以往版本的发布时间与更新说明。</div>
              </div>
              <el-button
                v-if="historyError"
                link
                class="!px-0 !text-primary-600"
                @click="loadUpdateHistory(true)"
              >
                重试
              </el-button>
            </div>

            <div v-if="historyLoading" class="mt-4 flex items-center gap-2 text-sm text-slate-500">
              <el-icon class="animate-spin"><RefreshRight /></el-icon>
              正在加载历史更新记录...
            </div>

            <div v-else-if="historyError" class="mt-4 rounded-xl border border-rose-100 bg-rose-50 px-3 py-3 text-sm text-rose-600">
              {{ historyError }}
            </div>

            <div v-else-if="updateHistory.length" class="mt-4 space-y-4">
              <div
                v-for="entry in updateHistory"
                :key="entry.version"
                class="rounded-2xl border border-white bg-white px-4 py-4 shadow-sm"
              >
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <div class="flex items-center gap-2">
                      <div class="text-base font-semibold text-slate-900">{{ entry.title }}</div>
                      <span
                        v-if="entry.version === currentVersion"
                        class="rounded-full bg-primary-50 px-2 py-0.5 text-[11px] font-semibold text-primary-600"
                      >
                        当前版本
                      </span>
                    </div>
                    <div class="mt-1 text-xs text-slate-500">发布时间：{{ entry.releaseDate || '未提供' }}</div>
                  </div>
                  <el-button
                    v-if="entry.releasePageUrl"
                    link
                    class="!px-0 !text-primary-600"
                    @click="openReleasePage(entry.releasePageUrl)"
                  >
                    查看发布页
                  </el-button>
                </div>

                <ul v-if="entry.notes.length" class="mt-3 space-y-2 text-sm text-slate-600">
                  <li v-for="item in entry.notes" :key="`${entry.version}-${item}`" class="flex items-start gap-2">
                    <span class="mt-1 h-1.5 w-1.5 rounded-full bg-primary-400" />
                    <span>{{ item }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <div v-else class="mt-4 text-sm text-slate-500">
              暂时还没有可展示的历史更新记录。
            </div>
          </div>
        </transition>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <el-button @click="showUpdateDialog = false">关闭</el-button>
          <el-button
            v-if="updateStatus === 'available'"
            type="primary"
            :disabled="!updateDownloadUrl"
            @click="startUpdateDownload"
          >
            立即下载
          </el-button>
          <el-button
            v-else-if="updateStatus === 'downloaded'"
            type="primary"
            @click="installDownloadedUpdate"
          >
            立即安装
          </el-button>
          <el-button
            v-else-if="updateStatus === 'checking' || updateStatus === 'downloading'"
            type="primary"
            loading
            disabled
          >
            {{ updateStatus === 'checking' ? '正在检查' : '正在下载' }}
          </el-button>
          <el-button
            v-else
            type="primary"
            @click="handleManualUpdateCheck"
          >
            重新检查
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLicenseStore } from "./stores/license"
import { useAppCacheControl, resetFrontendCaches } from '@/composables/useAppCacheControl'
import {
  Notebook, User, School, Printer,
  QuestionFilled, Setting, DataBoard, Key, Check, Clock, Download, Upload, RefreshRight
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { pythonBackend } from './lib/pythonBackend'
import { open, saveAndRun } from './lib/dialog'
import { createUiFeedback, formatActionError, formatActionSuccess } from './lib/uiFeedback'

dayjs.locale('zh-cn')

const route = useRoute()
const router = useRouter()
const licenseStore = useLicenseStore()
const { frontendResetEpoch } = useAppCacheControl()
const feedback = createUiFeedback()

type UpdateStatus = 'idle' | 'checking' | 'up_to_date' | 'available' | 'downloading' | 'downloaded' | 'error'

type UpdateCheckResult = {
  currentVersion: string
  latestVersion: string | null
  hasUpdate: boolean
  enabled: boolean
  releaseDate: string | null
  notes: string[]
  mandatory: boolean
  url: string | null
  downloadedFilePath: string | null
}

type UpdateHistoryEntry = {
  version: string
  title: string
  releaseDate: string
  notes: string[]
  url: string
  releasePageUrl?: string
}

// Once backend finishes checking, redirect to /registration if license is invalid
watch(() => licenseStore.checked, (checked) => {
  if (checked && !licenseStore.valid && route.path !== '/registration') {
    router.replace('/registration')
  }
})

const currentDateTime = ref(dayjs().format('YYYY年MM月DD日 dddd HH:mm'))
const currentVersion = ref('--')
const updateStatus = ref<UpdateStatus>('idle')
const latestVersion = ref('')
const releaseDate = ref('')
const notes = ref<string[]>([])
const downloadProgress = ref(0)
const downloadedFilePath = ref('')
const updateDownloadUrl = ref('')
const updateStatusMessage = ref('')
const showUpdateDialog = ref(false)
const showHistoryPanel = ref(false)
const historyLoading = ref(false)
const historyLoaded = ref(false)
const historyError = ref('')
const updateHistory = ref<UpdateHistoryEntry[]>([])
const showAllNotes = ref(false)

onMounted(() => {
  setInterval(() => {
    currentDateTime.value = dayjs().format('YYYY年MM月DD日 dddd HH:mm')
  }, 60000)
})

const showSettings = ref(false)
const avatarSeeds = ['Admin', 'Felix', 'Aneka', 'Zack', 'Milo', 'Bandit', 'Tinker', 'Cali', 'Coco', 'Bear']

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

onMounted(() => {
  const saved = localStorage.getItem('user_profile')
  if (saved) {
    try {
      const p = JSON.parse(saved)
      Object.assign(userProfile, p)
    } catch(e) { console.error('Failed to load profile', e) }
  }
})

const showDevDialog = ref(false)
const developerMode = ref(localStorage.getItem('developer_mode') === 'true')
const showOptimizationDetails = ref(localStorage.getItem('show_optimization_details') === 'true')

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
  } catch (e: any) {
    feedback.error(formatActionError('导入数据备份', e))
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

const showUpdateBadge = computed(() =>
  ['available', 'downloading', 'downloaded'].includes(updateStatus.value)
)

const updateTooltip = computed(() => {
  switch (updateStatus.value) {
    case 'checking':
      return '正在检查更新'
    case 'available':
      return '发现新版本，点击查看详情'
    case 'downloading':
      return '正在下载更新包'
    case 'downloaded':
      return '更新包已准备好，点击立即安装'
    case 'up_to_date':
      return '当前已是最新版本'
    case 'error':
      return '更新检查失败，点击重试'
    default:
      return '检查更新'
  }
})

const updateButtonClass = computed(() => {
  if (updateStatus.value === 'available' || updateStatus.value === 'downloading' || updateStatus.value === 'downloaded') {
    return 'border-primary-400/40 bg-primary-500/20 text-white shadow-lg shadow-primary-950/20 hover:bg-primary-500/30'
  }
  if (updateStatus.value === 'checking') {
    return 'border-primary-300/20 bg-white/10 text-white hover:bg-white/15'
  }
  return 'border-white/10 bg-white/5 text-primary-300 hover:bg-white/10 hover:text-white'
})

const updateIconClass = computed(() =>
  updateStatus.value === 'checking' ? 'animate-spin text-sm' : 'text-sm'
)

const updateStatusTitle = computed(() => {
  switch (updateStatus.value) {
    case 'checking':
      return '正在检查最新版本'
    case 'available':
      return '发现新版本'
    case 'downloading':
      return '更新包下载中'
    case 'downloaded':
      return '更新包已下载完成'
    case 'up_to_date':
      return '当前已是最新版本'
    case 'error':
      return '更新流程遇到问题'
    default:
      return '尚未执行更新检查'
  }
})

const updateStatusDescription = computed(() => {
  if (updateStatus.value === 'available' && !updateDownloadUrl.value) {
    return '检测到新版本，但当前更新源缺少下载地址，请稍后再试。'
  }
  switch (updateStatus.value) {
    case 'checking':
      return '正在连接更新源并比对版本信息。'
    case 'available':
      return '可以开始下载最新安装包，下载完成后即可直接安装。'
    case 'downloading':
      return '更新包将下载到本机更新缓存目录，下载完成后可直接启动安装。'
    case 'downloaded':
      return '安装时将关闭当前软件，请先确认当前工作已保存。'
    case 'up_to_date':
      return '暂时没有比当前版本更高的正式更新。'
    case 'error':
      return '你可以稍后重新检查，或确认网络和更新源配置是否正常。'
    default:
      return '启动后会静默检测更新，你也可以手动点击图标检查。'
  }
})

const updateStatusChipText = computed(() => {
  switch (updateStatus.value) {
    case 'checking':
      return '检查中'
    case 'available':
      return '可更新'
    case 'downloading':
      return '下载中'
    case 'downloaded':
      return '可安装'
    case 'up_to_date':
      return '已最新'
    case 'error':
      return '异常'
    default:
      return '空闲'
  }
})

const updateStatusChipClass = computed(() => {
  switch (updateStatus.value) {
    case 'available':
    case 'downloading':
    case 'downloaded':
      return 'bg-primary-100 text-primary-700'
    case 'checking':
      return 'bg-slate-100 text-slate-600'
    case 'error':
      return 'bg-rose-50 text-rose-600'
    case 'up_to_date':
      return 'bg-emerald-50 text-emerald-600'
    default:
      return 'bg-slate-100 text-slate-500'
  }
})

const updateStatusPanelClass = computed(() => {
  switch (updateStatus.value) {
    case 'available':
    case 'downloading':
    case 'downloaded':
      return 'border-primary-100 bg-primary-50/70'
    case 'error':
      return 'border-rose-100 bg-rose-50/80'
    case 'up_to_date':
      return 'border-emerald-100 bg-emerald-50/80'
    default:
      return 'border-slate-200 bg-slate-50'
  }
})

const updateStatusTitleClass = computed(() => {
  switch (updateStatus.value) {
    case 'available':
    case 'downloading':
    case 'downloaded':
      return 'text-primary-700'
    case 'error':
      return 'text-rose-600'
    case 'up_to_date':
      return 'text-emerald-600'
    default:
      return 'text-slate-700'
  }
})

const visibleNotes = computed(() =>
  showAllNotes.value || notes.value.length <= 4 ? notes.value : notes.value.slice(0, 4)
)

const applyUpdateResult = (result: UpdateCheckResult, manual: boolean) => {
  showAllNotes.value = false
  currentVersion.value = result.currentVersion || currentVersion.value
  latestVersion.value = result.latestVersion || ''
  releaseDate.value = result.releaseDate || ''
  notes.value = result.notes || []
  updateDownloadUrl.value = result.url || ''
  downloadedFilePath.value = result.downloadedFilePath || ''
  downloadProgress.value = result.downloadedFilePath ? 100 : 0
  updateStatusMessage.value = ''
  if (manual) {
    showUpdateDialog.value = true
  }

  if (!result.enabled) {
    updateStatus.value = 'idle'
    if (manual) {
      feedback.info('当前没有可用更新', { toast: true })
    }
    return
  }

  if (result.hasUpdate) {
    updateStatus.value = result.downloadedFilePath ? 'downloaded' : 'available'
    if (manual) {
      if (!result.url) {
        feedback.warning('检测到新版本，但更新配置不完整，暂时无法下载')
      }
    }
    return
  }

  updateStatus.value = 'up_to_date'
  if (manual) {
    feedback.success('当前已是最新版本', { toast: true })
  }
}

const runUpdateCheck = async (manual: boolean) => {
  const previousStatus = updateStatus.value
  updateStatus.value = 'checking'
  updateStatusMessage.value = ''
  try {
    const result = await window.electron?.ipcRenderer.invoke('update:check', {
      reason: manual ? 'manual' : 'startup',
    }) as UpdateCheckResult
    if (!result) {
      throw new Error('未收到更新检查结果')
    }
    applyUpdateResult(result, manual)
  } catch (error: any) {
    if (manual) {
      showUpdateDialog.value = true
      updateStatus.value = 'error'
      updateStatusMessage.value = error instanceof Error ? error.message : String(error)
    } else {
      updateStatus.value =
        previousStatus === 'downloaded'
          ? 'downloaded'
          : previousStatus === 'available'
            ? 'available'
            : 'idle'
      updateStatusMessage.value = ''
    }
    if (manual) {
      feedback.error(formatActionError('检查更新', error))
    }
  }
}

const handleManualUpdateCheck = async () => {
  showUpdateDialog.value = true
  await runUpdateCheck(true)
}

const handleUpdateIconClick = async () => {
  if (updateStatus.value === 'available' || updateStatus.value === 'downloading' || updateStatus.value === 'downloaded') {
    showUpdateDialog.value = true
    return
  }
  if (updateStatus.value === 'checking') {
    showUpdateDialog.value = true
    return
  }
  await runUpdateCheck(true)
}

const startUpdateDownload = async () => {
  if (!updateDownloadUrl.value) {
    feedback.warning('当前更新源缺少安装包地址，暂时无法下载')
    return
  }
  showUpdateDialog.value = true
  updateStatus.value = 'downloading'
  updateStatusMessage.value = ''
  downloadProgress.value = 0
  try {
    const result = await window.electron?.ipcRenderer.invoke('update:startDownload') as UpdateCheckResult
    if (result?.downloadedFilePath) {
      downloadedFilePath.value = result.downloadedFilePath
    }
  } catch (error: any) {
    updateStatus.value = 'available'
    updateStatusMessage.value = error instanceof Error ? error.message : String(error)
    feedback.error(formatActionError('下载更新包', error))
  }
}

const installDownloadedUpdate = async () => {
  if (!downloadedFilePath.value) {
    feedback.warning('请先下载更新包，再执行安装')
    return
  }
  try {
    await feedback.confirmWarning({
      title: '安装新版本',
      message: '安装将关闭当前软件并启动安装程序，是否继续？',
      confirmButtonText: '立即安装',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await window.electron?.ipcRenderer.invoke('update:installDownloaded')
  } catch (error: any) {
    feedback.error(formatActionError('启动安装包', error))
  }
}

const loadUpdateHistory = async (force = false) => {
  if (historyLoading.value) return
  if (historyLoaded.value && !force) return

  historyLoading.value = true
  historyError.value = ''
  try {
    const result = await window.electron?.ipcRenderer.invoke('update:getHistory') as UpdateHistoryEntry[]
    updateHistory.value = Array.isArray(result) ? result : []
    historyLoaded.value = true
  } catch (error: any) {
    historyError.value = error instanceof Error ? error.message : String(error)
  } finally {
    historyLoading.value = false
  }
}

const toggleHistoryPanel = async () => {
  showHistoryPanel.value = !showHistoryPanel.value
  if (showHistoryPanel.value) {
    await loadUpdateHistory()
  }
}

const openReleasePage = async (url: string) => {
  try {
    await window.electron?.ipcRenderer.invoke('open_external', url)
  } catch (error: any) {
    feedback.error(formatActionError('打开发布页', error))
  }
}

watch(developerMode, (val) => {
  localStorage.setItem('developer_mode', val ? 'true' : 'false')
})

watch(showOptimizationDetails, (val) => {
  localStorage.setItem('show_optimization_details', val ? 'true' : 'false')
})

watch(frontendResetEpoch, () => {
  Object.assign(userProfile, createDefaultUserProfile())
  showSettings.value = false
  showDevDialog.value = false
  developerMode.value = false
  showOptimizationDetails.value = false
  showHistoryPanel.value = false
  historyLoading.value = false
  historyLoaded.value = false
  historyError.value = ''
  updateHistory.value = []
  showAllNotes.value = false
})

onMounted(async () => {
  try {
    const version = await window.electron?.ipcRenderer.invoke('update:getCurrentVersion')
    if (typeof version === 'string' && version.trim()) {
      currentVersion.value = version.trim()
    }
  } catch (error) {
    currentVersion.value = currentVersion.value || '--'
  }

  const removeProgressListener = window.electron?.ipcRenderer.on('update-progress', (_event: any, payload: any) => {
    updateStatus.value = 'downloading'
    if (typeof payload?.percent === 'number' && Number.isFinite(payload.percent)) {
      downloadProgress.value = payload.percent
    }
    if (typeof payload?.version === 'string' && payload.version.trim()) {
      latestVersion.value = payload.version.trim()
    }
  })

  const removeDownloadedListener = window.electron?.ipcRenderer.on('update-downloaded', (_event: any, payload: any) => {
    updateStatus.value = 'downloaded'
    downloadProgress.value = 100
    downloadedFilePath.value = typeof payload?.filePath === 'string' ? payload.filePath : ''
    if (typeof payload?.version === 'string' && payload.version.trim()) {
      latestVersion.value = payload.version.trim()
    }
    feedback.success('更新包下载完成，可以立即安装')
  })

  const removeErrorListener = window.electron?.ipcRenderer.on('update-error', (_event: any, payload: any) => {
    if (updateStatus.value === 'downloading' || showUpdateDialog.value) {
      updateStatus.value = 'error'
      updateStatusMessage.value = typeof payload?.message === 'string' ? payload.message : '更新流程发生异常'
    }
  })

  void Promise.resolve().then(() => runUpdateCheck(false))

  void removeProgressListener
  void removeDownloadedListener
  void removeErrorListener
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
  const item = navItems.find(i => route.path.startsWith(i.path))
  return item ? item.label : 'Easy Exam'
})

const showWizard = computed(() => {
  return workflowSteps.some(s => route.path.startsWith(s.path))
})

const keepAliveInclude = ['PrintingPage', 'RegistrationPage']

function getKeepAliveKey(currentRoute: any) {
  const baseKey = String(currentRoute.name || currentRoute.path)
  if (currentRoute.meta?.preserveOnAppReset) return baseKey
  return `${baseKey}:${frontendResetEpoch.value}`
}

function isNavItemDisabled(path: string) {
  if (!licenseStore.valid && path !== "/registration") {
    return true
  }
  return false
}

function getStepClass(path: string) {
  if (route.path.startsWith(path)) {
    return 'bg-primary-50 text-primary-700 ring-1 ring-primary-200'
  }
  // Check if passed (simple check based on array index order in real app, here simplified)
  const currentIndex = workflowSteps.findIndex(s => route.path.startsWith(s.path))
  const stepIndex = workflowSteps.findIndex(s => s.path === path)
  
  if (stepIndex < currentIndex) {
    return 'text-slate-500 bg-slate-50'
  }
  return 'text-slate-400'
}

function getDotClass(path: string) {
  if (route.path.startsWith(path)) return 'bg-primary-500'
  const currentIndex = workflowSteps.findIndex(s => route.path.startsWith(s.path))
  const stepIndex = workflowSteps.findIndex(s => s.path === path)
  if (stepIndex < currentIndex) return 'bg-slate-400'
  return 'bg-slate-200'
}
</script>

<style>
/* Global Scrollbar */
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

/* Page Transitions */
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

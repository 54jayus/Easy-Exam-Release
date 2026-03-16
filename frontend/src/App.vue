<template>
  <div v-if="isStandaloneAssistant" class="h-screen w-screen bg-transparent flex flex-col overflow-hidden">
    <router-view />
  </div>
  <div v-else class="flex h-screen w-full bg-surface-50 overflow-hidden font-sans text-slate-900">
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
              <p class="text-primary-300 text-xs">v3.2.0316</p>
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
          <el-button link class="!text-primary-400 hover:!text-white" @click="showSettings = true">
            <el-icon><Setting /></el-icon>
          </el-button>
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
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <!-- Global AI Assistant -->
    <!-- <AiAssistant v-if="!isStandaloneAssistant" /> -->
    
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
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLicenseStore } from "./stores/license"
import AiAssistant from "@/components/AiAssistant.vue"
import { 
  Monitor, Notebook, User, School, Printer, 
  QuestionFilled, Setting, DataBoard, Key, Check, Clock
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

const route = useRoute()
const router = useRouter()
const licenseStore = useLicenseStore()

// Once backend finishes checking, redirect to /registration if license is invalid
watch(() => licenseStore.checked, (checked) => {
  if (checked && !licenseStore.valid && route.path !== '/registration') {
    router.replace('/registration')
  }
})

const currentDateTime = ref(dayjs().format('YYYY年MM月DD日 dddd HH:mm'))

onMounted(() => {
  setInterval(() => {
    currentDateTime.value = dayjs().format('YYYY年MM月DD日 dddd HH:mm')
  }, 60000)
})

const showSettings = ref(false)
const avatarSeeds = ['Admin', 'Felix', 'Aneka', 'Zack', 'Milo', 'Bandit', 'Tinker', 'Cali', 'Coco', 'Bear']

const userProfile = reactive({
  name: '管理员',
  email: '',
  avatarSeed: 'Cali',
  avatar: 'https://api.dicebear.com/9.x/notionists/svg?seed=Cali&backgroundColor=e1f5fe,ffecb3,ffe082,ffcdd2,f8bbd0,e1bee7,d1c4e9,c5cae9,bbdefb,b3e5fc,b2ebf2,b2dfdb,c8e6c9,dcedc8,f0f4c3,fff9c4'
})

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

watch(developerMode, (val) => {
  localStorage.setItem('developer_mode', val ? 'true' : 'false')
})

watch(showOptimizationDetails, (val) => {
  localStorage.setItem('show_optimization_details', val ? 'true' : 'false')
})


const isStandaloneAssistant = computed(() => {
  return route.path === '/assistant' || route.query.window === 'assistant' || window.location.hash.includes('assistant')
})

// --- Context Sharing Logic ---
const updateContext = () => {
  if (isStandaloneAssistant.value) return // Assistant window doesn't report its own context

  // Wait for DOM to likely be ready if called immediately
  requestAnimationFrame(() => {
    const pageTitle = document.title
    const currentPath = route.path
    const headerText = document.querySelector('header h2')?.textContent || ''
    
    // Try to find primary buttons or actions
    const buttons = Array.from(document.querySelectorAll('button'))
      .filter(b => b.offsetParent !== null) // Visible buttons
      .slice(0, 8) // Grab a few more
      .map(b => b.textContent?.trim())
      .filter(Boolean)
      .join(', ')

    const context = `Current Page: ${headerText || pageTitle} (Path: ${currentPath})\nVisible Actions: ${buttons}`
    
    if (window.electron) {
      window.electron.ipcRenderer.send('update-ui-context', context)
    }
  })
}

// Watch route changes to update context
watch(() => route.path, () => {
  setTimeout(updateContext, 500) // Small delay for DOM update
}, { immediate: true })

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

<template>
  <div class="fixed inset-0 z-[3000] flex items-center justify-center p-3 animate-fade-in bg-slate-900/20 backdrop-blur-[2px]">
    <div
      class="w-[420px] bg-white rounded-2xl shadow-[0_24px_60px_rgba(15,23,42,0.22)] ring-1 ring-slate-200/70 overflow-hidden animate-slide-up"
      @mousedown="startDrag"
    >
      <!-- Header -->
      <div class="px-6 pt-6 pb-3">
        <div class="flex items-start gap-4">
          <!-- Tray icon illustration -->
          <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center flex-shrink-0 shadow-sm">
            <svg class="w-7 h-7 text-primary-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="4" width="20" height="16" rx="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 10h20" stroke-linecap="round"/>
              <circle cx="12" cy="16" r="1.5" fill="currentColor" stroke="none"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-base font-bold text-slate-800">关闭窗口提示</h3>
            <p class="mt-1.5 text-sm text-slate-500 leading-relaxed">
              程序不会退出，将最小化到系统托盘继续运行。
            </p>
          </div>
        </div>
      </div>

      <!-- Tips -->
      <div class="px-6 pb-4">
        <div class="bg-slate-50 rounded-xl px-4 py-3 space-y-2">
          <p class="flex items-start gap-2.5 text-xs text-slate-500">
            <svg class="w-3.5 h-3.5 text-primary-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
            <span>右下角托盘运行，随时可打开主界面</span>
          </p>
          <p class="flex items-start gap-2.5 text-xs text-slate-500">
            <svg class="w-3.5 h-3.5 text-primary-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
            <span>双击托盘图标可重新打开窗口</span>
          </p>
          <p class="flex items-start gap-2.5 text-xs text-slate-500">
            <svg class="w-3.5 h-3.5 text-primary-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
            <span>右键托盘图标可完全退出程序</span>
          </p>
        </div>
      </div>

      <!-- Divider -->
      <div class="mx-6 border-t border-slate-100"></div>

      <!-- Footer -->
      <div class="px-6 py-3.5 flex items-center justify-between">
        <!-- Checkbox -->
        <label class="flex items-center gap-2 cursor-pointer group select-none">
          <input
            v-model="dontShowAgain"
            type="checkbox"
            class="w-4 h-4 rounded border-2 border-slate-300 text-primary-500 focus:ring-primary-500 focus:ring-offset-0 cursor-pointer accent-primary-500"
          />
          <span class="text-xs text-slate-400 group-hover:text-slate-600 transition-colors duration-150">不再提示</span>
        </label>

        <!-- Buttons -->
        <div class="flex items-center gap-2">
          <button
            class="px-4 py-2 text-sm font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all duration-150"
            @click="handleExit"
          >
            退出程序
          </button>
          <button
            class="px-5 py-2 text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 active:bg-primary-700 rounded-lg transition-all duration-150 shadow-sm shadow-primary-500/25"
            @click="handleMinimize"
          >
            最小化到托盘
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  useIpc?: boolean
}>(), {
  useIpc: true,
})

const emit = defineEmits<{
  minimize: [payload: { dontShowAgain: boolean }]
  exit: [payload: { dontShowAgain: boolean }]
}>()

const dontShowAgain = ref(false)

const handleMinimize = () => {
  const payload = { dontShowAgain: dontShowAgain.value }
  if (props.useIpc) {
    window.electron?.ipcRenderer.send('tray-dialog-response', {
      exitRequested: false,
      dontShowAgain: dontShowAgain.value,
    })
    return
  }
  emit('minimize', payload)
}

const handleExit = () => {
  const payload = { dontShowAgain: dontShowAgain.value }
  if (props.useIpc) {
    window.electron?.ipcRenderer.send('tray-dialog-response', {
      exitRequested: true,
      dontShowAgain: dontShowAgain.value,
    })
    return
  }
  emit('exit', payload)
}

// Enable window dragging
const startDrag = (e: MouseEvent) => {
  if ((e.target as HTMLElement).closest('button, label, input')) return
}

// Handle keyboard shortcuts
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    handleMinimize()
  } else if (e.key === 'Enter') {
    handleMinimize()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}

.animate-slide-up {
  animation: slideUp 0.25s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>

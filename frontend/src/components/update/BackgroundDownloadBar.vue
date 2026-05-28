<template>
  <transition name="slide-up">
    <div
      v-if="visible"
      ref="barRef"
      class="fixed z-[200] w-[480px] max-w-[calc(100vw-2rem)]"
      :style="positionStyle"
    >
      <div
        class="rounded-2xl border bg-white/95 backdrop-blur-md shadow-xl shadow-slate-950/10 overflow-hidden"
        :class="isReady ? 'border-emerald-200' : 'border-slate-200'"
      >
        <!-- Progress track -->
        <div
          v-if="!isReady"
          class="h-1 bg-slate-100"
        >
          <div
            class="h-full bg-primary-500 transition-[width] duration-500 ease-out"
            :style="{ width: `${smoothProgress}%` }"
          />
        </div>
        <div
          v-else
          class="h-1 bg-emerald-100"
        >
          <div class="h-full bg-emerald-500 w-full" />
        </div>

        <!-- Content -->
        <div
          class="flex items-center gap-3 px-4 py-2.5"
          :class="isDragging ? 'cursor-grabbing' : 'cursor-grab'"
          @mousedown="onDragStart"
        >
          <!-- Icon -->
          <div
            class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            :class="isReady ? 'bg-emerald-50' : 'bg-primary-50'"
          >
            <svg
              v-if="isReady"
              class="w-4 h-4 text-emerald-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M20 6L9 17l-5-5" />
            </svg>
            <svg
              v-else
              class="w-4 h-4 text-primary-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </div>

          <!-- Text -->
          <div class="flex-1 min-w-0 select-none">
            <div class="text-sm font-medium text-slate-800">
              {{ isReady ? '更新包已下载完成' : isPaused ? '下载已暂停' : '正在后台下载更新包' }}
            </div>
            <div class="text-xs text-slate-500 mt-0.5">
              <span v-if="version">v{{ version }}</span>
              <span v-if="version && !isReady"> · </span>
              <span v-if="!isReady">{{ smoothProgress.toFixed(1) }}%</span>
              <span v-if="isReady"> · 点击安装即可完成更新</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1.5 flex-shrink-0" @mousedown.stop>
            <template v-if="isReady">
              <el-button type="primary" size="small" @click="$emit('install')">
                立即安装
              </el-button>
            </template>
            <template v-else>
              <!-- Pause / Resume -->
              <button
                class="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                :title="isPaused ? '继续下载' : '暂停下载'"
                @click="isPaused ? $emit('resume') : $emit('pause')"
              >
                <!-- Pause icon -->
                <svg
                  v-if="!isPaused"
                  class="w-3.5 h-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <rect x="6" y="4" width="4" height="16" />
                  <rect x="14" y="4" width="4" height="16" />
                </svg>
                <!-- Resume icon -->
                <svg
                  v-else
                  class="w-3.5 h-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
              </button>
            </template>
            <!-- Dismiss X -->
            <button
              class="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              title="关闭"
              @click="$emit('dismiss')"
            >
              <svg
                class="w-3.5 h-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, ref, toRef, watch, onBeforeUnmount } from 'vue'
import { useSmoothProgress } from '@/composables/useSmoothProgress'

const props = defineProps<{
  visible: boolean
  progress: number
  version: string
  isReady: boolean
  isPaused?: boolean
}>()

defineEmits<{
  install: []
  pause: []
  resume: []
  dismiss: []
}>()

const smoothProgress = useSmoothProgress(toRef(props, 'progress'))

// --- Drag ---
const barRef = ref<HTMLElement>()
const isDragging = ref(false)
const hasDragged = ref(false)
const pos = ref<{ x: number; y: number } | null>(null)
const dragOffset = ref({ x: 0, y: 0 })

const positionStyle = computed(() => {
  if (pos.value) {
    return { left: `${pos.value.x}px`, top: `${pos.value.y}px` }
  }
  // Default: centered at bottom
  return { left: '50%', bottom: '16px', transform: 'translateX(-50%)' }
})

function onDragStart(e: MouseEvent) {
  if (e.button !== 0) return
  const bar = barRef.value
  if (!bar) return

  // If not yet positioned explicitly, resolve current position
  if (!pos.value) {
    const rect = bar.getBoundingClientRect()
    pos.value = { x: rect.left, y: rect.top }
  }

  isDragging.value = true
  hasDragged.value = false
  dragOffset.value = {
    x: e.clientX - pos.value.x,
    y: e.clientY - pos.value.y,
  }

  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
  e.preventDefault()
}

function onDragMove(e: MouseEvent) {
  if (!isDragging.value) return
  hasDragged.value = true

  const bar = barRef.value
  if (!bar) return

  const barWidth = bar.offsetWidth
  const barHeight = bar.offsetHeight
  const maxX = window.innerWidth - barWidth - 8
  const maxY = window.innerHeight - barHeight - 8

  pos.value = {
    x: Math.max(8, Math.min(maxX, e.clientX - dragOffset.value.x)),
    y: Math.max(8, Math.min(maxY, e.clientY - dragOffset.value.y)),
  }
}

function onDragEnd() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
}

// Reset position when bar becomes visible (new download)
watch(() => props.visible, (v) => {
  if (v) pos.value = null
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
})
</script>

<style scoped>
.slide-up-enter-active {
  transition: opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-leave-active {
  transition: opacity 0.25s ease-in;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
}
</style>

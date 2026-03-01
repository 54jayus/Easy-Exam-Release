<template>
  <div 
    class="z-50 pointer-events-none"
    :class="mode === 'standalone' ? 'relative h-full w-full' : 'fixed bottom-6 right-6'"
  >
    <!-- Chat Window (Only in Standalone Mode) -->
    <transition name="chat-slide">
      <div 
        v-if="mode === 'standalone'"
        ref="chatWindowRef"
        :style="chatWindowStyle"
        class="bg-white/95 backdrop-blur-xl flex flex-col pointer-events-auto overflow-hidden ring-1 ring-black/5 rounded-2xl shadow-2xl"
        :class="mode === 'standalone' ? 'h-full w-full' : ''"
      >
        <!-- Header -->
        <div 
          ref="dragHandleRef"
          class="relative h-14 bg-gradient-to-r from-violet-600/90 to-indigo-600/90 backdrop-blur-md px-4 flex items-center justify-between flex-shrink-0 cursor-move select-none border-b border-white/10 drag-region"
        >
          <!-- Drag Handle Visual -->
          <div class="absolute top-2 left-1/2 -translate-x-1/2 w-12 h-1 bg-white/20 rounded-full backdrop-blur-sm hover:bg-white/30 transition-colors"></div>

          <div class="flex items-center gap-3 text-white pointer-events-none">
            <div class="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center backdrop-blur-md border border-white/10 shadow-inner">
              <Sparkles class="w-5 h-5 text-yellow-300" />
            </div>
            <div>
              <div class="font-bold text-sm leading-tight tracking-wide">AI 智能助手</div>
              <div class="text-[10px] text-indigo-100 leading-tight opacity-80 font-medium">Smart Assistant</div>
            </div>
          </div>
          <div class="flex items-center gap-1.5 pointer-events-auto" @mousedown.stop>
            <button 
              @click="clearHistory" 
              class="p-2 text-indigo-100 hover:text-white hover:bg-white/15 rounded-lg transition-all duration-200 active:scale-95"
              title="清空对话"
            >
              <Trash2 class="w-4 h-4" />
            </button>
            <button 
              @click="handleMinimize" 
              class="p-2 text-indigo-100 hover:text-white hover:bg-white/15 rounded-lg transition-all duration-200 active:scale-95"
              title="最小化"
            >
              <Minimize2 class="w-4 h-4" />
            </button>
            <button 
              @click="handleClose" 
              class="p-2 text-indigo-100 hover:text-white hover:bg-white/15 rounded-lg transition-all duration-200 active:scale-95"
              title="关闭"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Messages Area -->
        <div v-if="!isConfigured" class="flex-1 overflow-y-auto p-6 bg-slate-50/50 flex flex-col items-center justify-center space-y-6">
            <div class="text-center space-y-3">
              <div class="w-20 h-20 bg-white rounded-3xl shadow-xl shadow-indigo-100 flex items-center justify-center mx-auto mb-6 ring-1 ring-slate-100">
                <Settings2 class="w-10 h-10 text-indigo-500" />
              </div>
              <h3 class="text-xl font-bold text-slate-800 tracking-tight">配置 AI 助手</h3>
              <p class="text-sm text-slate-500 font-medium">初次使用需配置 API Key</p>
            </div>

          <div class="w-full max-w-xs space-y-5">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-500 uppercase tracking-wider ml-1">厂商</label>
              <el-input model-value="智谱清言" disabled readonly size="large" class="!text-slate-700 shadow-sm">
                <template #prefix><span class="text-lg mr-1">🏢</span></template>
              </el-input>
            </div>
            
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-500 uppercase tracking-wider ml-1">模型</label>
              <el-input model-value="GLM-4.6V-Flash" disabled readonly size="large" class="!text-slate-700 shadow-sm">
                <template #prefix><span class="text-lg mr-1">🤖</span></template>
              </el-input>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-slate-500 uppercase tracking-wider ml-1">API Key</label>
              <el-input 
                v-model="configApiKey" 
                placeholder="请输入 API Key" 
                type="password" 
                show-password 
                size="large"
                class="shadow-sm focus-within:shadow-md transition-shadow" 
              />
              <div class="text-right pt-1">
                <a 
                  href="https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys" 
                  target="_blank" 
                  class="text-[11px] font-medium text-indigo-600 hover:text-indigo-700 hover:underline inline-flex items-center gap-1 transition-colors"
                >
                  获取 API Key <TopRight class="w-3 h-3" />
                </a>
              </div>
            </div>

            <el-button 
              type="primary" 
              class="!w-full !rounded-xl !h-11 !text-base !font-semibold !shadow-lg !shadow-indigo-500/20 hover:!shadow-indigo-500/30 transition-all active:!scale-[0.98]" 
              :loading="configLoading"
              @click="handleConfigure"
              color="#4f46e5"
            >
              测试并保存
            </el-button>
          </div>
        </div>

        <div 
          v-else
          ref="messagesRef" 
          class="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 scroll-smooth custom-scrollbar"
        >
          <!-- Welcome Message -->
          <div v-if="messages.length === 0" class="text-center py-12 px-6">
            <div class="w-20 h-20 bg-indigo-50/50 rounded-3xl flex items-center justify-center mx-auto mb-6 ring-1 ring-indigo-100/50 shadow-sm">
              <Bot class="w-10 h-10 text-indigo-500" />
            </div>
            <h3 class="text-lg font-bold text-slate-800 mb-3 tracking-tight">有什么可以帮您？</h3>
            <p class="text-sm text-slate-500 max-w-[240px] mx-auto leading-relaxed">
              我可以协助您进行排考、解答系统使用问题或提供操作建议。
            </p>
            
            <!-- Quick Suggestions -->
            <div class="mt-8 grid grid-cols-1 gap-2.5">
              <button 
                v-for="(suggestion, idx) in ['如何导入监考教师？', '排考规则怎么设置？', '导出考场编排表']" 
                :key="idx"
                @click="inputText = suggestion; handleSend()"
                class="text-xs text-slate-600 bg-white border border-slate-200 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50/30 py-2.5 px-4 rounded-xl transition-all duration-200 text-left w-full flex items-center justify-between group"
              >
                {{ suggestion }}
                <span class="opacity-0 group-hover:opacity-100 transition-opacity text-indigo-400">→</span>
              </button>
            </div>
          </div>

          <!-- Chat Items -->
          <div 
            v-for="(msg, index) in messages" 
            :key="index" 
            class="flex gap-3"
            :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
          >
            <!-- Avatar -->
            <div 
              class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs border"
              :class="msg.role === 'user' ? 'bg-indigo-100 text-indigo-600 border-indigo-200' : 'bg-white text-emerald-600 border-slate-100 shadow-sm'"
            >
              <User v-if="msg.role === 'user'" class="w-4 h-4" />
              <Bot v-else class="w-4 h-4" />
            </div>

            <!-- Content -->
            <div 
              class="max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm leading-relaxed break-words"
              :class="[
                msg.role === 'user' 
                  ? 'bg-gradient-to-br from-indigo-600 to-violet-600 text-white rounded-tr-none shadow-indigo-500/20' 
                  : 'bg-white text-slate-700 rounded-tl-none border border-slate-100/60 shadow-slate-200/50 ring-1 ring-slate-50'
              ]"
            >
              <div v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)" class="prose prose-sm max-w-none prose-p:my-1.5 prose-p:leading-6 prose-pre:my-2 prose-pre:bg-slate-50 prose-pre:text-slate-600 prose-pre:rounded-lg prose-pre:border prose-pre:border-slate-100"></div>
              <div v-else>{{ msg.content }}</div>
            </div>
          </div>

          <!-- Loading Indicator -->
          <div v-if="loading" class="flex gap-3">
            <div class="w-8 h-8 rounded-full bg-white text-emerald-600 border border-slate-100 shadow-sm flex items-center justify-center">
              <Bot class="w-4 h-4" />
            </div>
            <div class="bg-white rounded-2xl rounded-tl-none px-4 py-3 border border-slate-100 shadow-sm flex items-center gap-1.5">
              <div class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="p-4 bg-white border-t border-slate-100">
          <div class="relative group">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="1"
              :autosize="{ minRows: 1, maxRows: 4 }"
              placeholder="输入您的问题..."
              resize="none"
              class="custom-chat-input"
              @keydown.enter.prevent="handleEnter"
            />
            <button 
              @click="handleSend"
              :disabled="!inputText.trim() || loading"
              class="absolute right-2 bottom-1.5 p-2 bg-gradient-to-br from-indigo-500 to-indigo-600 text-white rounded-xl hover:from-indigo-400 hover:to-indigo-500 disabled:opacity-50 disabled:from-slate-400 disabled:to-slate-400 transition-all duration-200 flex items-center justify-center shadow-lg shadow-indigo-500/20 active:scale-95 active:shadow-none"
            >
              <Send class="w-4 h-4" />
            </button>
          </div>
          <div class="text-[10px] text-slate-400 mt-2.5 flex items-center justify-between px-1 font-medium tracking-wide">
            <span>Enter 发送，Shift + Enter 换行</span>
            <span class="flex items-center gap-1 opacity-80">基于 <span class="font-bold text-indigo-500">Zhipu AI</span></span>
          </div>
        </div>
        
      </div>
    </transition>

    <!-- Floating Trigger Button (Only in Embedded Mode) -->
    <button 
      v-if="mode !== 'standalone'"
      @click="toggleAssistant"
      class="group pointer-events-auto absolute bottom-0 right-0 flex items-center justify-center h-14 rounded-full shadow-lg shadow-indigo-500/30 transition-all duration-300 hover:scale-105 active:scale-95 z-50 bg-gradient-to-br from-indigo-500 to-indigo-600 hover:from-indigo-400 hover:to-indigo-500 text-white ring-2 ring-white/20"
      :class="isOpen ? 'w-14 !bg-slate-700 !hover:bg-slate-800 !text-slate-300 !from-transparent !to-transparent' : 'w-auto px-5 gap-2'"
    >
      <div class="relative w-5 h-5 flex items-center justify-center">
        <transition name="icon-morph">
          <component 
            :is="isOpen ? X : Sparkles" 
            class="w-5 h-5 absolute" 
            :key="isOpen ? 'close' : 'open'"
          />
        </transition>
      </div>
      
      <span v-if="!isOpen" class="font-bold text-sm whitespace-nowrap overflow-hidden">AI 助手</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, computed, onUnmounted } from 'vue'
import { 
  Bot, MessageSquareMore, Sparkles, Settings2, Minimize2, Trash2, Send, X, ExternalLink
} from 'lucide-vue-next'
import { marked } from 'marked'
import { pythonBackend } from '@/lib/pythonBackend'
import { createLogger } from '@/lib/logger'
import { useRoute } from 'vue-router'
import { useDraggable } from '@vueuse/core'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  mode?: 'embedded' | 'standalone'
  initialOpen?: boolean
}>()

const logger = createLogger('AiAssistant')

const route = useRoute()
const isOpen = ref(props.initialOpen || false)
const loading = ref(false)
const isConfigured = ref(false)
const configApiKey = ref('')
const configLoading = ref(false)
const inputText = ref('')
const messagesRef = ref<HTMLElement | null>(null)
const chatWindowRef = ref<HTMLElement | null>(null)
const dragHandleRef = ref<HTMLElement | null>(null)

// Check configuration on mount
onMounted(async () => {
  try {
    const res = await pythonBackend.request('assistant.checkConfig')
    isConfigured.value = res.configured
  } catch (e) {
    logger.error('检查助手配置失败', e)
  }
  
  if (props.mode === 'standalone') {
    // Listen for assistant closed event from main process if needed
    // And setup window dragging
    setupWindowDrag()
  } else {
    // Listen for assistant window status
    if (window.electron) {
      // Reset state if window is closed by user or system
      window.electron.ipcRenderer.on('assistant:closed', () => {
        isOpen.value = false
      })
    }
  }
})

const setupWindowDrag = () => {
  const handle = dragHandleRef.value
  if (!handle) return

  let isDragging = false
  let startX = 0
  let startY = 0

  handle.addEventListener('mousedown', (e) => {
    isDragging = true
    startX = e.screenX
    startY = e.screenY
  })

  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return
    const deltaX = e.screenX - startX
    const deltaY = e.screenY - startY
    
    // Call electron to move window
    window.electron?.ipcRenderer.invoke('assistant:move', { x: deltaX, y: deltaY })
    
    startX = e.screenX
    startY = e.screenY
  })

  window.addEventListener('mouseup', () => {
    isDragging = false
  })
}

const handleMinimize = () => {
  if (props.mode === 'standalone') {
    window.electron?.ipcRenderer.invoke('assistant:minimize')
  } else {
    isOpen.value = false
  }
}

const handleClose = () => {
  if (props.mode === 'standalone') {
    window.electron?.ipcRenderer.invoke('assistant:close')
  } else {
    isOpen.value = false
  }
}

const toggleAssistant = async () => {
  if (!window.electron) {
    ElMessage.error('无法调用系统窗口功能，请确保在客户端中运行')
    return
  }

  if (isOpen.value) {
    // Currently open, so minimize it
    try {
      await window.electron.ipcRenderer.invoke('assistant:minimize')
      // We don't set isOpen = false here immediately, because minimize doesn't mean closed.
      // But the user asked for "click X to minimize".
      // Visually, if it's minimized, should the button go back to "Open"?
      // The user said "click X to minimize independent window". 
      // Usually "minimize" means it's still running but hidden.
      // If I set isOpen = false, the icon becomes Sparkles. Next click calls openAssistantWindow -> assistant:open -> shows window.
      // This seems correct flow: Minimize -> Hidden (effectively closed from view) -> Click to Show.
      isOpen.value = false
    } catch (e) {
      logger.error('最小化助手窗口失败', e)
    }
  } else {
    // Currently closed/minimized, so open it
    await openAssistantWindow()
    isOpen.value = true
  }
}

const openAssistantWindow = async () => {
  try {
    if (!window.electron) {
      logger.error('未检测到 Electron 环境')
      ElMessage.error('无法调用系统窗口功能，请确保在客户端中运行')
      return
    }
    await window.electron.ipcRenderer.invoke('assistant:open')
  } catch (e) {
    logger.error('打开助手窗口失败', e)
    ElMessage.error('打开独立窗口失败')
  }
}

const handleConfigure = async () => {
  if (!configApiKey.value.trim()) {
    ElMessage.warning('请输入 API Key')
    return
  }
  
  configLoading.value = true
  try {
    const res = await pythonBackend.request('assistant.configure', {
      apiKey: configApiKey.value.trim()
    })

    if (res.success) {
      isConfigured.value = true
      ElMessage.success('配置成功')
    } else {
      ElMessage.error(res.error || '配置失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '配置请求异常')
  } finally {
    configLoading.value = false
  }
}

// Dragging Logic
const { x, y } = useDraggable(chatWindowRef, {
  handle: dragHandleRef,
  initialValue: { x: window.innerWidth - 380 - 24, y: window.innerHeight - 600 - 90 },
  preventDefault: true,
  disabled: props.mode === 'standalone' // Disable vueuse draggable in standalone mode
})

const chatWindowStyle = computed(() => {
  if (props.mode === 'standalone') {
    return {
      width: '100%',
      height: '100%',
      top: '0',
      left: '0',
      borderRadius: '16px', // Rounded corners for standalone window
    }
  }
  return {
    position: 'fixed' as const,
    left: `${x.value}px`,
    top: `${y.value}px`,
    width: '380px', // Default width
    height: '600px', // Default height
  }
})

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const STORAGE_KEY = 'ai_assistant_history'

// Load history from local storage
onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      messages.value = JSON.parse(saved)
    }
  } catch (e) {
    logger.warn('读取聊天记录失败', e)
  }
})

// Auto scroll to bottom
const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

watch(() => messages.value.length, scrollToBottom)
watch(() => loading.value, scrollToBottom)
// Save history on change
watch(() => messages.value, (newVal) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newVal))
  } catch (e) {
    logger.warn('保存聊天记录失败', e)
  }
}, { deep: true })

const toggleOpen = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    scrollToBottom()
  }
}

const clearHistory = () => {
  messages.value = []
  localStorage.removeItem(STORAGE_KEY)
}

const renderMarkdown = (text: string) => {
  try {
    return marked.parse(text)
  } catch (e) {
    return text
  }
}

const handleEnter = (e: KeyboardEvent) => {
  if (e.shiftKey) return
  handleSend()
}

const getUiContext = async () => {
  // If in standalone mode, fetch context from main process
  if (props.mode === 'standalone') {
    if (window.electron) {
      try {
        const context = await window.electron.ipcRenderer.invoke('get-ui-context')
        return context || "主窗口未连接"
      } catch (e) {
        logger.warn('获取主窗口上下文失败', e)
        return "获取上下文失败"
      }
    }
    return "独立窗口模式（未连接）"
  }

  // Simple extraction of page title and key elements (Embedded Mode)
  const pageTitle = document.title
  const currentPath = route.path
  
  // Try to find active step or header
  const headerText = document.querySelector('header h2')?.textContent || ''
  
  // Try to find primary buttons
  const buttons = Array.from(document.querySelectorAll('button'))
    .filter(b => b.offsetParent !== null) // Visible buttons
    .slice(0, 5)
    .map(b => b.textContent?.trim())
    .filter(Boolean)
    .join(', ')

  return `当前页面：${headerText || pageTitle}（路径：${currentPath}）\n可见操作：${buttons}`
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  // Add user message
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true

  try {
    const history = messages.value.slice(0, -1).map(m => ({
      role: m.role,
      content: m.content
    }))

    const uiContext = await getUiContext()

    const res = await pythonBackend.request('assistant.generateReply', {
      userText: text,
      history,
      uiContextText: uiContext,
      attachments: []
    }, 60000) // 60s timeout

    messages.value.push({ role: 'assistant', content: res.reply })
  } catch (e: any) {
    messages.value.push({ 
      role: 'assistant', 
      content: `请求失败：${e.message || '未知错误'}` 
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
  transform-origin: bottom right;
}

:deep(.custom-chat-input .el-textarea__inner) {
  padding-right: 40px;
  background-color: #f8fafc;
  border-color: transparent;
  border-radius: 0.75rem;
  transition: all 0.2s;
  box-shadow: none !important;
}

:deep(.custom-chat-input .el-textarea__inner:focus) {
  background-color: #fff;
  border-color: #e2e8f0;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

/* Icon Morph Transition */
.icon-morph-enter-active,
.icon-morph-leave-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: absolute;
}

.icon-morph-enter-from {
  opacity: 0;
  transform: rotate(-180deg) scale(0.5);
}

.icon-morph-leave-to {
  opacity: 0;
  transform: rotate(180deg) scale(0.5);
}

.icon-morph-enter-to,
.icon-morph-leave-from {
  opacity: 1;
  transform: rotate(0) scale(1);
}
</style>

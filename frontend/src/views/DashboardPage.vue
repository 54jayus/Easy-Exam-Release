<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
    <!-- Header Section -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Welcome Card -->
      <div class="md:col-span-2 relative overflow-hidden rounded-3xl bg-white/80 backdrop-blur-xl p-8 border border-white/20 shadow-sm group">
        <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-primary-100/50 to-purple-100/50 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
        <div class="relative z-10">
          <div class="flex items-start justify-between">
            <div>
              <h1 class="text-3xl font-bold text-slate-900 tracking-tight mb-2">考务指挥舱</h1>
            </div>
            <div class="hidden md:block">
              <span class="inline-flex items-center px-3 py-1 rounded-full bg-primary-50 text-primary-600 text-xs font-semibold border border-primary-100">
                <span class="w-2 h-2 rounded-full bg-primary-500 mr-2 animate-pulse"></span>
                系统运行正常
              </span>
            </div>
          </div>
          <div class="mt-8 flex gap-4">
             <el-button type="primary" size="large" round class="!px-8 shadow-lg shadow-primary-500/20" @click="$router.push('/subjects')">
               开始工作
               <el-icon class="ml-2"><ArrowRight /></el-icon>
             </el-button>
             <el-button size="large" round class="!bg-white/50 backdrop-blur" @click="$router.push('/help')">
               使用指南
             </el-button>
             
             <el-popconfirm
                title="确定要清空所有数据并重置系统吗？此操作不可恢复。"
                confirm-button-text="确定重置"
                cancel-button-text="取消"
                @confirm="handleReset"
                width="250"
             >
               <template #reference>
                 <el-button type="danger" size="large" round>
                   <el-icon class="mr-1"><Delete /></el-icon>
                   初始化系统
                 </el-button>
               </template>
             </el-popconfirm>
          </div>
        </div>
      </div>

      <!-- Countdown Card -->
      <div class="rounded-3xl bg-slate-900 text-white p-8 relative overflow-hidden shadow-lg flex flex-col justify-center">
        <div class="absolute top-0 right-0 w-32 h-32 bg-primary-500 rounded-full blur-[60px] opacity-40"></div>
        <div class="absolute bottom-0 left-0 w-24 h-24 bg-purple-500 rounded-full blur-[40px] opacity-30"></div>
        
        <div class="relative z-10">
          <div class="flex items-center gap-2 text-slate-400 text-sm font-medium mb-4 uppercase tracking-wider">
            <el-icon><Timer /></el-icon>
            <span>距离考试开始</span>
          </div>
          <div class="flex items-baseline gap-2">
             <span class="text-5xl font-mono font-bold tracking-tighter">{{ countdown.days }}</span>
             <span class="text-xl text-slate-400">天</span>
          </div>
          <div class="mt-4 pt-4 border-t border-white/10 flex justify-between text-xs text-slate-400 font-mono">
             <span>{{ countdown.time }}</span>
             <span>{{ countdown.targetDate }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats Grid (Bento Style) -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div v-for="(stat, index) in stats" :key="index" 
        class="bg-white/60 backdrop-blur-lg p-5 rounded-2xl border border-white/40 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 group cursor-default select-none"
        @dblclick="stat.path && $router.push(stat.path)">
        <div class="flex items-start justify-between mb-3">
          <div :class="`p-2.5 rounded-xl ${stat.bgClass} ${stat.textClass} group-hover:scale-110 transition-transform duration-300`">
            <component :is="stat.icon" class="w-5 h-5" />
          </div>
          <span v-if="stat.trend !== '--'" :class="['text-xs font-bold px-2 py-0.5 rounded-full flex items-center', stat.trendClass || 'bg-slate-100 text-slate-500']">
             <el-icon class="mr-0.5 transform rotate-45"><ArrowRight /></el-icon> {{ stat.trend }}
          </span>
        </div>
        <div class="text-2xl font-bold text-slate-900 tracking-tight">{{ stat.value }}</div>
        <div class="text-sm text-slate-500 font-medium mt-1">{{ stat.label }}</div>
      </div>
    </div>

    <!-- Main Workflow & Sidebar -->
    <div class="grid grid-cols-1 gap-6 items-stretch">
      <!-- Workflow Progress -->
      <div class="w-full bg-white/80 backdrop-blur-xl rounded-3xl p-8 border border-white/20 shadow-sm flex flex-col h-full">
        <div class="flex items-center justify-between mb-8">
          <div>
            <h2 class="text-xl font-bold text-slate-900">工作流进度</h2>
            <p class="text-slate-400 text-sm mt-1">按顺序完成以下步骤以生成考试安排</p>
          </div>
        </div>
        
        <div class="relative pl-4 flex-1">
          <!-- Connecting Line -->
          <div class="absolute left-8 top-4 bottom-12 w-0.5 bg-slate-100"></div>
          
          <div class="space-y-8 relative z-10">
            <div v-for="(step, index) in workflow" :key="index" 
                 class="group relative pl-12 transition-all duration-300 hover:pl-14 cursor-pointer"
                 @click="$router.push(step.path)">
              
              <!-- Step Indicator -->
              <div class="absolute left-0 top-0 w-8 h-8 flex items-center justify-center">
                 <div :class="`w-8 h-8 rounded-full flex items-center justify-center border-2 z-20 transition-all duration-300 bg-white ${
                    step.status === 'completed' ? 'border-primary-500 text-primary-500' :
                    step.status === 'current' ? 'border-primary-600 bg-primary-600 text-white shadow-lg shadow-primary-200 ring-4 ring-primary-50' :
                    'border-slate-200 text-slate-300 group-hover:border-slate-300'
                 }`">
                    <el-icon v-if="step.status === 'completed'" :size="14"><Check /></el-icon>
                    <span v-else class="text-xs font-bold">{{ index + 1 }}</span>
                 </div>
              </div>

              <!-- Content Card -->
              <div :class="`p-5 rounded-2xl border transition-all duration-300 ${
                  step.status === 'current' ? 'bg-primary-50/50 border-primary-100 shadow-sm' : 
                  'bg-white border-slate-100 hover:border-primary-200 hover:shadow-md'
              }`">
                <div class="flex items-center justify-between mb-2">
                  <h3 :class="`font-bold text-lg ${step.status === 'pending' ? 'text-slate-400' : 'text-slate-900'}`">
                    {{ step.title }}
                  </h3>
                  <el-tag :type="step.tagType" size="small" effect="light" round class="!font-semibold">
                    {{ step.statusLabel }}
                  </el-tag>
                </div>
                <p class="text-slate-500 text-sm mb-4 leading-relaxed">{{ step.desc }}</p>
                
                <div v-if="step.status === 'current' || step.status === 'completed'" class="flex items-center gap-3 animate-fade-in">
                  <el-button type="primary" size="small" round class="!px-4">
                    {{ step.status === 'completed' ? '重新配置' : '继续配置' }}
                  </el-button>
                  <span v-if="step.status === 'completed'" class="text-xs text-slate-400 flex items-center">
                    <el-icon class="mr-1"><Check /></el-icon> 已保存
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, onUnmounted, markRaw } from 'vue'
import { 
  Timer, Notebook, User, School, Printer, 
  ArrowRight, Check, ChatDotRound, Delete 
} from '@element-plus/icons-vue'
import { pythonBackend } from '../lib/pythonBackend'
import { ElMessage } from 'element-plus'

const iconMap: Record<string, any> = {
  'Notebook': markRaw(Notebook),
  'User': markRaw(User),
  'School': markRaw(School),
  'Printer': markRaw(Printer)
}

interface Subject {
  name: string
  exam_date: string
  exam_time: string
  duration_minutes: number
  remark: string
}

const countdown = reactive({
  days: '--',
  time: '--:--:--',
  targetDate: '--'
})

let timer: any = null

const updateCountdown = async () => {
  try {
    const res = await pythonBackend.request<{ subjects: Subject[] }>('subjects.list')
    if (!res.subjects || res.subjects.length === 0) {
      countdown.days = '0'
      countdown.time = '无待考科目'
      countdown.targetDate = '请先设置'
      return
    }

    const now = new Date()
    let closestExam: Date | null = null
    let minDiff = Infinity

    for (const sub of res.subjects) {
       const startTime = sub.exam_time.split('-')[0]
       if (!sub.exam_date || !startTime) continue
       
       // Parse date and time safely
       const [year, month, day] = sub.exam_date.split('-').map(Number)
       const [hour, minute] = startTime.split(':').map(Number)
       
       const examDateTime = new Date(year, month - 1, day, hour, minute)
       
       if (!isNaN(examDateTime.getTime()) && examDateTime > now) {
         const diff = examDateTime.getTime() - now.getTime()
         if (diff < minDiff) {
           minDiff = diff
           closestExam = examDateTime
         }
       }
    }

    if (closestExam) {
      const year = closestExam.getFullYear()
      const month = String(closestExam.getMonth() + 1).padStart(2, '0')
      const day = String(closestExam.getDate()).padStart(2, '0')
      countdown.targetDate = `${year}-${month}-${day}`
      
      const calculateTime = () => {
        const currentNow = new Date()
        const diff = closestExam!.getTime() - currentNow.getTime()
        
        if (diff <= 0) {
           countdown.days = '0'
           countdown.time = '00:00:00'
           return
        }

        const days = Math.floor(diff / (1000 * 60 * 60 * 24))
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
        const seconds = Math.floor((diff % (1000 * 60)) / 1000)
        
        countdown.days = days.toString()
        countdown.time = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
      }

      calculateTime()
      if (timer) clearInterval(timer)
      timer = setInterval(calculateTime, 1000)
    } else {
       countdown.days = '0'
       countdown.time = '无待考科目'
       countdown.targetDate = '已结束'
    }
  } catch (e) {
    console.error("更新倒计时失败", e)
  }
}

const stats = ref([
  { label: '考试科目', value: '--', icon: Notebook, bgClass: 'bg-sky-50', textClass: 'text-sky-600', trend: '--', trendClass: 'bg-slate-100 text-slate-500', path: '/subjects' },
  { label: '监考教师', value: '--', icon: User, bgClass: 'bg-emerald-50', textClass: 'text-emerald-600', trend: '--', trendClass: 'bg-slate-100 text-slate-500', path: '/proctoring' },
  { label: '考场编排', value: '--', icon: School, bgClass: 'bg-indigo-50', textClass: 'text-indigo-600', trend: '--', trendClass: 'bg-slate-100 text-slate-500', path: '/rooms' },
  { label: '资料打印', value: '--', icon: Printer, bgClass: 'bg-rose-50', textClass: 'text-rose-600', trend: '--', trendClass: 'bg-slate-100 text-slate-500', path: '/printing' },
])

const workflow = ref([
  { 
    title: '科目设置', 
    desc: '导入考试科目、时间及时长，自动检测冲突。', 
    status: 'pending', 
    statusLabel: '待开始',
    tagType: 'info',
    path: '/subjects'
  },
  { 
    title: '监考编排', 
    desc: '分配监考教师，支持多轮自动均衡算法。', 
    status: 'pending', 
    statusLabel: '待开始',
    tagType: 'info',
    path: '/proctoring'
  },
  { 
    title: '考场编排', 
    desc: '可视化分配考场座位，支持随机打乱。', 
    status: 'pending', 
    statusLabel: '待开始',
    tagType: 'info',
    path: '/rooms'
  },
  { 
    title: '资料打印', 
    desc: '一键生成准考证、台角纸及考场门贴。', 
    status: 'pending', 
    statusLabel: '待开始',
    tagType: 'info',
    path: '/printing'
  }
])

const loadStats = async () => {
  try {
    const res = await pythonBackend.request<any>('dashboard.getStats', {})
    if (res.stats) {
      const pathMap: Record<string, string> = {
        '考试科目': '/subjects',
        '监考教师': '/proctoring',
        '考场编排': '/rooms',
        '资料打印': '/printing'
      }
      stats.value = res.stats.map((s: any) => ({
        ...s,
        icon: iconMap[s.icon] || markRaw(Notebook),
        path: pathMap[s.label] || ''
      }))
    }
    if (res.workflow) {
      workflow.value = res.workflow.map((w: any) => {
        let statusLabel = '待开始'
        let tagType = 'info'
        if (w.status === 'completed') {
          statusLabel = '已完成'
          tagType = 'success'
        } else if (w.status === 'current') {
          statusLabel = '进行中'
          tagType = 'primary'
        }
        return {
          ...w,
          statusLabel,
          tagType
        }
      })
    }
  } catch (e) {
    console.error("读取看板数据失败", e)
  }
}

const handleReset = async () => {
  try {
    await pythonBackend.request('system.resetData', {})
    ElMessage.success('系统已重置')
    await loadStats()
  } catch (e: any) {
    ElMessage.error(`重置失败: ${e.message || e}`)
  }
}

onMounted(() => {
  loadStats()
  updateCountdown()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

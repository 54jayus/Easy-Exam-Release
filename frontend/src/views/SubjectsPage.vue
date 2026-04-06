<template>
  <div class="h-full flex bg-slate-50/50 animate-fade-in relative overflow-hidden font-sans text-slate-600">
    <!-- Background Pattern -->
    <div class="absolute inset-0 z-0 pointer-events-none opacity-[0.03]"
         style="background-image: radial-gradient(#64748b 1px, transparent 1px); background-size: 24px 24px;">
    </div>

    <!-- Left Sidebar: Controls & Settings -->
    <div
      class="flex flex-col border-r border-slate-200/80 bg-white/80 backdrop-blur-xl transition-[width,opacity] duration-300 relative z-20 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)]"
      :class="sidebarCollapsed ? 'w-0 opacity-0 overflow-hidden' : 'w-[280px] opacity-100'"
    >
       <div class="h-14 px-4 border-b border-slate-100/80 flex items-center justify-between shrink-0 bg-gradient-to-b from-white to-slate-50/50">
          <div class="flex items-center gap-2">
             <div class="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center text-white shadow-lg shadow-sky-200">
                <el-icon :size="16"><Notebook /></el-icon>
             </div>
             <span class="font-bold text-slate-800 text-base tracking-tight">科目设置</span>
          </div>
          <div class="flex items-center gap-1">
             <el-tooltip content="初始化当前页面（清除所有数据与设置）" placement="bottom">
                <el-button link class="!text-slate-400 hover:!text-rose-600 transition-colors flex items-center gap-1" @click="handleResetPage">
                   <el-icon><Delete /></el-icon>
                   <span class="text-xs">初始化</span>
                </el-button>
             </el-tooltip>
             <el-button link class="!text-slate-400 hover:!text-slate-600 transition-colors flex items-center gap-1" @click="sidebarCollapsed = true">
                <el-icon><Fold /></el-icon>
                <span class="text-xs">收起</span>
             </el-button>
          </div>
       </div>

       <div class="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-8">
          
          <!-- 1. Data Source -->
          <section class="space-y-3">
             <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                   <div class="w-1 h-3 bg-sky-500 rounded-full"></div>
                   <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">数据管理</span>
                </div>
                <div class="px-2 py-0.5 rounded text-[10px] font-bold transition-colors"
                     :class="subjects.length ? 'bg-sky-100 text-sky-700' : 'bg-slate-100 text-slate-400'">
                   {{ subjects.length ? `共 ${subjects.length} 科` : '无数据' }}
                </div>
             </div>

             <div class="grid grid-cols-2 gap-2">
                <button
                   class="flex items-center justify-center gap-2 p-2 pr-7 bg-white border border-slate-200 rounded-lg hover:border-sky-400 hover:shadow-md hover:shadow-sky-50 transition-[border-color,box-shadow] duration-200 group relative"
                   :class="importedFromFile ? '!border-sky-500 bg-sky-50/50' : ''"
                   @click="handleImport"
                >
                   <el-icon class="text-base transition-colors duration-200" :class="importedFromFile ? 'text-sky-600' : 'text-slate-400 group-hover:text-sky-500'"><FolderOpened /></el-icon>
                   <span class="text-xs font-medium transition-colors duration-200" :class="importedFromFile ? 'text-sky-700 font-bold' : 'text-slate-600 group-hover:text-sky-700'">导入科目</span>
                   <span
                      v-if="importedFromFile"
                      class="absolute right-1 top-1/2 -translate-y-1/2 w-5 h-5 rounded flex items-center justify-center text-sky-600 hover:bg-sky-100 transition-colors duration-200"
                      @click.stop.prevent="handleClearImport"
                   >×</span>
                </button>
                <button
                  class="flex items-center justify-center gap-2 p-2 bg-white border border-slate-200 rounded-lg hover:border-sky-400 hover:shadow-md hover:shadow-sky-50 transition-[border-color,box-shadow] duration-200 group"
                  @click="handleTemplate"
                >
                   <el-icon class="text-base text-slate-400 group-hover:text-sky-500 transition-colors"><Download /></el-icon>
                   <span class="text-xs font-medium text-slate-600 group-hover:text-sky-700">下载模板</span>
                </button>
             </div>

             <button
               class="flex w-full items-center justify-center gap-2 p-2 bg-white border border-slate-200 rounded-lg hover:border-sky-400 hover:shadow-md hover:shadow-sky-50 transition-[border-color,box-shadow] duration-200 group"
               @click="handleExport"
               :disabled="subjects.length === 0"
             >
                <el-icon class="text-base text-slate-400 group-hover:text-sky-500 transition-colors"><Share /></el-icon>
                <span class="text-xs font-medium text-slate-600 group-hover:text-sky-700">导出数据</span>
             </button>
          </section>

          <!-- 2. Validation Status -->
          <section class="space-y-3" v-if="validationErrors.length > 0">
             <div class="flex items-center gap-2 mb-2">
                <div class="w-1 h-3 bg-rose-500 rounded-full"></div>
                <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">异常检测</span>
             </div>
             <div 
               class="p-3 bg-rose-50 border border-rose-100 rounded-xl cursor-pointer hover:bg-rose-100 transition-colors"
               @click="showErrors = true"
             >
                <div class="flex items-center gap-2 text-rose-600 font-bold text-sm mb-1">
                   <el-icon><Warning /></el-icon>
                   <span>发现 {{ validationErrors.length }} 个冲突</span>
                </div>
                <div class="text-xs text-rose-400">点击查看详细校验报告</div>
             </div>
          </section>

          <!-- 3. Actions -->
          <section class="pt-4 mt-auto space-y-3">
             <el-button type="primary" size="large" class="w-full !h-12 !text-base !font-bold !rounded-xl shadow-lg shadow-sky-200 hover:shadow-sky-300 transition-all hover:-translate-y-0.5" @click="handleAdd">
                <el-icon class="mr-2"><Plus /></el-icon> 新建科目
             </el-button>
             
             <div v-if="subjects.length > 0" class="text-center">
                <el-popconfirm title="确定清空所有科目数据?" @confirm="handleClearAll">
                  <template #reference>
                    <el-button link type="danger" size="small" class="opacity-60 hover:opacity-100">
                       <el-icon class="mr-1"><Delete /></el-icon> 清空所有数据
                    </el-button>
                  </template>
                </el-popconfirm>
             </div>
          </section>

       </div>
    </div>

    <!-- Toggle Button (Visible when collapsed) -->
    <div 
       v-if="sidebarCollapsed" 
       class="absolute left-0 top-6 z-30 bg-white border border-l-0 border-slate-200 p-2 rounded-r-xl shadow-lg cursor-pointer hover:bg-sky-50 hover:text-sky-600 transition-all hover:pl-3"
       @click="sidebarCollapsed = false"
    >
       <el-icon><Expand /></el-icon>
    </div>

    <!-- Right Main Content -->
    <div class="flex-1 flex flex-col min-w-0 h-full relative z-10">
       
       <!-- Top Bar -->
       <div class="h-14 bg-white/80 backdrop-blur border-b border-slate-200/60 px-4 flex items-center justify-between shrink-0 sticky top-0 z-10 gap-4">
          <div class="flex items-center gap-4 flex-shrink min-w-0">
             <h2 class="text-base font-bold text-slate-700 truncate">科目列表</h2>
             <div class="flex items-center gap-2 px-2.5 py-1 bg-slate-100/80 rounded-full border border-slate-200/50 hidden md:flex">
                <span class="text-xs text-slate-500">状态:</span>
                <span 
                   class="text-xs font-bold"
                   :class="subjects.length > 0 ? (validationErrors.length === 0 ? 'text-emerald-600' : 'text-rose-600') : 'text-slate-400'"
                >
                   {{ subjects.length > 0 ? (validationErrors.length === 0 ? '数据正常' : '存在冲突') : '等待导入' }}
                </span>
             </div>
          </div>

          <div class="flex items-center gap-3 shrink-0">
             <!-- View Toggle -->
             <div class="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
                <el-tooltip content="列表视图" placement="bottom">
                   <button 
                      class="px-2 py-1 rounded-md text-xs font-bold transition-all flex items-center justify-center"
                      :class="viewMode === 'list' ? 'bg-white text-sky-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'"
                      @click="viewMode = 'list'"
                   >
                      <el-icon :size="16"><List /></el-icon>
                   </button>
                </el-tooltip>
                <el-tooltip content="网格视图" placement="bottom">
                   <button 
                      class="px-2 py-1 rounded-md text-xs font-bold transition-all flex items-center justify-center"
                      :class="viewMode === 'grid' ? 'bg-white text-sky-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'"
                      @click="viewMode = 'grid'"
                   >
                      <el-icon :size="16"><Grid /></el-icon>
                   </button>
                </el-tooltip>
             </div>

             <div class="w-px h-3 bg-slate-200 hidden xl:block"></div>

             <el-tooltip content="操作日志" placement="bottom">
                <button 
                  class="w-7 h-7 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-500 hover:text-sky-600 transition-colors relative"
                  @click="showLogs = true"
                >
                   <el-icon :size="16"><CollectionTag /></el-icon>
                   <el-badge :is-dot="logs.length > 0 && !showLogs" type="primary" :offset="[-2, 2]" class="absolute top-0 right-0" />
                </button>
             </el-tooltip>
          </div>
       </div>

       <!-- Content Area -->
       <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <!-- Empty State -->
          <div v-if="subjects.length === 0" class="h-full flex flex-col items-center justify-center bg-white/50 backdrop-blur-sm rounded-3xl border-2 border-dashed border-slate-300">
             <div class="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4 shadow-inner">
                <el-icon class="text-slate-300" :size="40"><Notebook /></el-icon>
             </div>
             <h3 class="text-lg font-bold text-slate-900 mb-1">暂无科目数据</h3>
             <p class="text-slate-500 mb-6">请导入 Excel 文件或手动添加科目</p>
             <div class="flex gap-3">
                <el-button type="primary" @click="handleImport">立即导入</el-button>
                <el-button @click="handleAdd">手动添加</el-button>
             </div>
          </div>

          <!-- Grid View (Bento Grid) -->
          <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-10">
             <div 
               v-for="(subject, index) in subjects" 
               :key="index"
               class="group relative bg-white rounded-2xl p-5 border border-slate-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-default"
             >
                <!-- Card Header -->
                <div class="flex items-start justify-between mb-4">
                   <div class="flex-1">
                      <h3 class="text-lg font-bold text-slate-900 line-clamp-1" :title="subject.name">{{ subject.name }}</h3>
                      <p class="text-xs text-slate-400 mt-1">ID: {{ index + 1 }}</p>
                   </div>
                   <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button class="p-1.5 text-slate-400 hover:text-sky-600 hover:bg-sky-50 rounded-lg transition-colors" @click.stop="handleEdit(subject, index)">
                         <el-icon><Edit /></el-icon>
                      </button>
                      <el-popconfirm title="确定删除?" @confirm="handleDelete(index)">
                         <template #reference>
                            <button class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors">
                               <el-icon><Delete /></el-icon>
                            </button>
                         </template>
                      </el-popconfirm>
                   </div>
                </div>

                <!-- Timeline / Schedule Info -->
                <div class="space-y-3">
                   <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-sky-50 flex items-center justify-center text-sky-600 flex-shrink-0">
                         <el-icon><Calendar /></el-icon>
                      </div>
                      <div>
                         <div class="text-xs text-slate-400">考试日期</div>
                         <div class="font-medium text-slate-700">{{ subject.exam_date }}</div>
                      </div>
                   </div>
                   
                   <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 flex-shrink-0">
                         <el-icon><Clock /></el-icon>
                      </div>
                      <div>
                         <div class="text-xs text-slate-400">时间段</div>
                         <div class="font-medium text-slate-700">{{ subject.exam_time }}</div>
                      </div>
                   </div>

                   <!-- Duration Bar -->
                   <div class="pt-2">
                      <div class="flex justify-between text-xs mb-1">
                         <span class="text-slate-500">时长</span>
                         <span class="font-bold text-slate-900">{{ subject.duration_minutes }} 分钟</span>
                      </div>
                      <div class="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                         <div class="h-full bg-gradient-to-r from-sky-400 to-indigo-500 rounded-full" :style="{ width: Math.min(subject.duration_minutes / 1.8, 100) + '%' }"></div>
                      </div>
                   </div>
                </div>

                <!-- Remark Footer -->
                <div v-if="subject.remark" class="mt-4 pt-3 border-t border-slate-50">
                   <p class="text-xs text-slate-500 line-clamp-2">{{ subject.remark }}</p>
                </div>
             </div>

             <!-- Add New Card (Ghost) -->
             <button 
               class="group flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-slate-300 hover:border-sky-400 hover:bg-sky-50/30 transition-all duration-300 min-h-[200px]"
               @click="handleAdd"
             >
                <div class="w-12 h-12 rounded-full bg-white shadow-sm flex items-center justify-center text-slate-400 group-hover:text-sky-600 group-hover:scale-110 transition-all duration-300">
                   <el-icon :size="24"><Plus /></el-icon>
                </div>
                <span class="font-medium text-slate-500 group-hover:text-sky-600">添加新科目</span>
             </button>
          </div>

          <!-- List View -->
          <div v-else class="h-full bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
             <el-table :data="subjects" border stripe height="100%" :header-cell-style="{background:'#f8fafc', color:'#475569', fontWeight:'600'}">
                <el-table-column type="index" label="序号" width="60" align="center" />
                <el-table-column prop="name" label="科目名称" min-width="120" align="center">
                   <template #default="{ row }">
                      <span class="font-bold text-slate-700">{{ row.name }}</span>
                   </template>
                </el-table-column>
                <el-table-column prop="exam_date" label="考试日期" width="120" align="center" sortable />
                <el-table-column prop="exam_time" label="时间段" width="140" align="center" />
                <el-table-column prop="duration_minutes" label="时长(分钟)" width="100" align="center" sortable>
                   <template #default="{ row }">
                      <el-tag type="info" effect="plain">{{ row.duration_minutes }} min</el-tag>
                   </template>
                </el-table-column>
                <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
                <el-table-column label="操作" width="120" align="center" fixed="right">
                   <template #default="{ row, $index }">
                      <el-button link type="primary" @click="handleEdit(row, $index)">编辑</el-button>
                      <el-popconfirm title="确定删除?" @confirm="handleDelete($index)">
                         <template #reference>
                            <el-button link type="danger">删除</el-button>
                         </template>
                      </el-popconfirm>
                   </template>
                </el-table-column>
             </el-table>
          </div>
       </div>
    </div>

    <!-- Validation Drawer -->
    <el-drawer v-model="showErrors" title="数据校验结果" direction="rtl" size="400px">
      <div class="space-y-3 p-4">
        <div v-for="(err, index) in validationErrors" :key="index" 
          class="flex items-start gap-3 p-3 bg-rose-50 text-rose-700 rounded-xl border border-rose-100 text-sm">
          <el-icon class="mt-0.5 flex-shrink-0"><WarningFilled /></el-icon>
          <span>{{ err }}</span>
        </div>
      </div>
    </el-drawer>

    <!-- Logs Drawer -->
    <el-drawer v-model="showLogs" title="系统操作日志" direction="rtl" size="350px">
       <div class="flex flex-col h-full">
          <div class="flex justify-end mb-4">
             <el-button size="small" type="danger" plain @click="logs = []">
                <el-icon class="mr-1"><Delete /></el-icon> 清空日志
             </el-button>
          </div>
          <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
             <div v-if="logs.length === 0" class="text-slate-400 italic text-center mt-10 flex flex-col items-center">
                <el-icon class="text-4xl mb-2 opacity-20"><CollectionTag /></el-icon>
                暂无日志记录...
             </div>
             <div v-else class="relative pl-4 border-l border-slate-200 ml-2 space-y-6">
                <div v-for="(log, idx) in logs" :key="idx" class="relative group">
                   <!-- Timeline Dot -->
                   <div class="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm transition-colors"
                        :class="{
                           'bg-sky-500': log.level === 'info',
                           'bg-emerald-500': log.level === 'success',
                           'bg-rose-500': log.level === 'error',
                           'bg-amber-500': log.level === 'warning'
                        }"></div>
                   
                   <div class="text-xs text-slate-400 font-mono mb-0.5">{{ log.time }}</div>
                   <div class="text-sm text-slate-700 break-words group-hover:text-sky-600 transition-colors bg-slate-50 p-2 rounded-lg border border-slate-100 group-hover:border-sky-100 group-hover:bg-sky-50/50">
                      {{ log.msg }}
                   </div>
                </div>
             </div>
          </div>
       </div>
    </el-drawer>

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑科目' : '新建科目'"
      width="500px"
      class="!rounded-2xl overflow-hidden"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="p-2">
        <el-form-item label="科目名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：语文" class="!text-lg" />
        </el-form-item>
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="考试日期" prop="exam_date">
            <el-date-picker v-model="form.exam_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" class="!w-full" />
          </el-form-item>
          <el-form-item label="时间段" prop="exam_time">
            <el-time-picker
              v-model="examTimeRange"
              is-range
              value-format="HH:mm"
              format="HH:mm"
              range-separator="-"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              :prefix-icon="Timer"
              class="!w-full"
            />
          </el-form-item>
        </div>
        <el-form-item label="时长 (分钟)" prop="duration_minutes">
          <el-input-number v-model="form.duration_minutes" :min="0" :step="10" class="!w-full" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePageSessionState } from '@/composables/usePageSessionState'
import { 
  Download, Share, FolderOpened, Plus, Warning, WarningFilled,
  Calendar, Clock, Edit, Delete, Timer, Notebook, CollectionTag,
  List, Grid, Fold, Expand
} from '@element-plus/icons-vue'
import { open, saveAndRun } from '@/lib/dialog'
import { pythonBackend } from '@/lib/pythonBackend'
import { createLogger } from '@/lib/logger'
import dayjs from 'dayjs'

interface Subject {
  name: string
  exam_date: string
  exam_time: string
  duration_minutes: number
  remark: string
}

// State
const sidebarCollapsed = ref(false)
const storage = usePageSessionState('subjects')
const getStored = (key: string, def: string) => storage.getPref(key, def)

const subjects = ref<Subject[]>([])
const importedFromFile = ref(false)
const validationErrors = ref<string[]>([])
const showErrors = ref(false)
const showLogs = ref(false)
const viewMode = ref(getStored('viewMode', 'grid')) // 'grid' | 'list'
type UiLogLevel = 'info' | 'success' | 'warning' | 'error'
const logs = ref<{ time: string; level: UiLogLevel; msg: string }[]>([])
const loading = ref(false)
const logger = createLogger('subjects')

// Persistence Watchers
watch(viewMode, (val) => storage.setPref('viewMode', val))

// Dialog State
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingIndex = ref(-1)
const formRef = ref()
const form = reactive<Subject>({
  name: '',
  exam_date: '',
  exam_time: '',
  duration_minutes: 0,
  remark: ''
})

const rules = {
  name: [{ required: true, message: '请输入科目名称', trigger: 'blur' }],
  exam_date: [{ required: true, message: '请选择考试日期', trigger: 'change' }],
  exam_time: [
    { required: true, message: '请选择考试时间段', trigger: 'change' },
    { pattern: /^\d{1,2}:\d{2}-\d{1,2}:\d{2}$/, message: '格式应为 HH:mm-HH:mm', trigger: 'change' }
  ]
}

// Logging
const pushLog = (level: UiLogLevel, msg: string) => {
  logs.value.unshift({ time: dayjs().format('HH:mm:ss'), level, msg })
}
const logInfo = (msg: string) => pushLog('info', msg)
const logSuccess = (msg: string) => pushLog('success', msg)
const logWarning = (msg: string) => pushLog('warning', msg)
const logError = (msg: string) => pushLog('error', msg)
const logFromText = (msg: string) => {
  const m = String(msg || '')
  if (m.includes('失败') || m.includes('异常') || m.includes('错误')) return logError(m)
  if (m.includes('警告')) return logWarning(m)
  if (m.includes('成功') || m.includes('完成')) return logSuccess(m)
  return logInfo(m)
}

// Methods
const syncToBackend = async () => {
   try {
      const res = await pythonBackend.request<any>('subjects.update', { subjects: subjects.value })
      if (res?.proctoringReset) {
         ElMessage.warning('科目已更新，原监考编排结果已自动清除')
         logInfo('科目变更，监考编排结果已自动重置')
      }
   } catch (e) {
      logger.error('同步科目数据失败', e)
   }
}

const loadFromBackend = async () => {
   try {
      const res = await pythonBackend.request('subjects.list')
      if (res && res.subjects) {
         subjects.value = res.subjects as any
         if (res.subjects.length > 0) importedFromFile.value = true
      }
   } catch (e) {
      logger.error('读取科目数据失败', e)
   }
}

const validateData = async () => {
  if (subjects.value.length === 0) {
    validationErrors.value = []
    return
  }
  try {
    const res = await pythonBackend.request('subjects.validate', {
      subjects: subjects.value
    })
    validationErrors.value = res.errors
    if (res.errors.length > 0) {
      ElMessage.warning(`发现 ${res.errors.length} 个潜在问题`)
      logWarning(`数据校验发现 ${res.errors.length} 个问题`)
    } else {
      logSuccess('数据校验通过')
    }
  } catch (err) {
    logger.error('数据校验失败', err)
  }
}

const handleImport = async () => {
  try {
    logInfo('正在打开文件选择器')
    const selected = await open({
      multiple: false,
      filters: [{ name: 'Excel Files', extensions: ['xlsx', 'xls'] }]
    })
    
    if (selected) {
      logInfo(`已选择文件：${selected}`)
      loading.value = true
      logInfo('正在导入科目数据')
      const res = await pythonBackend.request('subjects.import', {
        path: selected
      })
      
      if (res.subjects && res.subjects.length > 0) {
        subjects.value = res.subjects
        importedFromFile.value = true
        ElMessage.success(`成功导入 ${res.subjects.length} 个科目`)
        logSuccess(`成功导入 ${res.subjects.length} 个科目`)
        if (res.proctoringReset) {
          ElMessage.warning('科目已更新，原监考编排结果已自动清除')
          logInfo('科目变更，监考编排结果已自动重置')
        }
      }
      
      validationErrors.value = res.errors
      if (res.errors.length > 0) {
        showErrors.value = true
        logError(`导入发现 ${res.errors.length} 个错误`)
      }
    }
  } catch (err) {
    ElMessage.error('导入失败: ' + err)
    logError(`导入失败：${err}`)
  } finally {
    loading.value = false
  }
}

const handleClearImport = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有科目数据吗？',
      '清除科目数据',
      { type: 'warning', confirmButtonText: '清除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  subjects.value = []
  importedFromFile.value = false
  validationErrors.value = []
  await pythonBackend.request('subjects.update', { subjects: [] })
  logInfo('已清除科目数据')
}

const handleExport = async () => {
  if (subjects.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }
  
  logInfo('正在打开文件保存对话框')
  await saveAndRun({
    dialog: {
      filters: [{ name: 'Excel Files', extensions: ['xlsx'] }],
      defaultPath: '科目信息.xlsx'
    },
    run: async (path) => {
      logInfo('正在导出科目数据')
      return await pythonBackend.request('subjects.export', {
        path,
        subjects: subjects.value
      })
    },
    successText: '导出成功',
    errorText: '导出失败',
    openFolderTitle: '导出成功',
    onLog: logFromText
  })
}

const handleTemplate = async () => {
  logInfo('正在打开文件保存对话框')
  await saveAndRun({
    dialog: {
      filters: [{ name: 'Excel Files', extensions: ['xlsx'] }],
      defaultPath: '科目导入模板.xlsx'
    },
    run: async (path) => {
      return await pythonBackend.request('subjects.template', { path })
    },
    successText: '模板生成成功',
    errorText: '模板生成失败',
    openFolderTitle: '模板生成成功',
    onLog: logFromText
  })
}

const handleAdd = () => {
  isEdit.value = false
  editingIndex.value = -1
  Object.assign(form, {
    name: '',
    exam_date: '',
    exam_time: '',
    duration_minutes: 0,
    remark: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row: Subject, index: number) => {
  isEdit.value = true
  editingIndex.value = index
  Object.assign(form, { ...row })
  dialogVisible.value = true
}

const handleDelete = async (index: number) => {
  const deletedName = subjects.value[index].name
  subjects.value.splice(index, 1)
  await syncToBackend()
  logInfo(`删除科目：${deletedName}`)
  validateData()
}

const handleClearAll = async () => {
  subjects.value = []
  await syncToBackend()
  logInfo('已清空全部科目数据')
  validationErrors.value = []
}

const handleResetPage = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要初始化当前页面吗？这将清除所有数据与设置（科目数据、校验状态、日志、视图偏好等）。',
      '初始化页面',
      { type: 'warning', confirmButtonText: '初始化', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  storage.removePref('viewMode')

  subjects.value = []
  validationErrors.value = []
  showErrors.value = false
  showLogs.value = false
  logs.value = []
  loading.value = false

  dialogVisible.value = false
  isEdit.value = false
  editingIndex.value = -1
  Object.assign(form, {
    name: '',
    exam_date: '',
    exam_time: '',
    duration_minutes: 0,
    remark: ''
  })

  viewMode.value = 'grid'
  sidebarCollapsed.value = false

  await syncToBackend()
  logSuccess('页面已初始化')
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      const newSubject = { ...form }
      if (isEdit.value && editingIndex.value > -1) {
        subjects.value[editingIndex.value] = newSubject
        logInfo(`更新科目：${newSubject.name}`)
      } else {
        subjects.value.push(newSubject)
        logInfo(`新增科目：${newSubject.name}`)
      }
      await syncToBackend()
      dialogVisible.value = false
      validateData()
    }
  })
}

function calculateDuration() {
  if (!form.exam_time) return
  const m = form.exam_time.match(/^(\d{1,2}):(\d{2})\s*[-~]\s*(\d{1,2}):(\d{2})$/)
  if (!m) return

  const start = Number(m[1]) * 60 + Number(m[2])
  const end = Number(m[3]) * 60 + Number(m[4])
  if (Number.isNaN(start) || Number.isNaN(end)) return

  let diff = end - start
  if (diff < 0) diff += 24 * 60
  form.duration_minutes = diff
}

const examTimeRange = computed<[string, string] | undefined>({
  get() {
    const m = form.exam_time.match(/^(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})$/)
    if (!m) return undefined
    return [m[1], m[2]]
  },
  set(val) {
    if (Array.isArray(val) && val.length === 2 && val[0] && val[1]) {
      form.exam_time = `${val[0]}-${val[1]}`
      calculateDuration()
      return
    }
    form.exam_time = ''
    form.duration_minutes = 0
  }
})

// Initialize
let logCleanup: (() => void) | null = null

onMounted(() => {
  loadFromBackend()

  logCleanup = pythonBackend.onLog((msg, type) => {
    // Filter raw RPC JSON to reduce noise, but show everything else
    if (type === 'stdout') {
      try {
        const obj = JSON.parse(msg)
        if (obj.id !== undefined && (obj.result !== undefined || obj.error !== undefined)) {
           if (obj.error) {
             logError(`后端 RPC 失败：${String(obj.error)}`)
           }
           // Skip success RPC raw messages
           return
        }
      } catch {}
    }
    
    // Truncate very long messages
    const displayMsg = msg.length > 300 ? msg.slice(0, 300) + '...' : msg
    pushLog(type === 'stderr' ? 'warning' : 'info', `后端${type === 'stderr' ? 'stderr' : 'stdout'}：${displayMsg}`)
  })
})

onUnmounted(() => {
  if (logCleanup) logCleanup()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(148, 163, 184, 0.5);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(148, 163, 184, 0.8);
}
</style>

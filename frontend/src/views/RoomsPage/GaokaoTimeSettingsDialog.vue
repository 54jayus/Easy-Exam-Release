<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="高考模式时间设置"
    :width="dialogWidth"
    align-center
    :close-on-click-modal="false"
    append-to-body
    destroy-on-close
    class="gaokao-time-dialog"
  >
    <div class="dialog-content">
      <!-- 说明文字 -->
      <div class="info-banner">
        <i class="el-icon-info-filled"></i>
        <span>设置各科目的考试时间，选考科目可单独设置自习时间。</span>
      </div>

      <!-- 考试时间设置 -->
      <section class="time-section">
        <h3 class="section-title">考试时间设置</h3>

        <!-- 列标题 -->
        <div class="table-header">
          <div class="header-cell subject-col">科目</div>
          <div class="header-cell date-col">日期</div>
          <div class="header-cell time-col">时间段</div>
        </div>

        <!-- 数据行 -->
        <div class="table-body">
          <div v-for="subject in examSubjects" :key="subject" class="subject-group">
            <!-- 考试时间行 -->
            <div class="table-row exam-row">
              <div class="cell subject-col">
                <span class="subject-name">{{ subject }}</span>
              </div>
              <div class="cell date-col">
                <el-date-picker
                  v-model="(localSettings.examTimes as any)[subject].date"
                  type="date"
                  placeholder="选择日期"
                  size="default"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  class="w-full"
                />
              </div>
              <div class="cell time-col">
                <div class="time-range">
                  <el-time-picker
                    v-model="(localSettings.examTimes as any)[subject].startTime"
                    placeholder="开始"
                    size="default"
                    format="HH:mm"
                    value-format="HH:mm"
                    class="time-input"
                    :popper-options="{ strategy: 'fixed' }"
                    popper-class="time-picker-popper"
                  />
                  <span class="time-separator">-</span>
                  <el-time-picker
                    v-model="(localSettings.examTimes as any)[subject].endTime"
                    placeholder="结束"
                    size="default"
                    format="HH:mm"
                    value-format="HH:mm"
                    class="time-input"
                    :popper-options="{ strategy: 'fixed' }"
                    popper-class="time-picker-popper"
                  />
                </div>
              </div>
            </div>

            <!-- 自习时间行（仅选考科目） -->
            <div v-if="isElectiveSubject(subject)" class="self-study-row">
              <div class="self-study-toggle">
                <el-checkbox
                  v-model="customSelfStudyTime[subject]"
                  @change="handleSelfStudyToggle(subject)"
                >
                  自定义自习时间
                </el-checkbox>
              </div>
              <div v-if="customSelfStudyTime[subject]" class="self-study-settings">
                <div class="cell date-col">
                  <el-date-picker
                    v-model="(localSettings.selfStudyTimes as any)[subject].date"
                    type="date"
                    placeholder="选择日期"
                    size="small"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    class="w-full"
                  />
                </div>
                <div class="cell time-col">
                  <div class="time-range">
                    <el-time-picker
                      v-model="(localSettings.selfStudyTimes as any)[subject].startTime"
                      placeholder="开始"
                      size="small"
                      format="HH:mm"
                      value-format="HH:mm"
                      class="time-input"
                      :popper-options="{ strategy: 'fixed' }"
                      popper-class="time-picker-popper"
                    />
                    <span class="time-separator">-</span>
                    <el-time-picker
                      v-model="(localSettings.selfStudyTimes as any)[subject].endTime"
                      placeholder="结束"
                      size="small"
                      format="HH:mm"
                      value-format="HH:mm"
                      class="time-input"
                      :popper-options="{ strategy: 'fixed' }"
                      popper-class="time-picker-popper"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="resetToDefault" class="reset-btn">
          <i class="el-icon-refresh-left"></i>
          恢复默认
        </el-button>
        <div class="action-buttons">
          <el-button @click="$emit('update:visible', false)">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">
            <i v-if="!saving" class="el-icon-check"></i>
            保存
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { formatActionError, formatActionSuccess } from '@/lib/uiFeedback'
import { pythonBackend } from '@/lib/pythonBackend'
import { GAOKAO_TIME_DEFAULTS, type GaokaoTimeSettings } from '@/types/gaokao'

// Props & Emits
interface Props {
  visible: boolean
  settings: GaokaoTimeSettings
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:settings': [value: GaokaoTimeSettings]
  'log-success': [msg: string]
  'log-error': [msg: string]
}>()

// State
const examSubjects = ['语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物']
const electiveSubjects = ['化学', '地理', '政治', '生物']
const localSettings = ref<GaokaoTimeSettings>(JSON.parse(JSON.stringify(props.settings)))
const saving = ref(false)

// 自定义自习时间的开关状态
const customSelfStudyTime = reactive<Record<string, boolean>>({
  化学: false,
  地理: false,
  政治: false,
  生物: false
})

// 响应式对话框宽度 - 增加宽度以容纳组件
const dialogWidth = computed(() => {
  if (typeof window === 'undefined') return '800px'
  const width = window.innerWidth
  if (width < 768) return '95%'
  if (width < 1024) return '85%'
  return '800px'
})

// 判断是否为选考科目
const isElectiveSubject = (subject: string) => {
  return electiveSubjects.includes(subject)
}

// 检查自习时间是否与考试时间不同
const checkCustomSelfStudyTime = () => {
  for (const subject of electiveSubjects) {
    const examTime = localSettings.value.examTimes[subject as keyof typeof localSettings.value.examTimes]
    const selfStudyTime = localSettings.value.selfStudyTimes[subject as keyof typeof localSettings.value.selfStudyTimes]

    if (examTime.date !== selfStudyTime.date ||
        examTime.startTime !== selfStudyTime.startTime ||
        examTime.endTime !== selfStudyTime.endTime) {
      customSelfStudyTime[subject] = true
    }
  }
}

// Watch for external changes
watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    localSettings.value = JSON.parse(JSON.stringify(props.settings))
    checkCustomSelfStudyTime()
  }
})

// 处理自习时间开关切换
const handleSelfStudyToggle = (subject: string) => {
  if (!customSelfStudyTime[subject]) {
    // 关闭自定义时，同步为考试时间
    const examTime = localSettings.value.examTimes[subject as keyof typeof localSettings.value.examTimes]
    const selfStudyTime = localSettings.value.selfStudyTimes[subject as keyof typeof localSettings.value.selfStudyTimes]
    selfStudyTime.date = examTime.date
    selfStudyTime.startTime = examTime.startTime
    selfStudyTime.endTime = examTime.endTime
  }
}

// Methods
const resetToDefault = () => {
  localSettings.value = JSON.parse(JSON.stringify(GAOKAO_TIME_DEFAULTS))
  // 重置自定义开关
  for (const subject of electiveSubjects) {
    customSelfStudyTime[subject] = false
  }
  ElMessage.success('已恢复为默认时间设置')
  emit('log-success', formatActionSuccess('恢复默认时间设置'))
}

const validateSettings = (): string | null => {
  // 验证所有考试时间
  for (const subject of examSubjects) {
    const time = localSettings.value.examTimes[subject as keyof typeof localSettings.value.examTimes]
    if (!time.date || !time.startTime || !time.endTime) {
      return `${subject}的时间设置不完整`
    }
    if (time.startTime >= time.endTime) {
      return `${subject}的开始时间必须早于结束时间`
    }
  }

  // 验证自定义的自习时间
  for (const subject of electiveSubjects) {
    if (customSelfStudyTime[subject]) {
      const time = localSettings.value.selfStudyTimes[subject as keyof typeof localSettings.value.selfStudyTimes]
      if (!time.date || !time.startTime || !time.endTime) {
        return `${subject}的自习时间设置不完整`
      }
      if (time.startTime >= time.endTime) {
        return `${subject}的自习开始时间必须早于结束时间`
      }
    }
  }

  return null
}

const handleSave = async () => {
  // 验证
  const error = validateSettings()
  if (error) {
    ElMessage.error(error)
    return
  }

  saving.value = true
  try {
    const res = await pythonBackend.request('rooms.setGaokaoTimeSettings', {
      settings: localSettings.value
    }) as { error?: string }

    if (res?.error) {
      ElMessage.error(res.error)
      emit('log-error', formatActionError('保存时间设置', res.error))
      return
    }

    emit('update:settings', JSON.parse(JSON.stringify(localSettings.value)))
    ElMessage.success('时间设置已保存')
    emit('log-success', formatActionSuccess('保存高考模式时间设置'))
    emit('update:visible', false)
  } catch (e) {
    ElMessage.error(formatActionError('保存时间设置', e))
    emit('log-error', formatActionError('保存时间设置', e))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* 确保对话框在整个视口中居中，并限制整体高度 */
:deep(.gaokao-time-dialog.el-dialog) {
  margin: 0 auto !important;
  height: 85vh !important;
  max-height: 85vh !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}

/* 头部固定，不参与滚动 */
:deep(.gaokao-time-dialog .el-dialog__header) {
  flex-shrink: 0 !important;
}

/* 内容区自适应高度，超出时滚动 */
:deep(.gaokao-time-dialog .el-dialog__body) {
  padding: 20px 24px !important;
  flex: 1 1 auto !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  min-height: 0 !important;
  max-height: none !important;
  /* 关键：让 body 填满对话框剩余空间 */
  height: auto !important;
}

/* 底部固定，不参与滚动 */
:deep(.gaokao-time-dialog .el-dialog__footer) {
  flex-shrink: 0 !important;
}

/* 自定义滚动条样式 */
:deep(.gaokao-time-dialog .el-dialog__body)::-webkit-scrollbar {
  width: 8px;
}

:deep(.gaokao-time-dialog .el-dialog__body)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

:deep(.gaokao-time-dialog .el-dialog__body)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

:deep(.gaokao-time-dialog .el-dialog__body)::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 信息横幅 */
.info-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  border-left: 4px solid #2196f3;
  border-radius: 8px;
  font-size: 14px;
  color: #424242;
  line-height: 1.6;
}

.info-banner i {
  color: #2196f3;
  font-size: 18px;
  flex-shrink: 0;
}

/* 时间设置区域 */
.time-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e0e0e0;
}

/* 表格样式 */
.table-header {
  display: grid;
  grid-template-columns: 90px 160px 1fr;
  gap: 12px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: white;
}

.header-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 科目组 */
.subject-group {
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  overflow: hidden;
}

/* 考试时间行 */
.exam-row {
  display: grid;
  grid-template-columns: 90px 160px 1fr;
  gap: 12px;
  padding: 10px 12px;
  background: #fafafa;
  transition: all 0.2s ease;
}

.exam-row:hover {
  background: #f0f0f0;
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.cell {
  display: flex;
  align-items: center;
}

.subject-col {
  justify-content: center;
}

.subject-name {
  font-size: 14px;
  font-weight: 600;
  color: #424242;
  padding: 6px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

/* 时间范围 */
.time-range {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.time-input {
  flex: 1;
  min-width: 0;
}

.time-input :deep(.el-input__wrapper) {
  width: 100%;
}

.time-separator {
  color: #666;
  font-weight: 500;
  flex-shrink: 0;
  padding: 0 4px;
}

/* 自习时间行 */
.self-study-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 12px 12px 12px;
  background: #f5f5f5;
  border-top: 1px dashed #d0d0d0;
}

.self-study-toggle {
  display: flex;
  align-items: center;
  padding-left: 90px;
}

.self-study-toggle :deep(.el-checkbox) {
  font-size: 13px;
  color: #666;
}

.self-study-settings {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 12px;
  padding-left: 102px;
}

/* 底部按钮 */
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  :deep(.gaokao-time-dialog.el-dialog) {
    height: 90vh !important;
    max-height: 90vh !important;
  }

  :deep(.gaokao-time-dialog .el-dialog__body) {
    padding: 16px;
  }

  .table-header,
  .exam-row {
    grid-template-columns: 80px 140px 1fr;
    gap: 8px;
    font-size: 12px;
  }

  .table-header {
    padding: 8px 10px;
  }

  .exam-row {
    padding: 8px 10px;
  }

  .subject-name {
    font-size: 12px;
    padding: 4px 8px;
  }

  .section-title {
    font-size: 14px;
  }

  .info-banner {
    font-size: 13px;
    padding: 10px 12px;
  }

  .self-study-toggle {
    padding-left: 80px;
  }

  .self-study-settings {
    padding-left: 92px;
    grid-template-columns: 140px 1fr;
  }

  .dialog-footer {
    flex-direction: column;
    gap: 12px;
  }

  .action-buttons {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 640px) {
  :deep(.gaokao-time-dialog.el-dialog) {
    height: 95vh !important;
    max-height: 95vh !important;
  }

  :deep(.gaokao-time-dialog .el-dialog__body) {
    padding: 12px;
  }

  .table-header,
  .exam-row {
    grid-template-columns: 70px 120px 1fr;
    gap: 6px;
  }

  .subject-name {
    font-size: 11px;
    padding: 3px 6px;
  }

  .time-range {
    gap: 4px;
  }

  .time-separator {
    padding: 0 2px;
  }

  .self-study-toggle {
    padding-left: 70px;
  }

  .self-study-settings {
    padding-left: 82px;
    gap: 8px;
    grid-template-columns: 120px 1fr;
  }
}

/* Element Plus 组件样式覆盖 */
:deep(.gaokao-time-dialog .el-input__wrapper) {
  border-radius: 6px;
  transition: all 0.2s ease;
}

:deep(.gaokao-time-dialog .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

:deep(.gaokao-time-dialog .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #667eea inset;
}

:deep(.gaokao-time-dialog .el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
}

:deep(.gaokao-time-dialog .el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

:deep(.gaokao-time-dialog .el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

:deep(.gaokao-time-dialog .el-checkbox__label) {
  font-size: 13px;
}

/* 时间选择器下拉面板样式 */
:deep(.time-picker-popper) {
  max-width: 280px !important;
}
</style>


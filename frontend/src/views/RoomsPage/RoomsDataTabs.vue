<template>
  <div class="flex-1 flex flex-col min-w-0 h-full relative z-10">

    <!-- Header Area -->
    <div class="h-14 px-3 sm:px-4 flex items-center justify-between shrink-0 bg-white/80 backdrop-blur border-b border-slate-200/60 sticky top-0 z-10 gap-2 sm:gap-4">
      <div class="flex items-center flex-shrink min-w-0">
        <el-tabs :model-value="activeTab" @update:model-value="$emit('update:activeTab', $event)" class="custom-tabs-header no-border">
          <el-tab-pane name="settings">
            <template #label>
              <span class="flex items-center gap-1.5 text-sm">
                <el-icon><Setting /></el-icon> 考场设置
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane name="students">
            <template #label>
              <span class="flex items-center gap-1.5 text-sm">
                <el-icon><User /></el-icon> 考生名单
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane name="results">
            <template #label>
              <span class="flex items-center gap-1.5 text-sm">
                <el-icon><CollectionTag /></el-icon> 编排结果
              </span>
            </template>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- Top Actions -->
      <div class="flex items-center gap-2 shrink-0">
        <template v-if="activeTab === 'results'">
          <div class="flex items-center gap-1.5 px-2.5 py-1 bg-slate-100/80 rounded-full border border-slate-200/50 hidden xl:flex animate-fade-in">
            <span class="w-1.5 h-1.5 rounded-full" :class="hasResults ? 'bg-emerald-500' : 'bg-slate-300'"></span>
            <span class="text-xs font-medium text-slate-600">
              {{ hasResults ? `${resultsCount}人` : '待编排' }}
            </span>
          </div>

          <div class="h-3 w-px bg-slate-200 hidden xl:block animate-fade-in"></div>

          <div class="flex items-center gap-2 animate-fade-in">
            <el-input
              :model-value="searchQuery"
              @update:model-value="$emit('update:searchQuery', $event)"
              placeholder="搜索..."
              prefix-icon="Search"
              size="default"
              class="!w-20 sm:!w-24 md:!w-28 lg:!w-40 focus:!w-48 transition-all duration-300"
              clearable
            />
          </div>

          <div class="h-3 w-px bg-slate-200 animate-fade-in"></div>
        </template>

        <!-- Logs Button -->
        <el-tooltip content="操作日志" placement="bottom">
          <button
            class="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-500 hover:text-blue-600 transition-colors relative"
            @click="$emit('open-logs')"
          >
            <el-icon :size="18"><CollectionTag /></el-icon>
            <span v-if="logsCount > 0" class="absolute top-1 right-1 w-1.5 h-1.5 bg-red-500 rounded-full border border-white"></span>
          </button>
        </el-tooltip>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-hidden relative p-4">

      <!-- Tab 1: Room Settings Preview -->
      <div v-show="activeTab === 'settings'" class="h-full w-full bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
        <div class="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
              <el-icon class="text-xl"><Setting /></el-icon>
            </div>
            <div class="flex flex-col">
              <span class="font-bold text-slate-800">考场设置预览</span>
              <span class="text-xs text-slate-500">已加载 {{ settings.length }} 个标准考场</span>
            </div>
          </div>
          <el-button size="small" @click="$emit('reimport-settings')">重新导入</el-button>
        </div>
        <el-table
          :data="settings"
          border
          stripe
          height="100%"
          style="width: 100%"
          size="default"
          :header-cell-style="{ background: '#f8fafc', color: '#475569' }"
        >
          <el-table-column type="index" label="序号" width="80" align="center" />
          <el-table-column prop="roomNum" label="考场号" width="120" align="center" sortable>
            <template #default="{ row }">
              <span class="font-bold">{{ row.roomNum }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="roomName" label="考场" min-width="200" align="center" />
          <el-table-column prop="capacity" label="考场人数" width="120" align="center" sortable>
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.capacity }} 人</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Tab 2: Students Preview -->
      <div v-show="activeTab === 'students'" class="h-full w-full bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
        <div class="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 shrink-0">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
              <el-icon class="text-xl"><User /></el-icon>
            </div>
            <div class="flex flex-col">
              <span class="font-bold text-slate-800">考生名单预览</span>
              <span class="text-xs text-slate-500">已导入 {{ students.length }} 名考生数据</span>
            </div>
          </div>
          <el-button size="small" @click="$emit('reimport-students')">重新导入</el-button>
        </div>
        <el-table
          :data="pagedStudents"
          border
          stripe
          height="100%"
          style="width: 100%"
          size="default"
          :header-cell-style="{ background: '#f8fafc', color: '#475569' }"
        >
          <el-table-column type="index" label="序号" width="80" align="center" :index="studentIndexMethod" />
          <el-table-column prop="班级" label="班级" width="100" align="center" sortable />
          <el-table-column prop="学号" label="学号" width="120" align="center" sortable />
          <el-table-column prop="姓名" label="姓名" width="120" align="center">
            <template #default="{ row }">
              <span class="font-medium text-slate-900">{{ row['姓名'] }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="考号" label="考号" min-width="150" align="center" sortable />
          <el-table-column prop="选科" label="选科" min-width="150" show-overflow-tooltip />
        </el-table>

        <!-- Pagination for Students -->
        <BasePagination
          :current-page="studentsPage"
          @update:current-page="$emit('update:studentsPage', $event)"
          :page-size="studentsPageSize"
          @update:page-size="$emit('update:studentsPageSize', $event)"
          :total="students.length"
          :page-sizes="[50, 100, 200]"
        />
      </div>

      <!-- Tab 3: Results -->
      <div v-show="activeTab === 'results'" class="h-full w-full flex flex-col bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="h-full w-full flex flex-col">
          <el-table
            :data="pagedResults"
            border
            stripe
            height="100%"
            style="width: 100%"
            size="default"
            :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: '600', height: '44px' }"
          >
            <el-table-column type="index" label="序号" width="60" align="center" :index="resultsIndexMethod" fixed />

            <!-- 高考模式表格列 -->
            <template v-if="mode === 'gaokao'">
              <el-table-column prop="班级" label="班级" min-width="80" align="center" sortable />
              <el-table-column prop="姓名" label="姓名" min-width="80" align="center">
                <template #default="{ row }">
                  <span class="font-medium text-slate-700">{{ row['姓名'] }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="考号" label="考号" min-width="110" align="center" sortable />
              <el-table-column prop="选科" label="选科" min-width="100" show-overflow-tooltip />

              <!-- 统考分组 -->
              <el-table-column label="统考(语数英+物/史)">
                <el-table-column label="科目" min-width="60" align="center">
                  <template #default="{ row }">
                    {{ row['物理历史科目'] }}
                  </template>
                </el-table-column>
                <el-table-column label="考场" min-width="100" align="center" show-overflow-tooltip>
                  <template #default="{ row }">
                    {{ row['语文考场'] }}
                  </template>
                </el-table-column>
                <el-table-column label="考场号" min-width="70" align="center" sortable>
                  <template #default="{ row }">
                    <div class="inline-flex items-center px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-bold text-xs">
                      {{ row['语文考场号'] }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="座位号" min-width="70" align="center" sortable>
                  <template #default="{ row }">
                    <span class="font-mono text-blue-600 font-bold text-sm">{{ String(row['语文座位号']).padStart(2, '0') }}</span>
                  </template>
                </el-table-column>
              </el-table-column>

              <!-- 选考科目分组 -->
              <el-table-column v-for="subject in gaokaoElectives" :key="subject" :label="subject">
                <el-table-column label="考场号" min-width="70" align="center">
                  <template #default="{ row }">
                    <div class="inline-flex items-center px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-bold text-xs">
                      {{ row[subject + '考场号'] }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="座位号" min-width="70" align="center">
                  <template #default="{ row }">
                    <span class="font-mono text-blue-600 font-bold text-sm">{{ String(row[subject + '座位号']).padStart(2, '0') }}</span>
                    <div v-if="row[subject + '科目'] === '自习'" class="text-xs text-slate-400 leading-tight">自习</div>
                  </template>
                </el-table-column>
              </el-table-column>
            </template>

            <!-- 普通模式表格列 -->
            <template v-else>
              <el-table-column prop="班级" label="班级" min-width="80" align="center" sortable />
              <el-table-column prop="学号" label="学号" min-width="100" align="center" sortable show-overflow-tooltip />
              <el-table-column prop="姓名" label="姓名" min-width="100" align="center">
                <template #default="{ row }">
                  <span class="font-medium text-slate-700">{{ row['姓名'] }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="考号" label="考号" min-width="120" align="center" sortable />
              <el-table-column prop="选科" label="选科" min-width="100" show-overflow-tooltip />
              <el-table-column prop="首选" label="首选" min-width="80" align="center" />
              <el-table-column prop="选科1" label="选科1" min-width="80" align="center" />
              <el-table-column prop="选科2" label="选科2" min-width="80" align="center" />

              <el-table-column prop="考场" label="考场" min-width="120" align="center" show-overflow-tooltip />
              <el-table-column prop="考场号" label="考场号" min-width="90" align="center" sortable>
                <template #default="{ row }">
                  <div class="inline-flex items-center px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-bold text-xs">
                    {{ row['考场号'] }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="座位号" label="座位号" min-width="90" align="center" sortable>
                <template #default="{ row }">
                  <span class="font-mono text-blue-600 font-bold text-sm">{{ String(row['座位号']).padStart(2, '0') }}</span>
                </template>
              </el-table-column>

              <el-table-column v-if="mode === '3+1+2'" prop="考场选科组合" label="考场选科组合" min-width="120" show-overflow-tooltip />
            </template>
          </el-table>

          <!-- Pagination for Results -->
          <BasePagination
            :current-page="resultsPage"
            @update:current-page="$emit('update:resultsPage', $event)"
            :page-size="resultsPageSize"
            @update:page-size="$emit('update:resultsPageSize', $event)"
            :total="filteredResultsCount"
          />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Setting, User, CollectionTag } from '@element-plus/icons-vue'
import BasePagination from '@/components/BasePagination.vue'

interface Props {
  activeTab: string
  settings: any[]
  students: any[]
  results: any[]
  filteredResults: any[]
  studentsPage: number
  studentsPageSize: number
  resultsPage: number
  resultsPageSize: number
  searchQuery: string
  mode: string
  logsCount: number
}

const props = defineProps<Props>()

defineEmits<{
  'update:activeTab': [value: string]
  'update:studentsPage': [value: number]
  'update:studentsPageSize': [value: number]
  'update:resultsPage': [value: number]
  'update:resultsPageSize': [value: number]
  'update:searchQuery': [value: string]
  'reimport-settings': []
  'reimport-students': []
  'open-logs': []
}>()

// Constants
const gaokaoElectives = ['化学', '地理', '政治', '生物']

// Computed
const hasResults = computed(() => props.results.length > 0)
const resultsCount = computed(() => props.results.length)
const filteredResultsCount = computed(() => props.filteredResults.length)

const pagedStudents = computed(() => {
  const start = (props.studentsPage - 1) * props.studentsPageSize
  return props.students.slice(start, start + props.studentsPageSize)
})

const pagedResults = computed(() => {
  const start = (props.resultsPage - 1) * props.resultsPageSize
  return props.filteredResults.slice(start, start + props.resultsPageSize)
})

const studentIndexMethod = (index: number) => {
  return (props.studentsPage - 1) * props.studentsPageSize + index + 1
}

const resultsIndexMethod = (index: number) => {
  return (props.resultsPage - 1) * props.resultsPageSize + index + 1
}
</script>

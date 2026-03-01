<template>
  <div class="h-full flex bg-slate-50/50 animate-fade-in relative overflow-hidden font-sans text-slate-600">
    <!-- Background Pattern -->
    <div class="absolute inset-0 z-0 pointer-events-none opacity-[0.03]"
         style="background-image: radial-gradient(#64748b 1px, transparent 1px); background-size: 24px 24px;">
    </div>

    <!-- Left Sidebar: Controls & Settings -->
    <div 
      class="flex flex-col border-r border-slate-200/80 bg-white/80 backdrop-blur-xl transition-all duration-300 relative z-20 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)]"
      :class="sidebarCollapsed ? 'w-0 opacity-0 overflow-hidden' : 'w-[280px] opacity-100'"
    >
       <div class="h-14 px-4 border-b border-slate-100/80 flex items-center justify-between shrink-0 bg-gradient-to-b from-white to-slate-50/50">
          <div class="flex items-center gap-2">
             <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-200">
                <el-icon :size="16"><Setting /></el-icon>
             </div>
             <span class="font-bold text-slate-800 text-base tracking-tight">考场配置</span>
          </div>
          <div class="flex items-center gap-1">
             <el-tooltip content="初始化当前页面（清除所有考场数据与设置）" placement="bottom">
                <el-button link class="!text-slate-400 hover:!text-rose-600 transition-colors" @click="handleResetPage">
                   <el-icon><Delete /></el-icon>
                   <span class="text-xs">初始化</span>
                </el-button>
             </el-tooltip>
             <el-button link class="!text-slate-400 hover:!text-slate-600 transition-colors" @click="sidebarCollapsed = true">
                <el-icon><Fold /></el-icon>
                <span class="text-xs">收起</span>
             </el-button>
          </div>
       </div>

       <div class="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-8">
          
          <!-- 1. Templates -->
          <section class="space-y-3">
             <div class="flex items-center gap-2 mb-2">
                <div class="w-1 h-3 bg-blue-500 rounded-full"></div>
                <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">模板生成</span>
             </div>
             <div class="grid grid-cols-2 gap-2">
                <button 
                  class="flex items-center justify-center gap-2 p-2 bg-white border border-slate-200 rounded-lg hover:border-blue-400 hover:shadow-md hover:shadow-blue-50 transition-all duration-200 group"
                  @click="generateTemplate('settings')"
                >
                   <el-icon class="text-base text-slate-400 group-hover:text-blue-500 transition-colors"><Setting /></el-icon>
                   <span class="text-xs font-medium text-slate-600 group-hover:text-blue-700 font-bold transition-colors">考场设置</span>
                </button>
                
                <el-dropdown trigger="click" @command="generateTemplate" class="w-full">
                   <button class="flex items-center justify-center gap-2 w-full p-2 bg-white border border-slate-200 rounded-lg hover:border-blue-400 hover:shadow-md hover:shadow-blue-50 transition-all duration-200 group">
                      <el-icon class="text-base text-slate-400 group-hover:text-blue-500 transition-colors"><User /></el-icon>
                      <span class="text-xs font-medium text-slate-600 group-hover:text-blue-700 font-bold transition-colors">考生名册</span>
                      <el-icon class="text-[10px] text-slate-400 group-hover:text-blue-500 ml-0.5"><ArrowDown /></el-icon>
                   </button>
                   <template #dropdown>
                      <el-dropdown-menu class="w-[240px]">
                         <el-dropdown-item command="student_normal">
                            <div class="flex flex-col py-1">
                               <span class="font-bold">通用版 (普通)</span>
                               <span class="text-xs text-slate-400">适用于常规考试</span>
                            </div>
                         </el-dropdown-item>
                         <el-dropdown-item command="student_subject">
                            <div class="flex flex-col py-1">
                               <span class="font-bold">新高考版 (3+1+2)</span>
                               <span class="text-xs text-slate-400">包含选科组合信息</span>
                            </div>
                         </el-dropdown-item>
                      </el-dropdown-menu>
                   </template>
                </el-dropdown>
             </div>
          </section>

          <!-- 2. Data Import -->
          <section class="space-y-3">
             <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                   <div class="w-1 h-3 bg-emerald-500 rounded-full"></div>
                   <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">数据导入</span>
                </div>
                <div class="px-2 py-0.5 rounded text-[10px] font-bold transition-colors"
                     :class="students.length ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400'">
                   {{ students.length ? `${students.length} 人` : '未导入' }}
                </div>
             </div>
             <div class="grid grid-cols-2 gap-2">
                <button 
                   class="flex items-center justify-center gap-2 p-2 bg-white border border-slate-200 rounded-lg hover:border-emerald-400 hover:shadow-md hover:shadow-emerald-50 transition-all duration-200 group"
                   :class="roomSettings.length ? '!border-emerald-500 bg-emerald-50/50' : ''"
                   @click="handleImportSettings"
                >
                   <el-icon class="text-base transition-colors" :class="roomSettings.length ? 'text-emerald-600' : 'text-slate-400 group-hover:text-emerald-500'"><OfficeBuilding /></el-icon>
                   <span class="text-xs font-medium transition-colors" :class="roomSettings.length ? 'text-emerald-700 font-bold' : 'text-slate-600 group-hover:text-emerald-700'">考场设置</span>
                </button>
                <button 
                   class="flex items-center justify-center gap-2 p-2 bg-white border border-slate-200 rounded-lg hover:border-emerald-400 hover:shadow-md hover:shadow-emerald-50 transition-all duration-200 group"
                   :class="students.length ? '!border-emerald-500 bg-emerald-50/50' : ''"
                   @click="handleImportStudents"
                >
                   <el-icon class="text-base transition-colors" :class="students.length ? 'text-emerald-600' : 'text-slate-400 group-hover:text-emerald-500'"><Upload /></el-icon>
                   <span class="text-xs font-medium transition-colors" :class="students.length ? 'text-emerald-700 font-bold' : 'text-slate-600 group-hover:text-emerald-700'">考生名册</span>
                </button>
             </div>
          </section>

          <!-- 3. Parameters -->
          <section class="space-y-4">
             <div class="flex items-center gap-2 mb-2">
                <div class="w-1 h-3 bg-indigo-500 rounded-full"></div>
                <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">编排参数</span>
             </div>
             
             <div class="bg-slate-50/50 rounded-xl p-3 border border-slate-100 space-y-4">
                <div class="grid grid-cols-2 gap-3">
                   <div class="space-y-1.5">
                      <div class="text-[10px] font-bold text-slate-400 uppercase">考场数量</div>
                      <el-input-number 
                        v-model="config.totalRooms" 
                        :min="1" :max="200" 
                        size="small" 
                        class="!w-full shadow-sm"
                        controls-position="right"
                      />
                   </div>
                   <div class="space-y-1.5">
                      <div class="text-[10px] font-bold text-slate-400 uppercase">每场人数</div>
                      <el-input-number 
                        v-model="config.seatsPerRoom" 
                        :min="1" :max="100" 
                        size="small" 
                        class="!w-full shadow-sm"
                        controls-position="right"
                      />
                   </div>
                </div>

                <div class="space-y-1.5">
                   <label class="text-[10px] font-bold text-slate-400 uppercase">编排模式</label>
                   <el-select v-model="config.mode" size="default" class="w-full shadow-sm">
                     <el-option label="3+1+2选科编排" value="3+1+2">
                       <div class="flex items-center w-full">
                         <span class="truncate">3+1+2选科编排</span>
                         <el-button class="ml-auto -mr-5" link type="primary" size="small" @click.stop="openSubjectPriorityDialog">高级设置</el-button>
                       </div>
                     </el-option>
                      <el-option label="顺序编排" value="normal" />
                      <el-option label="随机编排" value="random" />
                   </el-select>
                </div>
             </div>
          </section>

          <!-- 4. Actions -->
          <section class="pt-4 mt-auto space-y-2">
             <el-button type="primary" size="default" class="!w-full !h-10 !text-sm !font-bold !rounded-lg shadow-lg shadow-blue-200 hover:shadow-blue-300 transition-all hover:-translate-y-0.5" :disabled="!canArrange" @click="handleArrange">
                智能编排
             </el-button>
             <div class="grid grid-cols-2 gap-2">
                <el-button plain size="default" class="!w-full !h-10 !rounded-lg border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-200" @click="handleImportResults">
                   <el-icon class="mr-1.5"><Upload /></el-icon> 导入结果
                </el-button>
                <el-button plain size="default" class="!w-full !h-10 !rounded-lg border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-200" :disabled="!hasResults" @click="handleExport">
                   <el-icon class="mr-1.5"><Download /></el-icon> 导出Excel
                </el-button>
             </div>
          </section>

       </div>
    </div>

    <!-- Toggle Button (Visible when collapsed) -->
    <div 
       v-if="sidebarCollapsed" 
       class="absolute left-0 top-6 z-30 bg-white border border-l-0 border-slate-200 p-2 rounded-r-xl shadow-lg cursor-pointer hover:bg-blue-50 hover:text-blue-600 transition-all hover:pl-3"
       @click="sidebarCollapsed = false"
    >
       <el-icon><Expand /></el-icon>
    </div>

    <!-- Right Main Content -->
    <div class="flex-1 flex flex-col min-w-0 h-full relative z-10">
       
       <!-- Header Area -->
       <div class="h-14 px-3 sm:px-4 flex items-center justify-between shrink-0 bg-white/80 backdrop-blur border-b border-slate-200/60 sticky top-0 z-10 gap-2 sm:gap-4">
          <div class="flex items-center flex-shrink min-w-0">
            <el-tabs v-model="activeTab" class="custom-tabs-header no-border">
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

          <!-- Top Actions (Visible in all tabs, with specific controls for results) -->
          <div class="flex items-center gap-2 shrink-0">
             <template v-if="activeTab === 'results'">
                <div class="flex items-center gap-1.5 px-2.5 py-1 bg-slate-100/80 rounded-full border border-slate-200/50 hidden xl:flex animate-fade-in">
                   <span class="w-1.5 h-1.5 rounded-full" :class="hasResults ? 'bg-emerald-500' : 'bg-slate-300'"></span>
                   <span class="text-xs font-medium text-slate-600">
                      {{ hasResults ? `${results.length}人` : '待编排' }}
                   </span>
                </div>

                <div class="h-3 w-px bg-slate-200 hidden xl:block animate-fade-in"></div>

                <div class="flex items-center gap-2 animate-fade-in">
                <el-input
                  v-model="searchQuery"
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
                  @click="showLogs = true"
                >
                   <el-icon :size="18"><CollectionTag /></el-icon>
                   <span v-if="logs.length > 0 && !showLogs" class="absolute top-1 right-1 w-1.5 h-1.5 bg-red-500 rounded-full border border-white"></span>
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
                      <span class="text-xs text-slate-500">已加载 {{ roomSettings.length }} 个标准考场</span>
                   </div>
                </div>
                <el-button size="small" @click="handleImportSettings">重新导入</el-button>
             </div>
             <el-table 
               :data="roomSettings" 
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
                <el-button size="small" @click="handleImportStudents">重新导入</el-button>
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
               v-model:current-page="studentCurrentPage"
               v-model:page-size="studentPageSize"
               :total="students.length"
               :page-sizes="[50, 100, 200]"
             />
          </div>

          <!-- Tab 3: Results -->
          <div v-show="activeTab === 'results'" class="h-full w-full flex flex-col bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <!-- List View -->
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
                    <el-table-column type="index" label="序号" width="60" align="center" :index="indexMethod" fixed />
                    
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
                    
                    <el-table-column v-if="config.mode === '3+1+2'" prop="考场选科组合" label="考场选科组合" min-width="120" show-overflow-tooltip />
                 </el-table>

                 <!-- Pagination for Results -->
                 <BasePagination
                   v-model:current-page="currentPage"
                   v-model:page-size="pageSize"
                   :total="filteredResults.length"
                 />
              </div>
          </div>

       </div>
    </div>

    <!-- Logs Drawer -->
    <el-dialog
      v-model="showSubjectPriorityDialog"
      title="选科编排高级设置"
      width="520px"
      align-center
      :close-on-click-modal="false"
    >
      <div class="space-y-3">
        <div class="text-sm text-slate-600">
          从上到下表示考试优先级从高到低（用于“考试顺序建议”的分段规则）。
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50/50 divide-y divide-slate-200">
          <div
            v-for="(subj, idx) in subjectPriorityDraft"
            :key="subj"
            class="flex items-center justify-between px-3 py-2"
            :class="dragOverSubjectIndex === idx ? 'bg-blue-50/60' : ''"
            @dragover.prevent="onSubjectDragOver(idx)"
            @dragenter.prevent="onSubjectDragOver(idx)"
            @drop.prevent="onSubjectDrop(idx)"
          >
            <div class="flex items-center gap-2 min-w-0">
              <div
                class="w-5 h-8 rounded flex flex-col items-center justify-center text-slate-400 hover:text-slate-600 cursor-move select-none"
                draggable="true"
                @dragstart="onSubjectDragStart(idx)"
                @dragend="onSubjectDragEnd"
              >
                <span class="leading-[8px] text-xs">⋮</span>
                <span class="leading-[8px] text-xs">⋮</span>
              </div>
              <div class="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-700 shrink-0">
                {{ idx + 1 }}
              </div>
              <div class="font-bold text-slate-800 truncate">{{ subj }}</div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <el-button size="small" :disabled="idx === 0" @click="moveSubjectPriority(idx, -1)">上移</el-button>
              <el-button size="small" :disabled="idx === subjectPriorityDraft.length - 1" @click="moveSubjectPriority(idx, 1)">下移</el-button>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-between w-full">
          <el-button @click="resetSubjectPriorityDraft">恢复默认</el-button>
          <div class="flex gap-2">
            <el-button @click="showSubjectPriorityDialog = false">取消</el-button>
            <el-button type="primary" :loading="savingSubjectPriority" @click="saveSubjectPriority">保存</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <el-drawer 
      v-model="showLogs" 
      title="系统操作日志" 
      direction="rtl" 
      size="380px"
      :modal="false"
      class="!shadow-2xl"
    >
       <div class="flex flex-col h-full">
          <div class="flex justify-between items-center mb-6 px-1">
             <span class="text-xs text-slate-400">记录最近的操作与状态</span>
             <el-button size="small" type="danger" plain @click="logs = []" :disabled="logs.length === 0">
                <el-icon class="mr-1"><Delete /></el-icon> 清空
             </el-button>
          </div>
          <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-4">
             <div v-if="logs.length === 0" class="flex flex-col items-center justify-center h-[300px] text-slate-300">
                <el-icon class="text-5xl mb-3 opacity-20"><CollectionTag /></el-icon>
                <span class="text-sm">暂无日志记录</span>
             </div>
             <div v-else class="relative pl-6 border-l border-slate-100 ml-3 space-y-6">
                <div v-for="(log, idx) in logs" :key="idx" class="relative group animate-fade-in">
                   <!-- Timeline Dot -->
                   <div class="absolute -left-[29px] top-1.5 w-3 h-3 rounded-full border-2 border-white shadow-sm transition-all duration-300 group-hover:scale-110"
                        :class="{
                           'bg-blue-500 shadow-blue-200': log.level === 'info',
                           'bg-emerald-500 shadow-emerald-200': log.level === 'success',
                           'bg-amber-500 shadow-amber-200': log.level === 'warning',
                           'bg-rose-500 shadow-rose-200': log.level === 'error'
                        }"></div>
                   
                   <div class="flex items-center justify-between mb-1">
                      <span class="text-[10px] font-mono text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded">{{ log.time }}</span>
                   </div>
                   <div class="text-sm text-slate-600 break-words group-hover:text-slate-900 transition-colors bg-white p-3 rounded-xl border border-slate-100 shadow-sm group-hover:shadow-md group-hover:border-blue-100 group-hover:bg-blue-50/30">
                      {{ log.msg }}
                   </div>
                </div>
             </div>
          </div>
       </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Setting, User, ArrowDown, OfficeBuilding, Upload, Download, Fold, Expand, Search, CollectionTag, Delete, Check } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { open, saveAndRun } from '@/lib/dialog'
import { pythonBackend } from '@/lib/pythonBackend'
import BasePagination from '@/components/BasePagination.vue'
import dayjs from 'dayjs'

// --- State ---
// Persistence Helper
const getStored = (key: string, def: string) => sessionStorage.getItem(`rooms_pref_${key}`) || def
const getCache = (key: string, def: string) => sessionStorage.getItem(`rooms_cache_${key}`) || def

const sidebarCollapsed = ref(getStored('sidebarCollapsed', 'false') === 'true')
const activeTab = ref(getStored('activeTab', 'settings')) // results, settings, students
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const showLogs = ref(false)
type UiLogLevel = 'info' | 'success' | 'warning' | 'error'
const logs = ref<{ time: string; level: UiLogLevel; msg: string }[]>([])

// Persistence Watchers
watch(sidebarCollapsed, (val) => sessionStorage.setItem('rooms_pref_sidebarCollapsed', String(val)))
watch(activeTab, (val) => sessionStorage.setItem('rooms_pref_activeTab', val))

// Student Pagination State
const studentCurrentPage = ref(1)
const studentPageSize = ref(50)

type RoomsConfig = {
  totalRooms: number
  seatsPerRoom: number
  mode: string
  subjectPriorityOrder: string[]
}

const SUBJECT_PRIORITY_DEFAULT = ['化学', '生物', '政治', '地理']

const config = reactive<RoomsConfig>({
  totalRooms: 30,
  seatsPerRoom: 30,
  mode: 'normal',
  subjectPriorityOrder: [...SUBJECT_PRIORITY_DEFAULT]
})

const students = ref<any[]>([])
const results = ref<any[]>([])
const roomSettings = ref<any[]>([])
const cachedResultsPath = ref(getCache('resultsPath', ''))

// --- Computed ---
const canArrange = computed(() => students.value.length > 0)
const hasResults = computed(() => results.value.length > 0)

const filteredResults = computed(() => {
   if (!searchQuery.value) return results.value
   const q = searchQuery.value.toLowerCase()
   return results.value.filter(r => 
      String(r['姓名']).toLowerCase().includes(q) || 
      String(r['考号']).toLowerCase().includes(q)
   )
})

const pagedResults = computed(() => {
   const start = (currentPage.value - 1) * pageSize.value
   return filteredResults.value.slice(start, start + pageSize.value)
})

const pagedStudents = computed(() => {
   const start = (studentCurrentPage.value - 1) * studentPageSize.value
   return students.value.slice(start, start + studentPageSize.value)
})

// --- Methods ---
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

const indexMethod = (index: number) => {
   return (currentPage.value - 1) * pageSize.value + index + 1
}

const studentIndexMethod = (index: number) => {
   return (studentCurrentPage.value - 1) * studentPageSize.value + index + 1
}

const generateTemplate = async (type: string) => {
   await saveAndRun({
      dialog: {
         filters: [{ name: 'Excel', extensions: ['xlsx'] }],
         defaultPath: type === 'settings' ? '考场设置模板.xlsx' : '考生名册模板.xlsx'
      },
      run: async (path) => {
         return await pythonBackend.request<any>('rooms.generateTemplate', { type, path })
      },
      successText: '模板生成成功',
      errorText: '生成模板失败',
      onLog: logFromText,
   })
}

const handleImportSettings = async () => {
   const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }] })
   if (path) {
      const res = await pythonBackend.request<any>('rooms.importSettings', { path })
      if (res?.error) {
         ElMessage.error(res.error)
         logError(`导入考场设置失败：${res.error}`)
      } else if (res?.settings) {
         roomSettings.value = res.settings
         config.totalRooms = res.settings.length
         // Try to detect capacity
         if (res.settings.length > 0) {
            config.seatsPerRoom = res.settings[0].capacity || 30
         }
         ElMessage.success(`成功导入 ${res.settings.length} 个考场设置`)
         logSuccess(`已导入考场设置：${res.settings.length} 个考场`)
         activeTab.value = 'settings'
      }
   }
}

const handleImportStudents = async () => {
   const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }] })
   if (path) {
      studentPath.value = path as string // Save path
      const res = await pythonBackend.request<any>('rooms.importStudents', { path })
      if (res?.error) {
         ElMessage.error(res.error)
         logError(`导入考生名册失败：${res.error}`)
      } else if (res?.students) {
         students.value = res.students
         ElMessage.success(`成功导入 ${res.total} 名考生`)
         logSuccess(`已导入考生名册：${res.total} 人`)
         activeTab.value = 'students'
      }
   }
}

const handleArrange = async () => {
   if (!studentPath.value) {
      ElMessage.warning('请先导入考生名册')
      return
   }

   logInfo('开始考场编排')
   try {
      const res = await pythonBackend.request<any>('rooms.arrange', {
         studentPath: studentPath.value,
         settings: roomSettings.value,
         config
      })
      
      if (res?.error) {
         ElMessage.error(res.error)
         logError(`编排失败：${res.error}`)
      } else if (res?.results) {
         results.value = res.results
         ElMessage.success('编排完成')
         logSuccess(`编排完成：共 ${res.results.length} 人`)
         activeTab.value = 'results'
      }
   } catch(e) {
      ElMessage.error('编排失败: ' + e)
      logError(`编排异常：${e instanceof Error ? e.message : String(e)}`)
   }
}

const handleExport = async () => {
   await saveAndRun({
      dialog: { filters: [{ name: 'Excel', extensions: ['xlsx'] }], defaultPath: '考场编排结果.xlsx' },
      run: async (path) => {
         return await pythonBackend.request<any>('rooms.export', { path })
      },
      successText: '导出成功',
      errorText: '导出失败',
      onLog: logFromText,
   })
}

const handleImportResults = async () => {
   const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }] })
   if (path) {
      const res = await pythonBackend.request<any>('rooms.importResults', { path })
      if (res?.error) {
         ElMessage.error(res.error)
         logError(`导入编排结果失败：${res.error}`)
      } else if (res?.results) {
         results.value = res.results
         cachedResultsPath.value = String(path)
         sessionStorage.setItem('rooms_cache_resultsPath', cachedResultsPath.value)
         ElMessage.success('导入成功')
         logSuccess(`已导入编排结果：共 ${res.results.length} 人`)
         activeTab.value = 'results'
      }
   }
}

const handleResetPage = async () => {
   try {
      await ElMessageBox.confirm(
         '确定要初始化当前页面吗？这将清除所有考场数据与设置。',
         '初始化页面',
         { type: 'warning', confirmButtonText: '初始化', cancelButtonText: '取消' }
      )
   } catch {
      return
   }

   const res = await pythonBackend.request<any>('rooms.resetState', {})
   if (res?.error) {
      ElMessage.error(res.error)
      logError(`初始化失败：${res.error}`)
      return
   }

   roomSettings.value = []
   students.value = []
   results.value = []
   studentPath.value = ''
   logs.value = []
   showLogs.value = false
   cachedResultsPath.value = ''
   sessionStorage.removeItem('rooms_cache_resultsPath')

   searchQuery.value = ''
   currentPage.value = 1
   pageSize.value = 50
   studentCurrentPage.value = 1
   studentPageSize.value = 50

   config.totalRooms = 30
   config.seatsPerRoom = 30
   config.mode = 'normal'

   sidebarCollapsed.value = false
   activeTab.value = 'settings'

   sessionStorage.removeItem('rooms_pref_sidebarCollapsed')
   sessionStorage.removeItem('rooms_pref_activeTab')

   logInfo('已初始化考场编排页面')
}

// Additional state for path
const studentPath = ref('')

const showSubjectPriorityDialog = ref(false)
const savingSubjectPriority = ref(false)
const subjectPriorityDraft = ref<string[]>([...SUBJECT_PRIORITY_DEFAULT])
const draggingSubjectIndex = ref<number | null>(null)
const dragOverSubjectIndex = ref<number | null>(null)

const normalizeSubjectPriorityOrder = (order: unknown): string[] => {
  const allowed = SUBJECT_PRIORITY_DEFAULT
  if (!Array.isArray(order)) return [...allowed]
  const cleaned = order.map((v) => String(v || '').trim()).filter((v) => allowed.includes(v))
  const dedup: string[] = []
  for (const s of cleaned) {
    if (!dedup.includes(s)) dedup.push(s)
  }
  for (const s of allowed) {
    if (!dedup.includes(s)) dedup.push(s)
  }
  return dedup.slice(0, allowed.length)
}

const openSubjectPriorityDialog = () => {
  config.subjectPriorityOrder = normalizeSubjectPriorityOrder(config.subjectPriorityOrder)
  subjectPriorityDraft.value = [...config.subjectPriorityOrder]
  showSubjectPriorityDialog.value = true
}

const moveSubjectPriority = (index: number, delta: number) => {
  const nextIndex = index + delta
  if (nextIndex < 0 || nextIndex >= subjectPriorityDraft.value.length) return
  const arr = [...subjectPriorityDraft.value]
  const tmp = arr[index]
  arr[index] = arr[nextIndex]
  arr[nextIndex] = tmp
  subjectPriorityDraft.value = arr
}

const onSubjectDragStart = (index: number) => {
  draggingSubjectIndex.value = index
}

const onSubjectDragOver = (index: number) => {
  if (draggingSubjectIndex.value == null) return
  if (dragOverSubjectIndex.value === index) return
  dragOverSubjectIndex.value = index
}

const onSubjectDrop = (targetIndex: number) => {
  const from = draggingSubjectIndex.value
  if (from == null) return
  if (from === targetIndex) return

  const arr = [...subjectPriorityDraft.value]
  const [moved] = arr.splice(from, 1)
  arr.splice(targetIndex, 0, moved)
  subjectPriorityDraft.value = arr
  draggingSubjectIndex.value = null
  dragOverSubjectIndex.value = null
}

const onSubjectDragEnd = () => {
  draggingSubjectIndex.value = null
  dragOverSubjectIndex.value = null
}

const resetSubjectPriorityDraft = () => {
  subjectPriorityDraft.value = [...SUBJECT_PRIORITY_DEFAULT]
}

const saveSubjectPriority = async () => {
  const normalized = normalizeSubjectPriorityOrder(subjectPriorityDraft.value)
  savingSubjectPriority.value = true
  try {
    const res = await pythonBackend.request<any>('rooms.setSubjectPriority', { order: normalized })
    if (res?.error) {
      ElMessage.error(res.error)
      logError(`保存高级设置失败：${res.error}`)
      return
    }
    config.subjectPriorityOrder = [...normalized]
    ElMessage.success('高级设置已保存')
    logSuccess(`高级设置已保存：${normalized.join(' > ')}`)
    showSubjectPriorityDialog.value = false
  } catch (e) {
    ElMessage.error('保存失败: ' + e)
    logError(`保存高级设置异常：${e instanceof Error ? e.message : String(e)}`)
  } finally {
    savingSubjectPriority.value = false
  }
}

onMounted(async () => {
   let res: any = null
   try {
      res = await pythonBackend.request<any>('rooms.getState')
   } catch (e) {
      logError(`加载状态失败：${e instanceof Error ? e.message : String(e)}`)
   }

   if (res) {
      if (res.settings) roomSettings.value = res.settings
      if (res.students) students.value = res.students
      if (res.results) results.value = res.results
      if (res.config) Object.assign(config, res.config)
      if (res.studentPath) studentPath.value = res.studentPath
   }

   config.subjectPriorityOrder = normalizeSubjectPriorityOrder((res?.config || {}).subjectPriorityOrder ?? config.subjectPriorityOrder)

   if ((!results.value || results.value.length === 0) && cachedResultsPath.value) {
      try {
         const r = await pythonBackend.request<any>('rooms.importResults', { path: cachedResultsPath.value })
         if (r?.results) {
            results.value = r.results
            logInfo(`已从上次导入文件恢复编排结果：共 ${r.results.length} 人`)
         }
      } catch (e) {
         logWarning(`自动恢复编排结果失败：${e instanceof Error ? e.message : String(e)}`)
      }
   }
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Optimize Tabs for compact layout */
:deep(.el-tabs__item) {
  padding: 0 10px !important;
  font-size: 13px;
}
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e2e8f0;
}
:deep(.el-tabs__active-bar) {
  height: 2px;
  background-color: #3b82f6;
}

/* Hide scrollbar for Chrome, Safari and Opera */
.custom-scrollbar::-webkit-scrollbar {
  display: none;
}
/* Hide scrollbar for IE, Edge and Firefox */
.custom-scrollbar {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
</style>

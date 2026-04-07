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
             <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-200">
                <el-icon :size="16"><Setting /></el-icon>
             </div>
             <span class="font-bold text-slate-800 text-base tracking-tight">监考配置</span>
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
                   <div class="w-1 h-3 bg-blue-500 rounded-full"></div>
                   <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">数据源</span>
                </div>
                <div class="px-2 py-0.5 rounded text-[10px] font-bold transition-colors"
                     :class="teachers.length ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-400'">
                   {{ teachers.length ? `已导入 ${teachers.length} 人` : '未导入' }}
                </div>
             </div>
             <div class="grid grid-cols-2 gap-2">
                <button 
                   class="flex items-center justify-center gap-2 p-2 pr-7 bg-white border border-slate-200 rounded-lg hover:border-blue-400 hover:shadow-md hover:shadow-blue-50 transition-all duration-200 group relative"
                   :class="teachers.length ? '!border-blue-500 bg-blue-50/50' : ''"
                   @click="handleAddTeacher"
                >
                   <el-icon class="text-base transition-colors" :class="teachers.length ? 'text-blue-600' : 'text-slate-400 group-hover:text-blue-500'"><Upload /></el-icon>
                   <span class="text-xs font-medium transition-colors" :class="teachers.length ? 'text-blue-700 font-bold' : 'text-slate-600 group-hover:text-blue-700'">导入教师</span>
                   <span
                      v-if="teachers.length"
                      class="absolute right-1 top-1/2 -translate-y-1/2 w-5 h-5 rounded flex items-center justify-center text-blue-600 hover:bg-blue-100 transition-colors"
                      @click.stop.prevent="handleClearTeachers"
                   >×</span>
                </button>
                <button 
                  class="flex items-center justify-center gap-2 p-2 bg-white border border-slate-200 rounded-lg hover:border-blue-400 hover:shadow-md hover:shadow-blue-50 transition-all duration-200 group"
                  @click="handleTemplate"
                >
                   <el-icon class="text-base text-slate-400 group-hover:text-blue-500 transition-colors"><Download /></el-icon>
                   <span class="text-xs font-medium text-slate-600 group-hover:text-blue-700">教师模板</span>
                </button>
             </div>
             
             <div class="grid grid-cols-2 gap-2">
                <button 
                   class="flex items-center justify-center gap-2 p-2 pr-7 bg-white border border-slate-200 rounded-lg hover:border-indigo-400 hover:shadow-md hover:shadow-indigo-50 transition-all duration-200 group relative"
                   :class="hasPreset ? '!border-indigo-500 bg-indigo-50/50' : ''"
                   @click="handlePresetDialog"
                >
                   <el-icon class="transition-colors" :class="hasPreset ? 'text-indigo-600' : 'text-slate-400 group-hover:text-indigo-500'"><List /></el-icon>
                   <span class="text-xs transition-colors" :class="hasPreset ? 'text-indigo-700 font-bold' : 'text-slate-600 group-hover:text-indigo-700'">预设监考</span>
                   <span
                      v-if="hasPreset"
                      class="absolute right-1 top-1/2 -translate-y-1/2 w-5 h-5 rounded flex items-center justify-center text-indigo-600 hover:bg-indigo-100 transition-colors"
                      @click.stop.prevent="handleClearPreset"
                   >×</span>
                </button>
                <button 
                   class="flex items-center justify-center gap-2 p-2 bg-white border border-slate-200 rounded-lg hover:border-indigo-400 hover:shadow-md hover:shadow-indigo-50 transition-all duration-200 group"
                   @click="handleImportSchedule"
                >
                   <el-icon class="text-slate-400 group-hover:text-indigo-500"><Upload /></el-icon>
                   <span class="text-xs text-slate-600 group-hover:text-indigo-700">导入安排</span>
                </button>
             </div>
          </section>

          <!-- 2. Parameters -->
          <section class="space-y-4">
             <div class="flex items-center gap-2 mb-2">
                <div class="w-1 h-3 bg-indigo-500 rounded-full"></div>
                <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">参数设置</span>
             </div>
             
             <div class="bg-slate-50/50 rounded-xl p-3 border border-slate-100 space-y-4">
                <div class="space-y-1.5">
                   <div class="flex justify-between text-[10px] font-bold text-slate-400 uppercase">
                      <span>考场数量</span>
                      <el-tooltip content="科目数量需从“科目设置”功能页中调整" placement="top">
                         <span class="cursor-help border-b border-dashed border-slate-300 text-indigo-400">科目: {{ subjectCount }}</span>
                      </el-tooltip>
                   </div>
                   <el-input-number 
                     v-model="config.roomCount" 
                     :min="0" :max="200" 
                     size="small" 
                     class="!w-full shadow-sm"
                     controls-position="right"
                   />
                </div>

                <div class="space-y-1.5">
                   <div class="flex items-center justify-between">
                      <label class="text-[10px] font-bold text-slate-400 uppercase">监考模式</label>
                      <el-popover placement="bottom" title="约束条件" :width="200" trigger="click" v-if="config.mode === 'double'">
                         <template #reference>
                           <el-button link size="small" class="!p-0 !h-auto">
                              <el-icon class="text-slate-400 hover:text-indigo-500"><Setting /></el-icon>
                           </el-button>
                         </template>
                         <div class="space-y-2 py-2">
                            <el-checkbox v-model="config.genderMix" label="男女搭配" size="small" class="!mr-0 !w-full" />
                            <el-checkbox v-model="config.internalMix" label="本外校搭配" size="small" class="!mr-0 !w-full" />
                         </div>
                      </el-popover>
                   </div>
                   <el-segmented v-model="config.mode" :options="[
                      { label: '单人监考', value: 'single' },
                      { label: '双人监考', value: 'double' }
                   ]" block size="small" class="custom-segmented" />
                </div>

                <div class="space-y-1.5">
                   <label class="text-[10px] font-bold text-slate-400 uppercase">均衡策略</label>
                   <el-segmented v-model="config.balanceMode" :options="[
                      { label: '时长均衡', value: 'duration' },
                      { label: '场次均衡', value: 'session' }
                   ]" block size="small" class="custom-segmented" />
                </div>
             </div>
          </section>

          <!-- 3. Actions -->
          <section class="pt-4 mt-auto space-y-3">
             <el-button type="primary" size="large" class="w-full !h-12 !text-base !font-bold !rounded-xl shadow-lg shadow-indigo-200 hover:shadow-indigo-300 transition-all hover:-translate-y-0.5" :disabled="!canSchedule" @click="handleSmartSchedule">
                开始智能编排
             </el-button>
             
             <div class="grid grid-cols-2 gap-2">
               <el-button 
                 class="!rounded-lg" 
                 :type="adjustMode ? 'danger' : ''" 
                 plain 
                 :disabled="!hasSchedule" 
                 @click="toggleAdjustMode"
               >
                  {{ adjustMode ? '退出调整' : '手动调整模式' }}
               </el-button>

               <el-button plain size="default" class="!rounded-lg border-slate-200 text-slate-600 hover:text-indigo-600 hover:border-indigo-200" :disabled="!hasSchedule" @click="handleExport">
                  <el-icon class="mr-1.5"><Download /></el-icon> 导出安排
               </el-button>
             </div>

             <el-button type="danger" plain class="w-full !rounded-lg" :disabled="!hasSchedule" @click="handleClearSchedule">
                <el-icon class="mr-1.5"><Delete /></el-icon> 清除当前编排
             </el-button>
          </section>

       </div>
    </div>

    <!-- Toggle Button (Visible when collapsed) -->
    <div 
       v-if="sidebarCollapsed" 
       class="absolute left-0 top-6 z-30 bg-white border border-l-0 border-slate-200 p-2 rounded-r-xl shadow-lg cursor-pointer hover:bg-indigo-50 hover:text-indigo-600 transition-all hover:pl-3"
       @click="sidebarCollapsed = false"
    >
       <el-icon><Expand /></el-icon>
    </div>

    <!-- Right Main Content -->
    <div class="flex-1 flex flex-col min-w-0 h-full relative z-10">
       
       <!-- Top Bar -->
       <div class="h-14 bg-white/80 backdrop-blur border-b border-slate-200/60 px-4 flex items-center justify-between shrink-0 sticky top-0 z-10 gap-4">
          <div class="flex items-center gap-4 flex-shrink min-w-0">
             <h2 class="text-base font-bold text-slate-700 truncate">监考安排结果</h2>
             <div class="flex items-center gap-2 px-2.5 py-1 bg-slate-100/80 rounded-full border border-slate-200/50 hidden md:flex">
                <span class="text-xs text-slate-500">状态:</span>
                <span 
                   class="text-xs font-bold"
                   :class="hasSchedule ? (missingSlots === 0 ? 'text-emerald-600' : 'text-amber-600') : 'text-slate-400'"
                >
                   {{ hasSchedule ? (missingSlots === 0 ? '已排满' : `未排满 (缺 ${missingSlots})`) : '等待编排' }}
                </span>
             </div>
             <div v-if="adjustMode" class="px-2 py-0.5 bg-rose-100 text-rose-600 text-xs rounded border border-rose-200 animate-pulse font-bold">
                手动调整模式开启
             </div>
          </div>

          <div class="flex items-center gap-3 shrink-0">
             <!-- Legend -->
             <div class="flex items-center gap-3 text-xs text-slate-400 mr-2 hidden xl:flex">
               <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-rose-500"></span><span>锁定</span></div>
               <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500"></span><span>预设</span></div>
               <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-blue-500"></span><span>男</span></div>
               <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-fuchsia-500"></span><span>女</span></div>
             </div>

             <div class="w-px h-3 bg-slate-200 hidden xl:block"></div>

             <el-tooltip content="操作日志" placement="bottom">
                <button 
                  class="w-7 h-7 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-500 hover:text-indigo-600 transition-colors relative"
                  @click="showLogs = true"
                >
                   <el-icon :size="16"><CollectionTag /></el-icon>
                   <el-badge :is-dot="logs.length > 0 && !showLogs" type="primary" :offset="[-2, 2]" class="absolute top-0 right-0" />
                </button>
             </el-tooltip>
          </div>
       </div>

       <!-- Table Area -->
       <div class="flex-1 overflow-hidden relative p-4">
          <div class="h-full w-full bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
              <!-- Result Header -->
              <div class="h-12 border-b border-slate-100 flex items-center justify-between px-4 bg-slate-50/50">
                  <div class="flex items-center gap-4">
                      <h3 class="text-sm font-bold text-slate-700">监考安排结果</h3>
                      <!-- Custom Segmented Tabs -->
                      <div class="bg-slate-200/50 p-0.5 rounded-lg flex text-xs font-medium">
                          <button 
                             class="px-3 py-1 rounded-md transition-all"
                             :class="activeTab === 'overview' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                             @click="activeTab = 'overview'"
                          >监考总览</button>
                          <button 
                             class="px-3 py-1 rounded-md transition-all"
                             :class="activeTab === 'stats' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                             @click="activeTab = 'stats'"
                          >监考统计</button>
                          <button 
                             class="px-3 py-1 rounded-md transition-all"
                             :class="activeTab === 'subject' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                             @click="activeTab = 'subject'"
                          >科目视图</button>
                      </div>
                  </div>
                  
                  <!-- Status Indicator -->
                  <div class="flex items-center gap-2">
                     <span v-if="!hasSchedule" class="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">状态: 等待编排</span>
                     <span v-else-if="missingSlots > 0" class="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <el-icon><Warning /></el-icon> 未完成 (缺 {{ missingSlots }} 人次)
                     </span>
                     <span v-else class="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <el-icon><CircleCheck /></el-icon> 已完成
                     </span>
                  </div>
              </div>

              <!-- Content Area (Manual Tab Switch) -->
              <div class="flex-1 overflow-hidden relative">
                  
                 <!-- Overview Tab -->
                 <div v-show="activeTab === 'overview'" class="h-full w-full">
                   <el-table 
                     :data="matrixData" 
                     border 
                     height="100%" 
                     style="width: 100%"
                     :cell-style="getCellStyle"
                     @cell-click="handleCellClick"
                     :header-cell-style="{ background: '#f8fafc', color: '#475569', height: '40px', padding: '4px 0', fontSize: '12px', fontWeight: '600' }"
                     :row-style="{ height: '40px' }"
                     size="small"
                   >
                     <el-table-column fixed prop="roomId" label="考场" width="80" align="center">
                       <template #default="scope">
                         <div class="flex flex-col items-center justify-center py-1">
                            <span class="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">#{{ scope.row.roomId }}</span>
                         </div>
                       </template>
                     </el-table-column>
                   
                   <template v-if="config.mode === 'double'">
                      <el-table-column 
                         v-for="sub in subjects" 
                         :key="sub.id" 
                         :label="sub.name" 
                         align="center"
                       >
                         <template #header>
                            <div class="leading-none py-1">
                               <div class="text-slate-600 font-bold">{{ sub.name }}</div>
                               <div class="text-[10px] text-slate-400 font-normal mt-0.5">{{ sub.time }}</div>
                            </div>
                         </template>
                         <el-table-column :prop="`sub_${sub.id}_1`" label="监考员1" min-width="85" align="center">
                            <template #default="{ row }">
                              <span class="text-xs cursor-pointer" :class="getTeacherTextClass(sub.id, row.roomId, 0)">
                                {{ getTeacherText(sub.id, row.roomId, 0) }}
                              </span>
                            </template>
                         </el-table-column>
                         <el-table-column :prop="`sub_${sub.id}_2`" label="监考员2" min-width="85" align="center">
                           <template #default="{ row }">
                             <span class="text-xs cursor-pointer" :class="getTeacherTextClass(sub.id, row.roomId, 1)">
                               {{ getTeacherText(sub.id, row.roomId, 1) }}
                             </span>
                           </template>
                         </el-table-column>
                      </el-table-column>
                   </template>
                   <template v-if="config.mode !== 'double'">
                      <el-table-column 
                         v-for="sub in subjects" 
                         :key="sub.id" 
                         :prop="`sub_${sub.id}`" 
                         min-width="110" 
                         align="center"
                       >
                         <template #header>
                             <div class="leading-tight py-1">
                                <div class="text-slate-600 font-bold">{{ sub.name }}</div>
                                <div class="text-[10px] font-normal text-slate-400 scale-90">{{ sub.time }}</div>
                             </div>
                          </template>
                         <template #default="{ row }">
                           <span class="text-sm cursor-pointer" :class="getTeacherTextClass(sub.id, row.roomId, 0)">
                             {{ getTeacherText(sub.id, row.roomId, 0) }}
                           </span>
                         </template>
                       </el-table-column>
                   </template>
                 </el-table>
                 </div>
 
                  <!-- Stats Tab -->
                  <div v-show="activeTab === 'stats'" class="h-full w-full">
                     <el-table :data="teacherStats" border stripe height="100%" style="width: 100%" size="small">
                      <el-table-column prop="name" label="教师姓名" min-width="100" align="center" fixed />
                      <el-table-column prop="gender" label="性别" min-width="60" align="center">
                         <template #default="{ row }">
                            <el-tag size="small" :type="row.gender === 'M' ? '' : 'danger'" effect="plain" class="!border-0">
                               {{ row.gender === 'M' ? '男' : '女' }}
                            </el-tag>
                         </template>
                      </el-table-column>
                      <el-table-column prop="isInternal" label="是否本校" min-width="80" align="center">
                         <template #default="{ row }">
                            <el-icon v-if="row.isInternal" class="text-emerald-500"><CircleCheck /></el-icon>
                         </template>
                      </el-table-column>
                      <el-table-column prop="maxSessions" label="最大监考段数" min-width="110" align="center" />
                     <el-table-column label="剩余监考次数" min-width="110" align="center">
                         <template #default="{ row }">
                            <span :class="(row.maxSessions - row.sessions) < 0 ? 'text-rose-500 font-bold' : 'text-slate-600'">
                               {{ row.maxSessions - row.sessions }}
                            </span>
                         </template>
                      </el-table-column>
                      
                      <el-table-column prop="unavailableSubjects" label="不监考科目" min-width="120" align="center">
                          <template #default="{ row }">
                              <el-tooltip v-if="row.unavailableSubjects && row.unavailableSubjects.length" :content="getUnavailableNames(row.unavailableSubjects)" placement="top">
                                <span class="text-xs text-slate-500 truncate block cursor-help">
                                    {{ getUnavailableNames(row.unavailableSubjects) }}
                                </span>
                              </el-tooltip>
                          </template>
                      </el-table-column>
                      
                      <!-- Per Subject Status -->
                      <el-table-column v-for="sub in subjects" :key="sub.id" :label="sub.name" min-width="90" align="center">
                         <template #default="{ row }">
                            <div v-if="row.subjectStatus[sub.id]" class="w-2.5 h-2.5 rounded-full bg-blue-500 mx-auto"></div>
                         </template>
                      </el-table-column>
   
                      <el-table-column prop="sessions" label="监考次数" min-width="90" align="center" />
                      
                      <el-table-column prop="supervisionDuration" label="监考时长(分钟)" min-width="130" align="center">
                         <template #default="{ row }">{{ row.supervisionDuration || 0 }}</template>
                      </el-table-column>
                      
                      <el-table-column prop="previousSupervisionDuration" label="历次监考时长(分钟)" min-width="150" align="center">
                         <template #default="{ row }">{{ row.previousSupervisionDuration || 0 }}</template>
                      </el-table-column>

                      <el-table-column prop="totalDuration" label="总监考时长(分钟)" min-width="150" align="center">
                         <template #default="{ row }">{{ (row.supervisionDuration || 0) + (row.previousSupervisionDuration || 0) }}</template>
                      </el-table-column>
                   </el-table>
                   </div>
 
                  <!-- Subject Tab -->
                  <div v-show="activeTab === 'subject'" class="h-full flex flex-col">
                     <div class="p-3 border-b border-slate-100 bg-slate-50 flex items-center gap-3">
                   <span class="text-sm text-slate-600">查看科目:</span>
                   <el-select v-model="selectedSubjectId" placeholder="请选择科目" size="small" class="w-48">
                      <el-option v-for="sub in subjects" :key="sub.id" :label="sub.name" :value="sub.id" />
                   </el-select>
                </div>
                <div class="flex-1 overflow-auto">
                   <el-table :data="subjectTableData" border stripe height="100%" style="width: 100%" size="small">
                      <el-table-column prop="roomLabel" label="考场" width="100" align="center" />
                      <template v-if="config.mode === 'double'">
                        <el-table-column prop="t1_name" label="监考员1" align="center">
                          <template #default="{ row }">
                            <span :class="row.t1_class">{{ row.t1_name }}</span>
                          </template>
                        </el-table-column>
                        <el-table-column prop="t1_gender" label="性别" align="center" width="60" />
                        <el-table-column prop="t1_source" label="来源" align="center" width="80" />
                        <el-table-column prop="t2_name" label="监考员2" align="center">
                          <template #default="{ row }">
                            <span :class="row.t2_class">{{ row.t2_name }}</span>
                          </template>
                        </el-table-column>
                        <el-table-column prop="t2_gender" label="性别" align="center" width="60" />
                        <el-table-column prop="t2_source" label="来源" align="center" width="80" />
                     </template>
                     <template v-if="config.mode !== 'double'">
                        <el-table-column prop="t1_name" label="监考教师" align="center">
                          <template #default="{ row }">
                            <span :class="row.t1_class">{{ row.t1_name }}</span>
                          </template>
                        </el-table-column>
                        <el-table-column prop="t1_gender" label="性别" align="center" />
                        <el-table-column prop="t1_source" label="来源" align="center" />
                     </template>
                   </el-table>
                </div>
             </div>
              </div>
          </div>
       </div>
    </div>

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
                           'bg-blue-500': log.level === 'info',
                           'bg-emerald-500': log.level === 'success',
                           'bg-rose-500': log.level === 'error',
                           'bg-amber-500': log.level === 'warning'
                        }"></div>
                   
                   <div class="text-xs text-slate-400 font-mono mb-0.5">{{ log.time }}</div>
                   <div class="text-sm text-slate-700 break-words group-hover:text-blue-600 transition-colors bg-slate-50 p-2 rounded-lg border border-slate-100 group-hover:border-blue-100 group-hover:bg-blue-50/50">
                      {{ log.msg }}
                   </div>
                </div>
             </div>
          </div>
       </div>
    </el-drawer>

    <!-- Preset Dialog -->
    <el-dialog v-model="presetVisible" width="480px" class="preset-dialog">
       <template #header>
         <div class="flex items-center gap-3 px-1 pt-2 pb-1">
           <div class="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-300">
             <el-icon :size="18"><List /></el-icon>
           </div>
           <div class="flex flex-col gap-0.5">
             <div class="text-sm font-bold text-slate-800">预设监考安排</div>
             <div class="text-[11px] text-slate-400 leading-snug">
               先生成模板或导入已有预设表，系统会在此基础上智能补全监考。
             </div>
           </div>
         </div>
       </template>
       <div class="space-y-5">
          <div class="flex gap-3 p-3 rounded-2xl border border-dashed border-slate-200 bg-slate-50">
            <div class="mt-0.5 text-indigo-400">
              <el-icon :size="16"><InfoFilled /></el-icon>
            </div>
            <div class="space-y-1">
              <div class="text-xs text-slate-600">
                请先导入科目与教师信息，再进行预设监考，避免报错。
              </div>
              <div class="text-[11px] text-slate-400">
                预设表中的安排会被保留，缺口部分由系统自动补齐。
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <button
              class="w-full flex items-center justify-between px-4 py-3 rounded-2xl border border-slate-200 bg-white hover:bg-indigo-50/60 hover:border-indigo-400 hover:shadow-md hover:shadow-indigo-100 transition-all group"
              @click="handleGenerateEmptyTemplate"
            >
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-all">
                  <el-icon :size="18"><Download /></el-icon>
                </div>
                <div class="text-left">
                  <div class="text-sm font-semibold text-slate-800">预设模板</div>
                  <div class="text-[11px] text-slate-400">
                    基于当前科目与考场数量生成 Excel 模板，方便批量编辑。
                  </div>
                </div>
              </div>
              <el-icon :size="18" class="text-slate-300 group-hover:text-indigo-500 transition-colors"><Download /></el-icon>
            </button>

            <button
              class="w-full flex items-center justify-between px-4 py-3 rounded-2xl border border-indigo-500 bg-indigo-50 text-indigo-700 hover:bg-indigo-600 hover:text-white hover:border-indigo-600 hover:shadow-lg hover:shadow-indigo-200 transition-all group"
              @click="handleImportPreset"
            >
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center group-hover:bg-white/10 transition-all">
                  <el-icon :size="18"><Upload /></el-icon>
                </div>
                <div class="text-left">
                  <div class="text-sm font-semibold">导入预设</div>
                  <div class="text-[11px] opacity-80">
                    选择已填写好的预设监考 Excel，自动识别监考模式并校验数据。
                  </div>
                </div>
              </div>
              <el-icon :size="18" class="text-indigo-400 group-hover:text-white transition-colors"><Upload /></el-icon>
            </button>
          </div>

          <div class="flex items-center justify-between text-[11px] text-slate-400">
            <span>支持 .xlsx 格式文件</span>
            <span
              v-if="hasPreset"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-100"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              已导入预设
            </span>
          </div>
       </div>
    </el-dialog>

    <el-dialog v-model="optDetailVisible" title="二次均衡优化明细" width="90%" class="max-w-5xl" append-to-body align-center>
      <div v-if="optDetail" class="space-y-4 max-h-[75vh] overflow-y-auto pr-1 custom-scrollbar">
        <!-- Comparison Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <!-- Before -->
          <div class="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col gap-3">
            <div class="flex items-center gap-2">
               <div class="w-1.5 h-1.5 rounded-full bg-slate-400"></div>
               <span class="text-xs font-bold text-slate-500 uppercase">优化前</span>
            </div>
            <div class="grid grid-cols-2 gap-x-8 gap-y-2">
               <div class="flex flex-col gap-0.5">
                  <span class="text-[10px] text-slate-400">最大时长(全局)</span>
                  <span class="font-mono text-sm font-semibold text-slate-700">{{ optDetail.before?.max_overall ?? optDetail.before?.maxOverall ?? '-' }}</span>
               </div>
               <div class="flex flex-col gap-0.5">
                  <span class="text-[10px] text-slate-400">最大时长(本次)</span>
                  <span class="font-mono text-sm font-semibold text-slate-700">{{ optDetail.before?.max_current ?? optDetail.before?.maxCurrent ?? '-' }}</span>
               </div>
               <div class="flex flex-col gap-0.5">
                  <span class="text-[10px] text-slate-400">方差(全局)</span>
                  <span class="font-mono text-sm text-slate-600">{{ formatVariance(optDetail.before?.var_overall ?? optDetail.before?.varOverall) }}</span>
               </div>
               <div class="flex flex-col gap-0.5">
                  <span class="text-[10px] text-slate-400">方差(本次)</span>
                  <span class="font-mono text-sm text-slate-600">{{ formatVariance(optDetail.before?.var_current ?? optDetail.before?.varCurrent) }}</span>
               </div>
            </div>
          </div>
          
          <!-- After -->
          <div class="p-4 rounded-xl border border-emerald-100 bg-emerald-50/30 flex flex-col gap-3 relative overflow-hidden">
            <div class="absolute top-0 right-0 p-2 opacity-10">
               <el-icon :size="48" class="text-emerald-500"><CircleCheck /></el-icon>
            </div>
            <div class="flex items-center gap-2">
               <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
               <span class="text-xs font-bold text-emerald-600 uppercase">优化后</span>
            </div>
            <div class="grid grid-cols-2 gap-x-8 gap-y-2 relative z-10">
               <div class="flex flex-col gap-0.5">
                  <span class="text-[10px] text-emerald-600/60">最大时长(全局)</span>
                  <div class="flex items-baseline gap-2">
                     <span class="font-mono text-sm font-bold text-emerald-700">{{ optDetail.after?.max_overall ?? optDetail.after?.maxOverall ?? '-' }}</span>
                     <span class="text-[10px]" :class="getDiffClass(optDetail.before, optDetail.after, 'maxOverall')">
                        {{ getDiff(optDetail.before, optDetail.after, 'maxOverall') }}
                     </span>
                  </div>
               </div>
               <div class="flex flex-col gap-0.5">
                  <span class="text-[10px] text-emerald-600/60">最大时长(本次)</span>
                  <div class="flex items-baseline gap-2">
                     <span class="font-mono text-sm font-bold text-emerald-700">{{ optDetail.after?.max_current ?? optDetail.after?.maxCurrent ?? '-' }}</span>
                     <span class="text-[10px]" :class="getDiffClass(optDetail.before, optDetail.after, 'maxCurrent')">
                        {{ getDiff(optDetail.before, optDetail.after, 'maxCurrent') }}
                     </span>
                  </div>
               </div>
               <div class="flex flex-col gap-0.5">
                  <span class="text-[10px] text-emerald-600/60">方差(全局)</span>
                  <div class="flex items-baseline gap-2">
                     <span class="font-mono text-sm text-emerald-700">{{ formatVariance(optDetail.after?.var_overall ?? optDetail.after?.varOverall) }}</span>
                     <span class="text-[10px]" :class="getDiffClass(optDetail.before, optDetail.after, 'varOverall')">
                        {{ getDiff(optDetail.before, optDetail.after, 'varOverall') }}
                     </span>
                  </div>
               </div>
               <div class="flex flex-col gap-0.5">
                  <span class="text-[10px] text-emerald-600/60">方差(本次)</span>
                  <div class="flex items-baseline gap-2">
                     <span class="font-mono text-sm text-emerald-700">{{ formatVariance(optDetail.after?.var_current ?? optDetail.after?.varCurrent) }}</span>
                     <span class="text-[10px]" :class="getDiffClass(optDetail.before, optDetail.after, 'varCurrent')">
                        {{ getDiff(optDetail.before, optDetail.after, 'varCurrent') }}
                     </span>
                  </div>
               </div>
            </div>
          </div>
        </div>
        
        <div v-if="optDetail.earlyStopReason" class="mb-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2">
          <el-icon class="mt-0.5 text-amber-500"><Warning /></el-icon>
          <div>
             <div class="font-bold mb-0.5">提前结束</div>
             <div class="opacity-90">{{ optDetail.earlyStopReason }}</div>
          </div>
        </div>

        <el-tabs class="custom-tabs">
          <el-tab-pane label="交换明细">
            <el-table :data="optDetail.swaps" border stripe height="320" style="width: 100%">
              <el-table-column prop="index" label="#" width="60" align="center" />
              <el-table-column prop="heavy" label="重载教师" width="110" align="center" />
              <el-table-column prop="light" label="轻载教师" width="110" align="center" />
              <el-table-column label="交换(从)" min-width="220">
                <template #default="{ row }">
                  科目{{ row?.from?.subject }}-考场{{ row?.from?.room }}（{{ row?.from?.duration }}分钟）
                </template>
              </el-table-column>
              <el-table-column label="交换(到)" min-width="220">
                <template #default="{ row }">
                  科目{{ row?.to?.subject }}-考场{{ row?.to?.room }}（{{ row?.to?.duration }}分钟）
                </template>
              </el-table-column>
              <el-table-column prop="note" label="备注" min-width="180" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="预设修复明细">
            <el-table :data="optDetail.presetDetails" border stripe height="320" style="width: 100%">
              <el-table-column prop="teacher" label="教师" width="120" align="center" />
              <el-table-column label="移动" min-width="420">
                <template #default="{ row }">
                  科目{{ row?.subject }}：考场{{ row?.from_room }} → 考场{{ row?.to_room }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
      <div v-else class="text-slate-500 text-sm">暂无可显示的优化明细</div>
    </el-dialog>

    <!-- Scheduling Progress Dialog -->
    <el-dialog v-model="isScheduling" title="正在编排" width="400px" :close-on-click-modal="false" :show-close="false" center>
       <div class="py-4 text-center space-y-4">
          <el-progress type="circle" :percentage="schedulingProgress" :status="schedulingStatus" />
          <div class="font-bold text-slate-700">{{ schedulingStepText }}</div>
          <div class="text-xs text-slate-400">请勿关闭窗口，正在进行智能运算...</div>
       </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { Upload, Download, List, CollectionTag, Delete, InfoFilled, CircleCheck, Warning, Fold, Expand, Setting, Check } from '@element-plus/icons-vue'
import { usePageSessionState } from '@/composables/usePageSessionState'
import { useProctoringBootstrap } from '@/views/ProctoringPage/composables/useProctoringBootstrap'
import { useProctoringDataManagement } from '@/views/ProctoringPage/composables/useProctoringDataManagement'
import { useProctoringOptimizationMetrics } from '@/views/ProctoringPage/composables/useProctoringOptimizationMetrics'
import { useProctoringScheduling } from '@/views/ProctoringPage/composables/useProctoringScheduling'
import { useProctoringSwap } from '@/views/ProctoringPage/composables/useProctoringSwap'
import { useProctoringViewData } from '@/views/ProctoringPage/composables/useProctoringViewData'
import dayjs from 'dayjs'

// --- State ---
// Persistence Helper
const storage = usePageSessionState('proctoring')
const getStored = (key: string, def: string) => storage.getPref(key, def)

const sidebarCollapsed = ref(getStored('sidebarCollapsed', 'false') === 'true')
const activeTab = ref(getStored('activeTab', 'overview'))
const showLogs = ref(false)
type UiLogLevel = 'info' | 'success' | 'warning' | 'error'
const logs = ref<{ time: string; level: UiLogLevel; msg: string }[]>([])
const presetVisible = ref(false)
const adjustMode = ref(false)
const selectedCells = ref<{roomId: number, c: string}[]>([])
const optDetailVisible = ref(false)
const optDetail = ref<any>(null)

const hasPreset = ref(false)
const schedulingProgress = ref(0)
const schedulingStatus = ref('') // success, exception, warning
const schedulingStepText = ref('')
const isScheduling = ref(false)

// Persistence Watchers
watch(sidebarCollapsed, (val) => storage.setPref('sidebarCollapsed', String(val)))
watch(activeTab, (val) => storage.setPref('activeTab', val))

// Configuration matches Python structure
const config = reactive({
  roomCount: 0,
  mode: 'single', // single, double
  balanceMode: 'duration', // session, duration
  genderMix: false,
  internalMix: false
})

// Data
const subjects = ref<{id: string, name: string, time: string, durationMinutes: number}[]>([])
const teachers = ref<any[]>([])
const schedule = ref<any[]>([]) // [{subjectId, rooms: [{id, teachers: []}]}]
const selectedSubjectId = ref('')

// --- Computed ---
const {
   subjectCount,
   canSchedule,
   hasSchedule,
   missingSlots,
   canContinue,
   canOptimize,
   getTeacherText,
   getTeacherTextClass,
   getUnavailableNames,
   matrixData,
   teacherStats,
   subjectTableData,
} = useProctoringViewData({
   config,
   subjects,
   teachers,
   schedule,
   selectedSubjectId,
})

const getRoomRecord = (subjectId: string, roomNum: number) => {
   const session = schedule.value.find((s: any) => s.subjectId === subjectId)
   const rooms: any[] = session?.rooms || []
   return rooms.find((r: any) => Number(r.roomNum ?? r.id) === roomNum) || null
}

const getTeacherObj = (subjectId: string, roomNum: number, idx: number) => {
   const room = getRoomRecord(subjectId, roomNum)
   const ts: any[] = room?.teachers || []
   if (config.mode === 'double') return ts[idx] || null
   return ts.find((t) => t) || null
}


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

const { formatVariance, getDiff, getDiffClass } = useProctoringOptimizationMetrics()

const {
   handleTemplate,
   handleAddTeacher,
   handlePresetDialog,
   handleClearTeachers,
   handleClearPreset,
   handleClearSchedule,
   handleResetPage,
   handleGenerateEmptyTemplate,
   handleImportPreset,
   handleImportSchedule,
   handleExport,
} = useProctoringDataManagement({
   config,
   subjects,
   teachers,
   schedule,
   logs,
   showLogs,
   presetVisible,
   hasPreset,
   adjustMode,
   selectedCells,
   selectedSubjectId,
   optDetailVisible,
   optDetail,
   sidebarCollapsed,
   activeTab,
   schedulingProgress,
   schedulingStatus,
   schedulingStepText,
   isScheduling,
   logInfo,
   logSuccess,
   logWarning,
   logError,
   logFromText,
})

const { initializePage } = useProctoringBootstrap({
   config,
   subjects,
   teachers,
   schedule,
   selectedSubjectId,
   hasPreset,
   logError,
})

const { handleSmartSchedule, handleOptimize } = useProctoringScheduling({
   config,
   teachers,
   subjects,
   schedule,
   hasPreset,
   showLogs,
   optDetailVisible,
   optDetail,
   schedulingProgress,
   schedulingStatus,
   schedulingStepText,
   isScheduling,
   logInfo,
   logSuccess,
   logWarning,
   logError,
})

const { toggleAdjustMode, getCellStyle, handleCellClick } = useProctoringSwap({
   config,
   adjustMode,
   selectedCells,
   schedule,
   teachers,
   subjects,
   getTeacherObj,
   logInfo,
   logSuccess,
   logWarning,
   logError,
})

const handleRoomCountChange = () => {
   // Update subjects rooms? Or just config
   // Backend generate uses config.roomCount
}

onMounted(async () => {
   await initializePage()
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

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e2e8f0;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: #cbd5e1;
}

/* Custom Segmented Control */
:deep(.custom-segmented) {
  --el-segmented-item-selected-color: #4f46e5;
  --el-segmented-item-selected-bg-color: #e0e7ff;
  --el-segmented-bg-color: #f1f5f9;
  --el-segmented-color: #64748b;
  padding: 2px;
}

/* Tab Optimization */
:deep(.custom-tabs-header .el-tabs__header) {
  margin: 0;
  border-bottom: none;
}
:deep(.custom-tabs-header .el-tabs__nav-wrap::after) {
  display: none;
}
:deep(.custom-tabs-header .el-tabs__item) {
  font-weight: 500;
  color: #64748b;
  padding: 0 16px;
  height: 48px;
  transition: all 0.2s;
}
:deep(.custom-tabs-header .el-tabs__item.is-active) {
  color: #4f46e5; /* Indigo-600 */
  font-weight: 700;
}
:deep(.custom-tabs-header .el-tabs__active-bar) {
  background-color: #4f46e5;
  height: 3px;
  border-radius: 3px;
}

/* Table Header */
:deep(.el-table th.el-table__cell) {
  background-color: #f8fafc;
  color: #475569;
  font-weight: 600;
}
</style>

<template>
  <div class="h-[calc(100vh-8rem)] flex flex-col animate-fade-in bg-slate-50">
    <div class="h-14 bg-white border-b border-slate-200 px-4 flex items-center shrink-0 shadow-sm z-20">
       <div class="flex-1 flex justify-center">
          <div class="bg-slate-100 p-1 rounded-lg flex gap-1 w-full max-w-[680px]">
             <div 
               v-for="tab in tabs" 
               :key="tab.id"
               class="flex-1 py-1.5 text-center text-xs font-bold cursor-pointer rounded-md transition-all duration-200 select-none"
               :class="activeTab === tab.id ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
               @click="activeTab = tab.id"
             >
                {{ tab.name }}
             </div>
          </div>
       </div>
    </div>

    <div class="flex-1 flex overflow-hidden relative">
       <!-- Left Sidebar: Configuration -->
       <div
         class="flex flex-col border-r border-slate-200/80 bg-white/80 backdrop-blur-xl transition-all duration-300 relative z-20 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)]"
         :class="sidebarCollapsed ? 'w-0 opacity-0 overflow-hidden' : 'w-[280px] opacity-100'"
       >
          <div class="h-14 px-4 border-b border-slate-100/80 flex items-center justify-between shrink-0 bg-gradient-to-b from-white to-slate-50/50">
             <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center text-white shadow-lg shadow-primary-500/20">
                   <el-icon :size="16"><Printer /></el-icon>
                </div>
                <span class="font-bold text-slate-800 text-base tracking-tight">打印配置</span>
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
          <!-- Config Form -->
          <div class="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-8">
             
             <!-- 2. Data Source -->
             <section class="space-y-3">
                <div class="flex items-center justify-between mb-2">
                   <div class="flex items-center gap-2">
                      <div class="w-1 h-3 bg-blue-500 rounded-full"></div>
                      <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">数据来源</span>
                   </div>
                   <div class="px-2 py-0.5 rounded text-[10px] font-bold transition-colors" :class="previewTotal > 0 ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-400'">
                       {{ previewTotal > 0 ? `${previewTotal} 条` : '未加载' }}
                   </div>
                </div>
                
                <div class="grid grid-cols-1 gap-2">
                   <!-- Empty Mode Card -->
                   <div v-if="activeTab !== 'roll_call'"
                      class="relative border rounded-lg p-3 cursor-pointer transition-all duration-200 group bg-white hover:shadow-md hover:shadow-slate-100"
                      :class="sourceType === 'empty' ? 'border-primary-500 bg-primary-50/30 ring-1 ring-primary-500/20' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'"
                      @click="sourceType = 'empty'"
                   >
                      <div class="flex items-center gap-3">
                         <div class="p-2 rounded-lg" :class="sourceType === 'empty' ? 'bg-primary-100 text-primary-600' : 'bg-slate-100 text-slate-400'">
                            <el-icon><Document /></el-icon>
                         </div>
                         <div class="flex-1">
                            <div class="text-sm font-bold" :class="sourceType === 'empty' ? 'text-primary-700' : 'text-slate-700'">空白模板</div>
                            <div class="text-[10px] text-slate-400">仅生成带样式的空白表格</div>
                         </div>
                         <div v-if="sourceType === 'empty'" class="text-primary-500">
                            <el-icon><Select /></el-icon>
                         </div>
                      </div>
                   </div>

                   <!-- File Mode Card -->
                   <div v-if="activeTab !== 'roll_call'"
                      class="relative border rounded-lg p-3 cursor-pointer transition-all duration-200 group bg-white hover:shadow-md hover:shadow-slate-100"
                      :class="sourceType === 'file' ? 'border-primary-500 bg-primary-50/30 ring-1 ring-primary-500/20' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'"
                      @click="sourceType = 'file'"
                   >
                      <div class="flex items-center gap-3">
                         <div class="p-2 rounded-lg" :class="sourceType === 'file' ? 'bg-primary-100 text-primary-600' : 'bg-slate-100 text-slate-400'">
                            <el-icon><Upload /></el-icon>
                         </div>
                         <div class="flex-1">
                            <div class="text-sm font-bold" :class="sourceType === 'file' ? 'text-primary-700' : 'text-slate-700'">导入考生数据</div>
                            <div class="text-[10px] text-slate-400">从 Excel 文件导入考生名单</div>
                         </div>
                         <div v-if="sourceType === 'file'" class="text-primary-500">
                            <el-icon><Select /></el-icon>
                         </div>
                      </div>
                   </div>

                   <!-- Schedule Mode Card -->
                   <div 
                      class="relative border rounded-lg p-3 cursor-pointer transition-all duration-200 group bg-white hover:shadow-md hover:shadow-slate-100"
                      :class="sourceType === 'schedule' ? 'border-primary-500 bg-primary-50/30 ring-1 ring-primary-500/20' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'"
                      @click="sourceType = 'schedule'"
                   >
                      <div class="flex items-center gap-3">
                         <div class="p-2 rounded-lg" :class="sourceType === 'schedule' ? 'bg-primary-100 text-primary-600' : 'bg-slate-100 text-slate-400'">
                            <el-icon><School /></el-icon>
                         </div>
                         <div class="flex-1">
                            <div class="text-sm font-bold" :class="sourceType === 'schedule' ? 'text-primary-700' : 'text-slate-700'">考场编排</div>
                            <div class="text-[10px] text-slate-400">使用系统当前的编排结果</div>
                         </div>
                         <div v-if="sourceType === 'schedule'" class="text-primary-500">
                            <el-icon><Select /></el-icon>
                         </div>
                      </div>
                   </div>
                </div>

                <div class="bg-slate-50/50 rounded-xl border border-slate-100 p-2 h-[72px] flex flex-col justify-center">
                   <div v-if="sourceType === 'empty'" class="flex items-center justify-between">
                      <span class="text-xs text-slate-600 font-medium">生成数量</span>
                      <el-input-number v-model="totalCount" :min="1" :step="10" size="small" class="!w-24" controls-position="right" />
                   </div>

                   <div v-else-if="sourceType === 'file'" class="space-y-1 cursor-default" @click.stop>
                      <div 
                        class="flex items-center gap-2 p-1 rounded-lg border border-dashed border-slate-300 hover:border-primary-400 hover:bg-white transition-colors cursor-pointer"
                        @click="handleSelectFile"
                      >
                         <template v-if="!dataPath">
                            <el-icon class="text-slate-400"><Plus /></el-icon>
                            <span class="text-xs text-slate-500">选择文件...</span>
                         </template>
                         <template v-else>
                            <el-icon class="text-emerald-500"><DocumentChecked /></el-icon>
                            <span class="text-xs font-bold text-slate-700 truncate flex-1">{{ dataFileName }}</span>
                            <el-icon class="text-slate-400 hover:text-rose-500 p-1" @click.stop="clearSelectedFile"><Close /></el-icon>
                         </template>
                      </div>
                      <div class="flex justify-between items-center px-0.5">
                         <span class="text-[10px] text-slate-400">{{ previewTotal > 0 ? `已加载 ${previewTotal} 条` : '未加载数据' }}</span>
                         <el-button 
                           v-if="activeTab !== 'exam_bag_label'"
                           link type="primary" size="small" class="!text-xs !h-auto !p-0" @click="openMappingDialog" :disabled="!dataPath">
                            字段映射
                         </el-button>
                      </div>
                   </div>

                   <div v-else class="flex items-center justify-between cursor-default" @click.stop>
                      <div class="flex items-center gap-1.5 text-emerald-600" v-if="previewTotal > 0">
                         <el-icon size="12"><CircleCheckFilled /></el-icon>
                         <span class="text-xs font-bold">{{ previewTotal }} 条数据</span>
                      </div>
                      <span v-else class="text-xs text-slate-400">暂无数据</span>

                      <el-button size="small" type="primary" link :loading="loadingSchedule" @click="handleLoadFromSchedule">
                         <span class="text-xs">刷新数据</span>
                      </el-button>
                   </div>
                </div>
             </section>

             <!-- 1. Layout Settings (Desk Tab Only) -->
             <section v-if="activeTab === 'desk'" class="space-y-3 animate-fade-in">
                <div class="flex items-center gap-2 mb-2">
                   <div class="w-1 h-3 bg-primary-500 rounded-full"></div>
                   <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">布局设置</span>
                </div>
                <button
                  class="group flex items-center justify-between w-full p-2.5 bg-white border border-slate-200 rounded-lg hover:border-primary-400 hover:shadow-md hover:shadow-primary-500/5 transition-all duration-200 text-left"
                  @click="openDeskLayoutDialog"
                >
                   <div class="flex items-center min-w-0">
                      <div class="w-8 h-8 rounded bg-slate-50 group-hover:bg-primary-50 flex items-center justify-center text-slate-500 group-hover:text-primary-600 transition-colors mr-3 border border-slate-100">
                         <el-icon><Grid /></el-icon>
                      </div>
                      <div class="flex flex-col min-w-0">
                          <span class="text-sm font-medium text-slate-700 group-hover:text-slate-900">座位布局</span>
                         <span class="text-[10px] text-slate-400 truncate">{{ deskLayoutSummary }}</span>
                      </div>
                   </div>
                   <span class="text-xs font-bold text-primary-600 group-hover:text-primary-700 shrink-0">设置...</span>
                </button>
             </section>

             <!-- 3. Specific Settings (Other Tabs) -->
             <section class="space-y-4">
                <div class="flex items-center gap-2 mb-2">
                   <div class="w-1 h-3 bg-indigo-500 rounded-full"></div>
                    <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">参数配置</span>
                </div>

                <!-- Exam Bag Config -->
                <div v-if="activeTab === 'exam_bag_label'" class="space-y-4 animate-fade-in bg-slate-50 rounded-xl p-4 border border-slate-100">
                   <div class="space-y-1">
                      <label class="text-xs text-slate-500">学校名称</label>
                      <el-input v-model="config.examBag.schoolName" size="small" />
                   </div>
                   <div class="space-y-2">
                       <div class="flex items-center justify-between">
                          <label class="text-xs text-slate-500">科目与时间</label>
                          <el-tooltip
                            v-if="isExamBagScheduleSubjectsLocked"
                            :content="examBagSubjectLockMessage"
                            placement="top"
                         >
                            <el-button size="small" type="info" link disabled>编辑科目</el-button>
                         </el-tooltip>
                          <el-button v-else size="small" type="primary" link @click="openSubjectDialog">编辑科目</el-button>
                       </div>
                       <div class="rounded-lg border border-slate-200 bg-white p-2 min-h-[40px] space-y-1">
                         <div v-for="(row, idx) in examBagSubjectPreviewWithTime" :key="idx" class="flex items-center justify-between gap-2 px-1 py-0.5 rounded hover:bg-slate-50">
                            <span class="text-xs text-slate-700 truncate flex-1 font-medium">{{ row.name }}</span>
                            <span class="text-[10px] text-slate-400 font-mono whitespace-nowrap">{{ row.time || '--' }}</span>
                         </div>
                         <div v-if="examBagSubjectPreviewWithTime.length === 0" class="text-xs text-slate-400 w-full text-center py-1">
                            {{ isExamBagScheduleSubjectsLocked ? examBagSubjectLockEmptyText : '未设置科目' }}
                         </div>
                       </div>
                    </div>
                    <div class="text-[10px] text-slate-400 leading-relaxed">
                      {{ examBagConfigHint }}
                    </div>
                 </div>

                <!-- Corner Paper Config -->
                <div v-if="activeTab === 'corner'" class="space-y-4 animate-fade-in bg-slate-50 rounded-xl p-4 border border-slate-100">
                   <div class="space-y-1">
                      <label class="text-xs text-slate-500">大标题</label>
                      <el-input v-model="config.corner.title" placeholder="例如：2025年期末考试" size="small" />
                   </div>
                   <div class="space-y-2">
                      <div class="flex items-center justify-between">
                         <label class="text-xs text-slate-500">科目与时间</label>
                         <el-tooltip
                            v-if="sourceType === 'schedule' && isGaokaoMode"
                            content="高考模式下科目与时间由编排数据决定，无需手动设置"
                            placement="top"
                         >
                            <el-button size="small" type="info" link disabled>编辑科目</el-button>
                         </el-tooltip>
                         <el-button v-else size="small" type="primary" link @click="openSubjectDialog">编辑科目</el-button>
                      </div>
                      <div class="rounded-lg border border-slate-200 bg-white p-2 min-h-[40px] space-y-1">
                         <div v-for="(row, idx) in subjectPreviewWithTime" :key="idx" class="flex items-center justify-between gap-2 px-1 py-0.5 rounded hover:bg-slate-50">
                            <span class="text-xs text-slate-700 truncate flex-1 font-medium">{{ row.name }}</span>
                            <span class="text-[10px] text-slate-400 font-mono whitespace-nowrap">{{ row.time || '--' }}</span>
                         </div>
                         <div v-if="subjectPreviewWithTime.length === 0" class="text-xs text-slate-400 w-full text-center py-1">
                            {{ sourceType === 'schedule' && isGaokaoMode ? '高考模式：科目与时间由编排数据决定' : '未设置科目' }}
                         </div>
                      </div>
                   </div>
                </div>

                <!-- Ticket Config -->
                <div v-if="activeTab === 'ticket'" class="space-y-4 animate-fade-in bg-slate-50 rounded-xl p-4 border border-slate-100">
                   <div class="space-y-1">
                      <label class="text-xs text-slate-500">大标题</label>
                      <el-input v-model="config.ticket.title" size="small" />
                   </div>
                   <div class="space-y-2">
                      <div class="flex items-center justify-between">
                         <label class="text-xs text-slate-500">科目与时间</label>
                         <el-tooltip
                            v-if="sourceType === 'schedule' && isGaokaoMode"
                            content="高考模式下科目与时间由编排数据决定，无需手动设置"
                            placement="top"
                         >
                            <el-button size="small" type="info" link disabled>编辑科目</el-button>
                         </el-tooltip>
                         <el-button v-else size="small" type="primary" link @click="openSubjectDialog">编辑科目</el-button>
                      </div>
                      <div class="rounded-lg border border-slate-200 bg-white p-2 min-h-[40px] space-y-1">
                         <div v-for="(row, idx) in subjectPreviewWithTime" :key="idx" class="flex items-center justify-between gap-2 px-1 py-0.5 rounded hover:bg-slate-50">
                            <span class="text-xs text-slate-700 truncate flex-1 font-medium">{{ row.name }}</span>
                            <span class="text-[10px] text-slate-400 font-mono whitespace-nowrap">{{ row.time || '--' }}</span>
                         </div>
                         <div v-if="subjectPreviewWithTime.length === 0" class="text-xs text-slate-400 w-full text-center py-1">
                            {{ sourceType === 'schedule' && isGaokaoMode ? '高考模式：科目与时间由编排数据决定' : '未设置科目' }}
                         </div>
                      </div>
                   </div>
                </div>
                
                <!-- Student Table Config -->
                <div v-if="activeTab === 'table'" class="space-y-4 animate-fade-in bg-slate-50 rounded-xl p-4 border border-slate-100">
                   <div class="space-y-1">
                      <label class="text-xs text-slate-500">表格标题</label>
                      <el-input v-model="config.table.title" size="small" />
                   </div>
                   <div class="space-y-1">
                      <label class="text-xs text-slate-500">分组方式</label>
                      <div class="flex bg-white rounded border border-slate-200 overflow-hidden">
                         <button 
                            class="flex-1 py-1 text-xs transition-colors"
                            :class="config.table.groupMode === 'class' ? 'bg-primary-50 text-primary-600 font-bold' : 'text-slate-500 hover:bg-slate-50'"
                            @click="config.table.groupMode = 'class'"
                         >按班级</button>
                         <div class="w-px bg-slate-200"></div>
                         <button 
                            class="flex-1 py-1 text-xs transition-colors"
                            :class="config.table.groupMode === 'examroom' ? 'bg-primary-50 text-primary-600 font-bold' : 'text-slate-500 hover:bg-slate-50'"
                            @click="config.table.groupMode = 'examroom'"
                         >按考场</button>
                      </div>
                   </div>
                   <div class="flex items-center justify-between pt-2">
                      <span class="text-xs text-slate-600">包含选科列</span>
                      <el-switch v-model="config.table.includeSubjectFields" size="small" />
                   </div>
                </div>

                <div v-if="activeTab === 'roll_call'" class="space-y-3 animate-fade-in bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <div><label class="text-xs text-slate-500">考试名称</label><el-input v-model="config.rollCall.examName" size="small" /></div>
                  <div><label class="text-xs text-slate-500">学校名称</label><el-input v-model="config.rollCall.schoolName" size="small" /></div>
                  <div class="grid grid-cols-2 gap-2">
                    <div><label class="text-xs text-slate-500">模板样式</label><el-select v-model="config.rollCall.templateMode" size="small" class="w-full"><el-option label="完整考务版" value="full" /><el-option label="精简点名版" value="compact" /></el-select></div>
                    <div><label class="text-xs text-slate-500">纸张方向</label><el-select v-model="config.rollCall.orientation" size="small" class="w-full"><el-option label="自动" value="auto" /><el-option label="纵向" value="portrait" /><el-option label="横向" value="landscape" /></el-select></div>
                  </div>
                  <div class="flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600">
                    <el-checkbox v-model="config.rollCall.mirrorView">镜像为监考视角</el-checkbox>
                    <el-checkbox v-model="config.rollCall.showExamNo">显示考号</el-checkbox>
                    <el-checkbox v-model="config.rollCall.showClass">显示班级</el-checkbox>
                    <el-checkbox v-model="config.rollCall.showCheckbox">显示缺考框</el-checkbox>
                  </div>
                  <div v-if="config.rollCall.templateMode === 'full'"><label class="text-xs text-slate-500">使用说明</label><el-input v-model="config.rollCall.instructions" type="textarea" :rows="3" size="small" /></div>
                  <button class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-left hover:border-primary-300" @click="openDeskLayoutDialog">
                    <div class="text-xs font-bold text-slate-700">公共座位布局</div><div class="text-[10px] text-slate-400">{{ deskLayoutSummary }}，特殊考场布局请在考场编排页设置</div>
                  </button>
                </div>

             </section>

             <!-- 4. Export Options -->
             <section class="space-y-3">
                <div class="flex items-center gap-2 mb-2">
                   <div class="w-1 h-3 bg-emerald-500 rounded-full"></div>
                    <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">输出格式</span>
                </div>
                <div class="flex gap-4 p-3 bg-slate-50/50 rounded-xl border border-slate-100">
                   <el-checkbox v-model="commonConfig.exportXlsx" label="Excel" size="small" />
                    <el-checkbox v-model="commonConfig.exportPdf" label="PDF（推荐）" size="small" />
                </div>
             </section>

          </div>
          
          <div class="shrink-0 border-t border-slate-100/80 p-4 bg-white/80 backdrop-blur-xl">
             <el-button type="primary" class="!w-full !h-12 !text-base !font-bold !rounded-xl shadow-lg shadow-primary-500/20 hover:shadow-primary-500/30 transition-all hover:-translate-y-0.5" :loading="generating" @click="handleGenerate">
                <el-icon class="mr-1.5"><VideoPlay /></el-icon> 开始生成
             </el-button>
          </div>
       </div>

       <div
         v-if="sidebarCollapsed"
         class="absolute left-0 top-6 z-30 bg-white/80 backdrop-blur border border-l-0 border-slate-200/80 p-2 rounded-r-xl shadow-lg cursor-pointer hover:bg-primary-50 hover:text-primary-600 transition-all hover:pl-3"
         @click="sidebarCollapsed = false"
       >
          <el-icon><Expand /></el-icon>
       </div>

      <!-- Right: Preview Area -->
       <div class="flex-1 bg-slate-200/50 relative flex flex-col overflow-hidden">
          <!-- Canvas -->
          <div
            ref="previewViewportRef"
            class="flex-1 overflow-auto p-8 custom-scrollbar relative z-0"
            :class="[
              previewCursorClass,
              autoFit ? 'flex items-center justify-center' : 'flex justify-center'
            ]"
            @wheel="handlePreviewWheel"
            @mousedown="handlePreviewMouseDown"
          >
             <div
               ref="previewPageRef"
               class="bg-white shadow-[0_20px_50px_-12px_rgba(0,0,0,0.25)] origin-center flex-shrink-0 border border-slate-100"
               :class="isPanningPreview ? '' : 'transition-all duration-200 ease-out'"
               :style="{
                  width: previewPageSizeMm.width,
                  height: previewPageSizeMm.height,
                  minHeight: previewPageSizeMm.height,
                  zoom: autoFit ? 1 : previewScale,
                  transform: autoFit
                    ? `translate(${previewOffset.x}px, ${previewOffset.y}px) scale(${previewScale})`
                    : `translate(${previewOffset.x}px, ${previewOffset.y}px)`
               }"
            >
               <div class="relative w-full h-full" :style="{ height: previewPageSizeMm.height, minHeight: previewPageSizeMm.height }">
                   
                   <div v-if="!hasPreviewData" class="absolute inset-0 flex flex-col items-center justify-center text-slate-300">
                      <el-icon :size="64" class="mb-4"><Document /></el-icon>
                      <p>请配置数据源以查看预览</p>
                   </div>

                   <template v-else>
                      <template v-if="previewMode === 'print' && (activeTab === 'corner' || activeTab === 'ticket')">
                         <!-- Grid Layout Simulation (Replacing PDF iframe) -->
                         <div class="absolute inset-0 px-[2.5mm] py-[1.5mm]">
                            <div class="grid grid-cols-3 gap-[3mm]">
                               <template v-if="activeTab === 'corner'">
                                  <div v-for="(item, idx) in printPreviewList" :key="idx" class="corner-card w-full !shadow-none !w-auto">
                                     <table class="corner-table w-full">
                                        <colgroup>
                                           <col style="width: 22.1%" />
                                           <col style="width: 19.8%" />
                                           <col style="width: 29.0%" />
                                           <col style="width: 29.1%" />
                                        </colgroup>
                                        <tbody>
                                           <tr>
                                              <td class="corner-td corner-title-td" colspan="4">{{ config.corner.title || 'xxx考试台角纸' }}</td>
                                           </tr>
                                           <tr>
                                              <td class="corner-td corner-label-td">考场</td>
                                              <td class="corner-td">{{ item['考场'] }}</td>
                                              <td class="corner-td corner-label-td">考场号</td>
                                              <td class="corner-td">{{ item['考场号'] }}</td>
                                           </tr>
                                           <tr>
                                              <td class="corner-td"></td>
                                              <td class="corner-td"></td>
                                              <td class="corner-td corner-label-td">座位号</td>
                                              <td class="corner-td">{{ item['座位号'] }}</td>
                                           </tr>
                                           <tr>
                                              <td class="corner-td corner-label-td">科目</td>
                                              <td class="corner-td corner-label-td">考生姓名</td>
                                              <td class="corner-td corner-label-td">考生考号</td>
                                              <td class="corner-td corner-label-td">考生班级学号</td>
                                           </tr>
                                           <tr v-for="(sub, sidx) in cornerSubjectRows" :key="sidx">
                                              <td class="corner-td">{{ sub }}</td>
                                              <td class="corner-td">{{ getCornerStudentName(item, sidx) }}</td>
                                              <td class="corner-td">{{ getCornerStudentExamNo(item, sidx) }}</td>
                                              <td class="corner-td">{{ getCornerStudentClassNo(item, sidx) }}</td>
                                           </tr>
                                        </tbody>
                                     </table>
                                  </div>
                               </template>
                               
                               <template v-if="activeTab === 'ticket'">
                                  <div v-for="(item, idx) in printPreviewList" :key="idx" class="ticket-card w-full !shadow-none !w-auto">
                                     <table class="ticket-xlsx-table w-full">
                                        <colgroup>
                                           <col style="width: 18.25%" />
                                           <col style="width: 37.60%" />
                                           <col style="width: 16.37%" />
                                           <col style="width: 13.89%" />
                                           <col style="width: 13.89%" />
                                        </colgroup>
                                        <tbody>
                                           <tr>
                                               <td class="ticket-xlsx-td ticket-xlsx-title-td" colspan="5">{{ config.ticket.title || 'xxx考试准考证' }}</td>
                                           </tr>
                                           <tr>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td">考号</td>
                                               <td class="ticket-xlsx-td">{{ item['考生考号'] }}</td>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td" colspan="2">班级</td>
                                               <td class="ticket-xlsx-td">{{ (item as any)['班级'] }}</td>
                                           </tr>
                                           <tr>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td">姓名</td>
                                               <td class="ticket-xlsx-td">{{ item['考生姓名'] }}</td>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td" colspan="2">学号</td>
                                               <td class="ticket-xlsx-td">{{ (item as any)['学号'] }}</td>
                                           </tr>
                                           <tr>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td">科目</td>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td">时间</td>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td">考场</td>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td">考场号</td>
                                               <td class="ticket-xlsx-td ticket-xlsx-label-td">座位号</td>
                                           </tr>
                                     <tr v-for="(row, idx) in ticketSubjectRowsForPrint" :key="idx">
                                              <td class="ticket-xlsx-td">{{ row.name }}</td>
                                              <td class="ticket-xlsx-td">{{ row.time }}</td>
                                              <td class="ticket-xlsx-td">{{ getTicketRoom(item, idx) }}</td>
                                              <td class="ticket-xlsx-td">{{ getTicketRoomNo(item, idx) }}</td>
                                              <td class="ticket-xlsx-td">{{ getTicketSeatNo(item, idx) }}</td>
                                           </tr>
                                        </tbody>
                                     </table>
                                  </div>
                               </template>
                            </div>
                         </div>
                         <div v-if="previewPrintFooterText" class="absolute bottom-[2mm] left-0 w-full text-center text-[10px] text-slate-600 pointer-events-none">
                            {{ previewPrintFooterText }}
                         </div>
                      </template>

                      <!-- Corner Paper Preview (Single Centered) -->
                      <div v-if="activeTab === 'corner' && previewMode === 'style'" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                         <div class="corner-card pointer-events-auto" style="transform: scale(2.5)">
                            <table class="corner-table">
                               <colgroup>
                                  <col style="width: 24.43%" />
                                  <col style="width: 19.83%" />
                                  <col style="width: 29.02%" />
                                  <col style="width: 26.72%" />
                               </colgroup>
                               <tbody>
                                  <tr>
                                     <td class="corner-td corner-title-td" colspan="4">{{ sourceType === 'empty' ? 'xxx考试台角纸' : (config.corner.title || 'xxx考试台角纸') }}</td>
                                  </tr>
                                  <tr>
                                     <td class="corner-td corner-label-td">考场</td>
                                     <td class="corner-td">{{ cornerPreview['考场'] }}</td>
                                     <td class="corner-td corner-label-td">考场号</td>
                                     <td class="corner-td">{{ cornerPreview['考场号'] }}</td>
                                  </tr>
                                  <tr>
                                     <td class="corner-td"></td>
                                     <td class="corner-td"></td>
                                     <td class="corner-td corner-label-td">座位号</td>
                                     <td class="corner-td">{{ cornerPreview['座位号'] }}</td>
                                  </tr>
                                  <tr>
                                     <td class="corner-td corner-label-td">科目</td>
                                     <td class="corner-td corner-label-td">考生姓名</td>
                                     <td class="corner-td corner-label-td">考生考号</td>
                                     <td class="corner-td corner-label-td">考生班级学号</td>
                                  </tr>
                                  <tr v-for="(sub, sidx) in cornerSubjectRowsForStyle" :key="sidx">
                                     <td class="corner-td">{{ sub }}</td>
                                     <td class="corner-td">{{ getCornerStudentName(cornerPreview, sidx) }}</td>
                                     <td class="corner-td">{{ getCornerStudentExamNo(cornerPreview, sidx) }}</td>
                                     <td class="corner-td">{{ getCornerStudentClassNo(cornerPreview, sidx) }}</td>
                                  </tr>
                               </tbody>
                            </table>
                         </div>
                      </div>

                      <!-- Ticket Preview (Single Centered) -->
                      <div v-if="activeTab === 'ticket' && previewMode === 'style'" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                         <div class="ticket-card pointer-events-auto" style="transform: scale(2.5)">
                            <table class="ticket-xlsx-table">
                               <colgroup>
                                  <col style="width: 17.24%" />
                                  <col style="width: 37.42%" />
                                  <col style="width: 17.24%" />
                                  <col style="width: 14.05%" />
                                  <col style="width: 14.05%" />
                               </colgroup>
                               <tbody>
                                  <tr>
                                     <td class="ticket-xlsx-td ticket-xlsx-title-td" colspan="5">{{ config.ticket.title || 'xxx考试准考证' }}</td>
                                  </tr>
                                  <tr>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td">考号</td>
                                     <td class="ticket-xlsx-td">{{ ticketPreview['考生考号'] }}</td>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td" colspan="2">班级</td>
                                     <td class="ticket-xlsx-td">{{ ticketPreview['班级'] }}</td>
                                  </tr>
                                  <tr>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td">姓名</td>
                                     <td class="ticket-xlsx-td">{{ ticketPreview['考生姓名'] }}</td>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td" colspan="2">学号</td>
                                     <td class="ticket-xlsx-td">{{ ticketPreview['学号'] }}</td>
                                  </tr>
                                  <tr>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td">科目</td>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td">时间</td>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td">考场</td>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td">考场号</td>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td">座位号</td>
                                  </tr>
                                  <tr v-for="(row, idx) in ticketSubjectRows" :key="idx">
                                     <td class="ticket-xlsx-td">{{ row.name }}</td>
                                     <td class="ticket-xlsx-td">{{ row.time }}</td>
                                     <td class="ticket-xlsx-td">{{ getTicketRoom(ticketPreview, idx) }}</td>
                                     <td class="ticket-xlsx-td">{{ getTicketRoomNo(ticketPreview, idx) }}</td>
                                     <td class="ticket-xlsx-td">{{ getTicketSeatNo(ticketPreview, idx) }}</td>
                                  </tr>
                               </tbody>
                            </table>
                         </div>
                      </div>
                      <div v-if="activeTab === 'desk' && deskPreviewMode === 'seat'" class="p-8 flex flex-col items-center h-full box-border">
                         <div class="w-full h-full flex flex-col">
                            <div class="w-full flex justify-center mb-4 shrink-0">
                               <div class="w-full h-12 border border-slate-200 bg-slate-50 flex items-center justify-center text-slate-500 text-sm font-bold tracking-wider">
                                   讲台
                               </div>
                            </div>
                            <div 
                              class="grid gap-3 p-2 bg-white flex-1 min-h-0"
                              :style="{ 
                                 gridTemplateColumns: `repeat(${deskEffectiveLayout.cols}, 1fr)`,
                                 gridTemplateRows: `repeat(${deskEffectiveLayout.rows}, 1fr)`,
                                 width: '100%'
                              }"
                            >
                               <template v-for="(row, rIndex) in deskSeatNumberGrid" :key="rIndex">
                                  <div 
                                    v-for="(cell, cIndex) in row" 
                                    :key="`${rIndex}-${cIndex}`"
                                    class="border border-slate-200 bg-white flex items-center justify-center text-slate-500 text-sm w-full h-full"
                                    :class="cell.valid ? 'opacity-100' : 'opacity-0'"
                                  >
                                     {{ cell.seatNo || '' }}
                                  </div>
                               </template>
                            </div>
                         </div>
                      </div>

                      <div v-if="activeTab === 'desk' && deskPreviewMode === 'print'" class="absolute inset-0 p-[5mm]">
                         <div class="w-full h-full p-[3.2mm]">
                            <table class="desk-label-table">
                               <tbody>
                                  <tr v-for="r in deskEffectiveLayout.rows" :key="r" :style="{ height: `${100 / deskEffectiveLayout.rows}%` }">
                                     <td v-for="c in deskEffectiveLayout.cols" :key="`${r}-${c}`" class="desk-label-td">
                                       {{ deskPrintCellText(r - 1, c - 1) }}
                                     </td>
                                  </tr>
                               </tbody>
                            </table>
                         </div>
                      </div>

                      <div v-if="activeTab === 'roll_call'" class="absolute inset-0 p-[8mm] flex flex-col text-slate-900 bg-white">
                        <div class="text-center font-bold" style="font-size: 18px;">{{ config.rollCall.examName }}</div>
                        <div class="mt-2 text-center" style="font-size: 10px;">学校：{{ config.rollCall.schoolName }}　科目：{{ rollCallPreview?.subject || '--' }}　考场：{{ rollCallPreview?.roomName || '--' }}　考场号：{{ rollCallPreview?.roomNo || '--' }}　人数：{{ rollCallPreview?.students?.length || 0 }}</div>
                        <div v-if="config.rollCall.templateMode === 'full'" class="mt-2 text-right" style="font-size: 10px;">主监考（签名）：________　副监考（签名）：________</div>
                        <div class="flex-1 min-h-0">
                          <div class="w-full h-full" :style="{ display: 'grid', gridTemplateColumns: `repeat(${rollCallLayout.layoutCols}, 1fr)`, gridTemplateRows: `repeat(${rollCallLayout.layoutRows}, 1fr)` }">
                            <div v-for="cell in rollCallPreviewCells" :key="cell.key" class="roll-call-cell" :class="cell.valid ? 'border-slate-600' : 'border-transparent'">
                              <template v-if="cell.valid">
                                <span class="roll-call-seat">{{ cell.seat }}. {{ cell.student?.name || '' }}</span>
                                <span v-if="config.rollCall.showExamNo" class="roll-call-exam-no">{{ cell.student?.examNo || '' }}</span>
                                <span v-if="config.rollCall.showClass && cell.student?.className" class="roll-call-class">{{ cell.student.className }}</span>
                                <span v-if="config.rollCall.showCheckbox" class="roll-call-checkbox">□ 缺考</span>
                              </template>
                            </div>
                          </div>
                        </div>
                        <div v-if="config.rollCall.templateMode === 'full'" class="grid grid-cols-3 gap-2" style="height: calc(20% - 8mm); margin-top: 4mm;">
                          <div class="col-span-2 border p-2 flex flex-col" style="font-size: 10px;">
                            <span class="font-bold">{{ config.rollCall.notesTitle }}</span>
                          </div>
                          <div class="whitespace-pre-line" style="font-size: 9px; line-height: 1.5;">{{ config.rollCall.instructions }}</div>
                        </div>
                      </div>

                      <!-- Table Preview -->
                      <div v-if="activeTab === 'table'" class="absolute inset-0 px-[10mm] py-[10mm] flex flex-col">
                         <table class="w-full border-collapse" :style="{ fontSize: studentInfoPrintLayout.fontSizePx }">
                            <colgroup>
                               <col v-for="col in studentInfoColumns" :key="col.key" :style="{ width: col.width }" />
                            </colgroup>
                            <tbody>
                               <tr :style="{ height: studentInfoPrintLayout.titleH }">
                                  <td
                                     :colspan="studentInfoColumns.length"
                                     class="border-[0.5px] border-black text-center font-bold px-[3px] py-[2px]"
                                     :style="{ fontSize: studentInfoPrintLayout.titleFontSizePx }"
                                  >
                                     {{ config.table.title }}
                                  </td>
                               </tr>
                               <tr class="bg-[#F2F2F2]" :style="{ height: studentInfoPrintLayout.headerH }">
                                  <th
                                     v-for="col in studentInfoColumns"
                                     :key="col.key"
                                     class="border-[0.5px] border-black border-b-[1px] font-bold text-center px-[3px] py-[2px]"
                                  >
                                     {{ col.label }}
                                  </th>
                               </tr>
                               <tr v-for="(row, idx) in studentInfoPrintBodyRows" :key="idx" :style="{ height: studentInfoPrintLayout.bodyH }">
                                  <td v-for="col in studentInfoColumns" :key="col.key" class="border-[0.5px] border-black text-center px-[3px] py-[2px]">
                                     {{ (row as any)[col.key] }}
                                  </td>
                               </tr>
                               <tr v-if="studentInfoFirstPageMeta.showSummary" :style="{ height: studentInfoPrintLayout.summaryH }">
                                  <td v-for="col in studentInfoColumns" :key="col.key" class="border-[0.5px] border-black text-center px-[3px] py-[2px]">
                                     {{ (studentInfoPrintSummaryRow as any)[col.key] }}
                                  </td>
                               </tr>
                            </tbody>
                         </table>
                      </div>

                      <!-- Exam Bag Label Preview -->
                      <div v-if="activeTab === 'exam_bag_label'" class="absolute inset-0 px-[5.08mm] py-[2.54mm]">
                         <div class="grid grid-cols-3 grid-rows-3 w-full h-[264.58mm] gap-0">
                            <div
                               v-for="(text, idx) in examBagPrintCells"
                               :key="idx"
                               class="border-[0.5pt] border-black flex items-center"
                               style="font-family: SimSun, SimHei, 'Microsoft YaHei', serif;"
                            >
                               <div class="w-full px-[10pt] py-[8pt] text-[14pt] font-bold leading-[16pt] whitespace-pre-wrap">
                                  {{ text }}
                               </div>
                            </div>
                         </div>
                         <div v-if="examBagPreviewFooterText" class="absolute bottom-[2mm] left-0 w-full text-center text-[10px] text-slate-600 pointer-events-none">
                            {{ examBagPreviewFooterText }}
                         </div>
                      </div>
                   </template>

                </div>
             </div>
          </div>
          <div ref="previewOverlayRef" class="absolute bottom-6 left-0 w-full flex flex-col items-center justify-center gap-2 pointer-events-none z-20">
             <div v-if="previewBadgeText" class="bg-white/80 backdrop-blur-md shadow-md border border-white/50 rounded-xl px-3 py-1 text-xs font-bold text-slate-600">
                {{ previewBadgeText }}
             </div>
             <div class="bg-white/80 backdrop-blur-md shadow-lg border border-white/50 rounded-2xl p-2 flex items-center gap-3 pointer-events-auto transition-all hover:bg-white hover:shadow-xl">
                 <div v-if="activeTab === 'corner' || activeTab === 'ticket'" class="flex bg-slate-100 rounded-lg p-1">
                    <button
                      class="px-3 py-1.5 text-xs font-bold rounded-md transition-all"
                      :class="previewMode === 'style' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                      @click="previewMode = 'style'"
                    >样式预览</button>
                    <button
                      class="px-3 py-1.5 text-xs font-bold rounded-md transition-all"
                      :class="previewMode === 'print' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                      @click="previewMode = 'print'"
                    >打印预览</button>
                 </div>
                 
                 <div v-if="activeTab === 'desk'" class="flex bg-slate-100 rounded-lg p-1">
                    <button
                      class="px-3 py-1.5 text-xs font-bold rounded-md transition-all"
                      :class="deskPreviewMode === 'seat' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                      @click="deskPreviewMode = 'seat'"
                    >座位布局</button>
                    <button
                      class="px-3 py-1.5 text-xs font-bold rounded-md transition-all"
                      :class="deskPreviewMode === 'print' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                      @click="deskPreviewMode = 'print'"
                    >桌角纸打印</button>
                 </div>

                 <div v-if="activeTab === 'corner' || activeTab === 'ticket'" class="w-px h-4 bg-slate-200"></div>
                 <div v-if="activeTab === 'desk'" class="w-px h-4 bg-slate-200"></div>

                 <div class="flex items-center gap-1">
                    <el-tooltip content="缩小" placement="top">
                       <button class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors" @click="handleZoomOut">
                          <el-icon><Minus /></el-icon>
                       </button>
                    </el-tooltip>
                    <span class="text-xs font-mono w-10 text-center select-none text-slate-700">{{ Math.round(previewScale * 100) }}%</span>
                    <el-tooltip content="放大" placement="top">
                       <button class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors" @click="handleZoomIn">
                          <el-icon><Plus /></el-icon>
                       </button>
                    </el-tooltip>
                 </div>

                 <div class="w-px h-4 bg-slate-200"></div>

                 <el-tooltip content="自适应窗口" placement="top">
                   <button 
                      class="p-1.5 rounded-lg transition-colors" 
                      :class="autoFit ? 'text-primary-600 bg-primary-50' : 'text-slate-500 hover:bg-slate-100'"
                      @click="handleAutoFit"
                   >
                      <el-icon><FullScreen /></el-icon>
                   </button>
                 </el-tooltip>
             </div>
          </div>
       </div>
    </div>

    <PrintingMappingDialog
      v-model="showMappingDialog"
      :required-fields="requiredFields"
      :headers="headers"
      :mapping="mapping"
      @confirm="handleConfirmMapping"
    />

    <PrintingSubjectsDialog
      v-model="showSubjectDialog"
      v-model:subject-draft-count="subjectDraftCount"
      :syncing-subjects="syncingSubjects"
      :subject-draft-rows="subjectDraftRows"
      :get-row-date="getRowDate"
      :set-row-date="setRowDate"
      :get-row-time-range="getRowTimeRange"
      :set-row-time-range="setRowTimeRange"
      @sync-subjects="handleSyncSubjects"
      @remove-subject="handleRemoveSubjectDraft"
      @save-subjects="handleSaveSubjects"
    />

    <PrintingDeskLayoutDialog
      v-model="showDeskLayoutDialog"
      :desk-layout-options="deskLayoutOptions"
      :desk-layout-draft="deskLayoutDraft"
      @apply="applyDeskLayoutDraft"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onActivated, nextTick } from 'vue'
import { 
  Printer, VideoPlay, DocumentChecked, Close, 
  Document, Minus, Plus, FullScreen, Grid, DataLine, Select, 
  Calendar, CircleCheckFilled, Download, Upload, Setting, Fold, Expand, Delete, School,
  Refresh, Back, Right
} from '@element-plus/icons-vue'
import { usePageSessionState } from '@/composables/usePageSessionState'
import { applyPageReset, useAppCacheControl } from '@/composables/useAppCacheControl'
import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionSuccess } from '@/lib/uiFeedback'
import { usePrintingFileSource } from './PrintingPage/composables/usePrintingFileSource'
import { usePrintingDeskLayout } from './PrintingPage/composables/usePrintingDeskLayout'
import { usePrintingGenerate } from './PrintingPage/composables/usePrintingGenerate'
import { usePrintingPreview } from './PrintingPage/composables/usePrintingPreview'
import { usePrintingPreviewData } from './PrintingPage/composables/usePrintingPreviewData'
import { usePrintingScheduleSource } from './PrintingPage/composables/usePrintingScheduleSource'
import { usePrintingSubjects } from './PrintingPage/composables/usePrintingSubjects'
import PrintingMappingDialog from './PrintingPage/components/PrintingMappingDialog.vue'
import PrintingSubjectsDialog from './PrintingPage/components/PrintingSubjectsDialog.vue'
import PrintingDeskLayoutDialog from './PrintingPage/components/PrintingDeskLayoutDialog.vue'
import { getSeatMapping, mirrorSeatLayout, normalizeSeatLayout } from '@/types/seatLayout'

// --- State ---
const storage = usePageSessionState('printing')
const { printingSubjectDependencyEpoch, printingScheduleDependencyEpoch } = useAppCacheControl()
const feedback = createUiFeedback()
const getStored = (key: string, def: string) => storage.getPref(key, def)

const sidebarCollapsed = ref(getStored('sidebarCollapsed', 'false') === 'true')
const activeTab = ref(getStored('activeTab', 'corner'))

// Data Source
const sourceType = ref('empty') // 'empty' | 'file' | 'schedule'
const totalCount = ref(800)
const loadingSchedule = ref(false)
const scheduleArrangementMode = ref('') // 考场编排模式: 'gaokao_mode' | 'normal_mode' | 'subject_mode' | 'random_mode'
const EXAM_BAG_FIXED_SUBJECT_ORDER = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '政治', '地理'] as const

const dataPath = ref('')
const isGaokaoMode = computed(() => scheduleArrangementMode.value === 'gaokao_mode')
const isExamBagScheduleSubjectsLocked = computed(() =>
   sourceType.value === 'schedule'
   && activeTab.value === 'exam_bag_label'
   && ['subject_mode', 'gaokao_mode'].includes(scheduleArrangementMode.value)
)
const examBagSubjectLockMessage = computed(() => {
   if (scheduleArrangementMode.value === 'subject_mode') {
      return '3+1+2选科编排下试卷袋科目按固定规则生成，不允许手动编辑'
   }
   if (scheduleArrangementMode.value === 'gaokao_mode') {
      return '高考模式下试卷袋科目按固定规则生成，不允许手动编辑'
   }
   return ''
})
const examBagSubjectLockEmptyText = computed(() => {
   if (scheduleArrangementMode.value === 'subject_mode') {
      return '3+1+2选科编排：试卷袋科目按固定规则生成'
   }
   if (scheduleArrangementMode.value === 'gaokao_mode') {
      return '高考模式：试卷袋科目按固定规则生成'
   }
   return '未设置科目'
})
const examBagSubjectPreviewWithTime = computed(() => {
   if (!isExamBagScheduleSubjectsLocked.value) {
      return subjectPreviewWithTime.value
   }

   const timeMap = new Map(
      subjectRows.value
         .map((row) => [String(row.name ?? '').trim(), String(row.time ?? '').trim()] as const)
         .filter(([name]) => Boolean(name))
   )
   const mergedGaokaoTime = timeMap.get('物理历史') || ''

   return EXAM_BAG_FIXED_SUBJECT_ORDER.map((subject) => ({
      name: subject,
      time: timeMap.get(subject) || ((subject === '物理' || subject === '历史') ? mergedGaokaoTime : '')
   }))
})
const examBagConfigHint = computed(() => {
   if (sourceType.value === 'empty') {
      return '说明：当前为空白试卷袋样式预览。切换到“导入数据”或“考场编排”后，可根据实际数据生成试卷袋。'
   }
   if (sourceType.value === 'file') {
      return '说明：导入 Excel 数据时，第一列为“考场”，后续列为“科目”（单元格值为人数）。系统会按学科分组生成试卷袋。'
   }
   if (scheduleArrangementMode.value === 'subject_mode') {
      return '说明：3+1+2选科编排下，试卷袋会严格按“语文、数学、英语、物理、化学、生物、历史、政治、地理”的固定顺序生成，并按科目在各考场的实际考试人数统计。'
   }
   if (isGaokaoMode.value) {
      return '说明：高考模式下，试卷袋会严格按“语文、数学、英语、物理、化学、生物、历史、政治、地理”的固定顺序生成，并按科目在各考场的实际考试人数统计。'
   }
   return '说明：使用考场编排作为数据源时，将按当前考场编排结果生成试卷袋，科目与时间默认读取“科目设置”，也可在此处手动调整。'
})
const headers = ref<string[]>([])
const showMappingDialog = ref(false)
const previewData = ref<any[]>([])
const previewTotal = ref(0)

const {
   previewViewportRef,
   previewPageRef,
   previewOverlayRef,
   previewScale,
   autoFit,
   previewOffset,
   isPanningPreview,
   previewMode,
   deskPreviewMode,
   previewCursorClass,
   previewPageSizeMm,
   previewTargetPx,
   resetPreviewTransform,
   handleZoomIn,
   handleZoomOut,
   handleAutoFit,
   handlePreviewWheel,
   handlePreviewMouseDown,
   measurePreviewBaseSize: _measurePreviewBaseSize,
   updatePreviewScale: _updatePreviewScale,
   initPreviewAutoScale: _initPreviewAutoScale,
} = usePrintingPreview({
   activeTab,
   rollCallOrientation: computed(() => String(config.rollCall.orientation || 'auto')),
})

// Persistence Watchers
watch(sidebarCollapsed, (val) => storage.setPref('sidebarCollapsed', String(val)))
watch(activeTab, (val) => storage.setPref('activeTab', val))

let _saveConfigTimer: ReturnType<typeof setTimeout> | null = null
function _scheduleSaveConfig() {
   if (_saveConfigTimer) clearTimeout(_saveConfigTimer)
   _saveConfigTimer = setTimeout(async () => {
      try {
         await pythonBackend.request('printing.saveConfig', {
            config: JSON.parse(JSON.stringify(config)),
            commonConfig: JSON.parse(JSON.stringify(commonConfig)),
            totalCount: totalCount.value,
            sourceType: sourceType.value,
            subjectRows: JSON.parse(JSON.stringify(subjectRows.value)),
            studentInfoTitles: JSON.parse(JSON.stringify(studentInfoTitles)),
         })
      } catch {}
   }, 600)
}

watch(activeTab, async (val) => {
   if (val === 'roll_call' && sourceType.value !== 'schedule') sourceType.value = 'schedule'
   if (val !== 'corner' && val !== 'ticket') previewMode.value = 'style'
   if (val === 'exam_bag_label') showMappingDialog.value = false
   resetPreviewTransform()
   if (sourceType.value === 'file' && dataPath.value) {
      const canLoad = val === 'exam_bag_label' || isMappingComplete()
      if (canLoad) {
         await loadPreview()
      }
   }
   // 如果数据来源是考场编排，切换标签时自动刷新数据
   if (sourceType.value === 'schedule') {
      await nextTick()
      await handleLoadFromSchedule()
   }
   await nextTick()
   _measurePreviewBaseSize()
   _updatePreviewScale()
}, { immediate: true })

const tabs = [
  { id: 'corner', name: '台角纸' },
  { id: 'desk', name: '桌角标签' },
  { id: 'ticket', name: '准考证' },
  { id: 'table', name: '考生信息表' },
  { id: 'exam_bag_label', name: '试卷袋' },
  { id: 'roll_call', name: '点名表' }
]

const commonConfig = reactive({
   exportXlsx: false,
   exportPdf: true
})

const config = reactive({
   corner: {
      title: 'xxx考试台角纸'
   },
   desk: {
      layoutName: '7行×6列',
      layoutRows: 7,
      layoutCols: 6,
      layoutPattern: 'S型竖排',
      startPos: 'left',
      customColCounts: null as number[] | null,
   },
   ticket: {
      title: 'xxx考试准考证'
   },
   table: {
      title: 'xxx考试座位安排',
      includeSubjectFields: false,
      groupMode: 'class'
   },
   examBag: {
      schoolName: 'xxx学校'
   },
   rollCall: {
      examName: 'xxx考试点名表',
      schoolName: 'xxx学校',
      templateMode: 'full',
      orientation: 'auto',
      mirrorView: false,
      showExamNo: true,
      showClass: false,
      showCheckbox: true,
      notesTitle: '备注栏：',
      instructions: '1.学生缺考时，请在对应方框内打勾。\n2.学生出现异常行为，请在备注栏记录相关情况。\n3.请将本表张贴于答卷袋正面。'
   }
})

const rollCallPreview = computed(() => previewData.value[0] || null)
const rollCallLayout = computed(() => mirrorSeatLayout(rollCallPreview.value?.seatLayout || config.desk, Boolean(config.rollCall.mirrorView)))
const rollCallPreviewCells = computed(() => {
   const layout = rollCallLayout.value
   const mapping = getSeatMapping(layout)
   const positionToSeat = new Map(Object.entries(mapping).map(([seat, pos]) => [`${pos[0]}-${pos[1]}`, Number(seat)]))
   const students = new Map<number, any>((rollCallPreview.value?.students || []).map((student: any) => [Number(student.seatNo), student]))
   return Array.from({ length: layout.layoutRows * layout.layoutCols }, (_, index) => {
      const row = Math.floor(index / layout.layoutCols)
      const col = index % layout.layoutCols
      const seat = positionToSeat.get(`${row}-${col}`)
      return { key: `${row}-${col}`, valid: Boolean(seat), seat, student: seat ? students.get(seat) : null }
   })
})

const {
   dataFileName,
   mapping,
   requiredFields,
   filePreviewCache,
   clearSelectedFile,
   resetFileState,
   cacheCurrentFileState: _cacheCurrentFileState,
   applyCachedFileState,
   restoreFileStateFromPrintingState,
   openMappingDialog,
   handleConfirmMapping,
   isMappingComplete,
   loadPreview,
   handleSelectFile,
} = usePrintingFileSource({
   storage,
   activeTab,
   sourceType,
   dataPath,
   headers,
   previewData,
   previewTotal,
   showMappingDialog,
   getSaveConfigPayload: () => ({
      config: JSON.parse(JSON.stringify(config)),
      commonConfig: JSON.parse(JSON.stringify(commonConfig)),
      totalCount: totalCount.value,
      sourceType: sourceType.value,
   }),
})

const {
   subjectRows,
   subjectDraftRows,
   subjectDraftCount,
   subjectRowsCustomized,
   showSubjectDialog,
   syncingSubjects,
   subjectPreviewWithTime,
   initializeSubjectRows,
   restoreSubjectRows,
   resetSubjectRows,
   syncSubjectRowsForCurrentSource,
   openSubjectDialog,
   handleSyncSubjects,
   handleRemoveSubjectDraft,
   handleSaveSubjects,
   getRowDate,
   setRowDate,
   getRowTimeRange,
   setRowTimeRange,
} = usePrintingSubjects({
   storage,
   sourceType,
   isGaokaoMode,
})

watch(config, _scheduleSaveConfig, { deep: true })
watch(commonConfig, _scheduleSaveConfig, { deep: true })
watch(totalCount, _scheduleSaveConfig)
watch(sourceType, _scheduleSaveConfig)
watch(subjectRows, _scheduleSaveConfig, { deep: true })

watch(printingSubjectDependencyEpoch, async () => {
   if (sourceType.value !== 'schedule') return
   try {
      if (!subjectRowsCustomized.value) {
         await syncSubjectRowsForCurrentSource()
      }
      await refreshSchedulePreviewSilently()
   } catch (error) {
      console.error('Failed to refresh printing after subject dependency reset:', error)
   }
})

watch(printingScheduleDependencyEpoch, async () => {
   if (sourceType.value !== 'schedule') return
   try {
      await refreshSchedulePreviewSilently()
   } catch (error) {
      console.error('Failed to refresh printing after schedule dependency reset:', error)
   }
})

const storedStudentInfoTitles = storage.getJsonPref<{ class?: string; examroom?: string }>('studentInfoTitles_v1', {})
const studentInfoTitles = reactive<{ class: string; examroom: string }>({
   class: String(storedStudentInfoTitles.class ?? ''),
   examroom: String(storedStudentInfoTitles.examroom ?? ''),
})
if (!studentInfoTitles.class) studentInfoTitles.class = config.table.title
if (!studentInfoTitles.examroom) studentInfoTitles.examroom = config.table.title

watch(() => config.table.groupMode, (mode) => {
   const m = mode === 'examroom' ? 'examroom' : 'class'
   const nextTitle = studentInfoTitles[m]
   if (typeof nextTitle === 'string' && nextTitle.trim().length) {
      config.table.title = nextTitle
   }
})

watch(() => config.table.title, (val) => {
   const m = config.table.groupMode === 'examroom' ? 'examroom' : 'class'
   studentInfoTitles[m] = String(val ?? '')
   storage.setJsonPref('studentInfoTitles_v1', { ...studentInfoTitles })
})
watch(studentInfoTitles, _scheduleSaveConfig, { deep: true })
onMounted(async () => {
   initializeSubjectRows()

   // Restore printing state
   try {
      const state = await pythonBackend.request<any>('printing.getState', {})
      if (!restoreFileStateFromPrintingState(state) && state && state.sourceType === 'schedule') {
         sourceType.value = 'schedule'
      }

      // Restore config
      if (state && state.config && typeof state.config === 'object') {
         const c = state.config
         if (c.corner?.title != null) config.corner.title = c.corner.title
         if (c.desk) {
            if (c.desk.layoutName != null) config.desk.layoutName = c.desk.layoutName
            if (c.desk.layoutRows != null) config.desk.layoutRows = c.desk.layoutRows
            if (c.desk.layoutCols != null) config.desk.layoutCols = c.desk.layoutCols
            if (c.desk.layoutPattern != null) config.desk.layoutPattern = c.desk.layoutPattern
            if (c.desk.startPos != null) config.desk.startPos = c.desk.startPos
            if (c.desk.customColCounts !== undefined) config.desk.customColCounts = c.desk.customColCounts
         }
         if (c.ticket?.title != null) config.ticket.title = c.ticket.title
         if (c.table) {
            if (c.table.title != null) config.table.title = c.table.title
            if (c.table.includeSubjectFields != null) config.table.includeSubjectFields = c.table.includeSubjectFields
            if (c.table.groupMode != null) config.table.groupMode = c.table.groupMode
         }
         if (c.examBag?.schoolName != null) config.examBag.schoolName = c.examBag.schoolName
         if (c.rollCall) Object.assign(config.rollCall, c.rollCall)
      }
      if (state && state.commonConfig && typeof state.commonConfig === 'object') {
         const cc = state.commonConfig
         if (cc.exportXlsx != null) commonConfig.exportXlsx = cc.exportXlsx
         if (cc.exportPdf != null) commonConfig.exportPdf = cc.exportPdf
      }
      if (state && state.totalCount != null) {
         totalCount.value = state.totalCount
      }
      if (Array.isArray(state?.subjectRows) && state.subjectRows.length > 0) {
         restoreSubjectRows(state.subjectRows, true)
      }
      if (state && state.studentInfoTitles && typeof state.studentInfoTitles === 'object') {
         const nextTitles = state.studentInfoTitles as Record<string, string>
         if (nextTitles.class != null) studentInfoTitles.class = String(nextTitles.class)
         if (nextTitles.examroom != null) studentInfoTitles.examroom = String(nextTitles.examroom)
         storage.setJsonPref('studentInfoTitles_v1', { ...studentInfoTitles })
      }

      try {
         const layoutState = await pythonBackend.request<any>('rooms.getSeatLayout', {})
         const shared = layoutState?.seatLayout?.defaultLayout
         if (shared) Object.assign(config.desk, normalizeSeatLayout(shared))
      } catch (error) {
         console.error('Failed to load shared seat layout:', error)
      }

      // Re-sync studentInfoTitles from restored config.table.title if sessionStorage had no saved value
      if (!storage.hasPref('studentInfoTitles_v1')) {
         studentInfoTitles.class = config.table.title
         studentInfoTitles.examroom = config.table.title
      }
   } catch (e) {
      console.error('Failed to restore printing state:', e)
   }

   previewScale.value = 1
   await nextTick()
   _measurePreviewBaseSize()
   _initPreviewAutoScale()

   // Force re-measure and auto-fit after a small delay to ensure layout is stable
   // This fixes the issue where initial auto-fit might fail if layout isn't fully ready
   setTimeout(() => {
      _measurePreviewBaseSize()
      handleAutoFit()
   }, 200)
})

onActivated(async () => {
   await nextTick()
   _measurePreviewBaseSize()
   _updatePreviewScale()

   if (sourceType.value === 'schedule') {
      await handleLoadFromSchedule({ silent: true })
   }
})

const handleResetPage = async () => {
   try {
      await feedback.confirmWarning({
         message: '确定要初始化当前页面吗？这将清除所有数据与设置。',
         title: '初始化页面',
         confirmButtonText: '初始化',
         cancelButtonText: '取消',
      })
   } catch {
      return
   }

   sidebarCollapsed.value = false
   activeTab.value = 'corner'

   sourceType.value = 'empty'
   totalCount.value = 800
   loadingSchedule.value = false

   // Reset backend state
   if (_saveConfigTimer) { clearTimeout(_saveConfigTimer); _saveConfigTimer = null }
   try {
      await pythonBackend.request('printing.resetState', {})
   } catch (e) {
      console.error('Failed to reset backend printing state:', e)
   }

   resetFileState()

   commonConfig.exportXlsx = false
   commonConfig.exportPdf = true

   config.corner.title = 'xxx考试台角纸'
   config.desk.layoutRows = 7
   config.desk.layoutCols = 6
   config.desk.layoutName = '7行×6列'
   config.desk.layoutPattern = 'S型竖排'
   config.desk.startPos = 'left'
   config.desk.customColCounts = null
   config.ticket.title = 'xxx考试准考证'
   config.table.title = 'xxx考试座位安排'
   config.table.includeSubjectFields = false
   config.table.groupMode = 'class'
   config.examBag.schoolName = 'xxx学校'

   studentInfoTitles.class = config.table.title
   studentInfoTitles.examroom = config.table.title

   resetSubjectRows()

   autoFit.value = true
   previewMode.value = 'style'
   await nextTick()
   _measurePreviewBaseSize()
   _updatePreviewScale()

   applyPageReset('printing')
   feedback.success(formatActionSuccess('初始化打印页面'))
}

// --- Computed ---
const {
   hasPreviewData,
   displayData,
   tablePreviewRows,
   studentInfoColumns,
   studentInfoPrintLayout,
   studentInfoFirstGroupRows,
   studentInfoFirstPageMeta,
   studentInfoPrintBodyRows,
   studentInfoPrintSummaryRow,
   examBagGroupedPages,
   examBagPreviewList,
   examBagPrintCells,
   examBagPreviewFooterText,
   getCornerStudentName,
   getCornerStudentExamNo,
   getCornerStudentClassNo,
   getTicketRoom,
   getTicketRoomNo,
   getTicketSeatNo,
   cornerPreview,
   cornerSubjectRowsForStyle,
   cornerSubjectRows,
   cornerTemplatesPerCol,
   itemsPerPage,
   previewTotalPages,
   printPreviewList,
   ticketPreview,
   ticketSubjectRows,
   ticketSubjectRowsForPrint,
   previewBadgeText,
   previewPrintFooterText,
} = usePrintingPreviewData({
   activeTab,
   sourceType,
   previewMode,
   previewData,
   previewTotal,
   config,
   subjectRows,
})
const {
   deskLayoutOptions,
   deskEffectiveLayout,
   deskSeatGrid,
   deskSeatNumberGrid,
   deskPrintCellText,
   deskLayoutSummary,
   showDeskLayoutDialog,
   deskLayoutDraft,
   openDeskLayoutDialog,
   applyDeskLayoutDraft,
} = usePrintingDeskLayout({
   config,
   displayData,
   hasPreviewData,
   sourceType,
   onAfterApply: async () => {
      try {
         const current = await pythonBackend.request<any>('rooms.getSeatLayout', {})
         await pythonBackend.request('rooms.setSeatLayout', {
            seatLayout: {
               defaultLayout: normalizeSeatLayout({ ...config.desk, startPos: config.desk.startPos === 'right' ? 'right' : 'left' }),
               roomOverrides: current?.seatLayout?.roomOverrides || {},
            }
         })
      } catch (error) {
         console.error('Failed to save shared seat layout:', error)
      }
      await nextTick()
      _measurePreviewBaseSize()
      handleAutoFit()
   },
})
const {
   generating,
   handleGenerate,
} = usePrintingGenerate({
   activeTab,
   sourceType,
   dataPath,
   previewData,
   showMappingDialog,
   mapping,
   isMappingComplete,
   commonConfig,
   config,
   totalCount,
   isGaokaoMode,
   subjectRows,
   deskEffectiveLayout,
   tabs,
})

// --- Methods ---

const {
   refreshSchedulePreviewSilently,
   handleLoadFromSchedule,
} = usePrintingScheduleSource({
   activeTab,
   loadingSchedule,
   scheduleArrangementMode,
   previewData,
   previewTotal,
   syncSubjectRowsForCurrentSource,
   shouldSyncSubjectRows: () => !subjectRowsCustomized.value,
   getScheduleParams: () => activeTab.value === 'exam_bag_label'
      ? { subjects: subjectRows.value.map((row) => String(row.name ?? '').trim()).filter(Boolean) }
      : {},
})
// Auto load schedule if mode selected
watch(sourceType, (val, oldVal) => {
   if (oldVal === 'file') _cacheCurrentFileState()

   if (val === 'schedule') {
      previewData.value = []
      previewTotal.value = 0
      handleLoadFromSchedule()
      return
   }

   if (val === 'file') {
      applyCachedFileState()
      return
   }

   previewData.value = []
   previewTotal.value = 0
})

watch(subjectRows, async () => {
   if (sourceType.value === 'schedule' && activeTab.value === 'exam_bag_label' && subjectRowsCustomized.value) {
      await refreshSchedulePreviewSilently()
   }
   await nextTick()
   _measurePreviewBaseSize()
   _updatePreviewScale()
}, { deep: true })

</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 3px;
}

.print-preview-pdf {
  background: #ffffff;
}

.preview-page {
  width: 297mm;
  min-height: 210mm;
}

.corner-page-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4mm 4mm;
}

.corner-template {
  border: 1px solid #0f172a;
  background: #ffffff;
  min-width: 0;
  min-height: 0;
}

.corner-template-table {
  border-collapse: collapse;
  table-layout: fixed;
}

.corner-template-td {
  border: 1px solid #cbd5e1;
  padding: 2px 3px;
  text-align: center;
  vertical-align: middle;
}

.corner-template-td--label {
  font-weight: 700;
}

.corner-template-td--title {
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.02em;
  padding: 6px 4px;
}

.corner-template-td--gap {
  border-left-color: #cbd5e1;
  border-right-color: #cbd5e1;
  border-top-style: dashed;
  border-bottom-style: dashed;
  color: transparent;
}

.corner-paper-table {
  border-collapse: collapse;
  table-layout: fixed;
}

.corner-paper-td {
  border: 1px solid #cbd5e1;
  padding: 6px 8px;
  text-align: center;
  vertical-align: middle;
}

.corner-paper-td--label {
  font-weight: 700;
}

.ticket-table {
  border-collapse: collapse;
  table-layout: fixed;
}

.ticket-td {
  border: 1px solid #cbd5e1;
  padding: 6px 8px;
  text-align: center;
  vertical-align: middle;
}

.ticket-td--label {
  font-weight: 700;
}

.single-preview-item {
  width: 95mm;
  /* min-height: 65mm; Let content dictate height, but usually fixed */
  background: white;
  border: 2px solid #0f172a;
  padding: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.corner-card {
  width: 92mm;
  background: #ffffff;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.corner-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-family: SimSun, "瀹嬩綋", serif;
  font-size: 10pt;
  color: #000;
}

.corner-td {
  border: 1px solid #000;
  height: 13.5pt;
  padding: 0;
  text-align: center;
  vertical-align: middle;
  line-height: 1;
}

.corner-title-td {
  height: 18.75pt;
  font-size: 14pt;
  font-weight: 700;
}

.corner-label-td {
  font-weight: 700;
}

.ticket-card {
  width: 92mm;
  background: #ffffff;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.ticket-xlsx-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-family: SimSun, "瀹嬩綋", serif;
  font-size: 10pt;
  color: #000;
}

.ticket-xlsx-td {
  border: 1px solid #000;
  height: 13.5pt;
  padding: 0;
  text-align: center;
  vertical-align: middle;
  line-height: 1;
}

.ticket-xlsx-title-td {
  height: 18.75pt;
  font-size: 14pt;
  font-weight: 700;
  white-space: normal;
}

.ticket-xlsx-label-td {
  font-weight: 700;
}

.desk-label-table {
  width: 100%;
  height: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-family: SimSun, "瀹嬩綋", serif;
  font-size: 9pt;
  color: #000;
}

.desk-label-td {
  border: 0.5pt solid #000;
  padding: 2mm 1.5mm;
  vertical-align: middle;
  text-align: left;
  white-space: pre-line;
  line-height: 1.15;
}

/* 点名表单元格样式 */
.roll-call-cell {
  border: 0.5pt solid #000;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 1mm;
  text-align: center;
  line-height: 1.3;
  overflow: hidden;
}

.roll-call-seat {
  font-size: 11px;
  font-weight: 700;
  color: #000;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.roll-call-exam-no {
  font-size: 10px;
  color: #374151;
  white-space: nowrap;
}

.roll-call-class {
  font-size: 10px;
  color: #374151;
  white-space: nowrap;
}

.roll-call-checkbox {
  font-size: 10px;
  color: #6b7280;
}
</style>

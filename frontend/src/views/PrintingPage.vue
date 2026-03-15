<template>
  <div class="h-[calc(100vh-8rem)] flex flex-col animate-fade-in bg-slate-50">
    <div class="h-14 bg-white border-b border-slate-200 px-4 flex items-center shrink-0 shadow-sm z-20">
       <div class="flex-1 flex justify-center">
          <div class="bg-slate-100 p-1 rounded-lg flex gap-1 w-full max-w-[560px]">
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
                   <div 
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
                   <div 
                      class="relative border rounded-lg p-3 cursor-pointer transition-all duration-200 group bg-white hover:shadow-md hover:shadow-slate-100"
                      :class="sourceType === 'file' ? 'border-primary-500 bg-primary-50/30 ring-1 ring-primary-500/20' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'"
                      @click="sourceType = 'file'"
                   >
                      <div class="flex items-center gap-3">
                         <div class="p-2 rounded-lg" :class="sourceType === 'file' ? 'bg-primary-100 text-primary-600' : 'bg-slate-100 text-slate-400'">
                            <el-icon><FolderOpened /></el-icon>
                         </div>
                         <div class="flex-1">
                            <div class="text-sm font-bold" :class="sourceType === 'file' ? 'text-primary-700' : 'text-slate-700'">导入数据</div>
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
                            <el-icon class="text-slate-400 hover:text-rose-500 p-1" @click.stop="dataPath = ''"><Close /></el-icon>
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
                   <div class="text-[10px] text-slate-400 leading-relaxed">
                      说明：请上传 Excel 数据文件，第一列为"考场"，后续列为"科目"（值为人数）。系统将自动识别并生成标签。
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
                         <label class="text-xs text-slate-500">科目列表</label>
                         <el-tooltip
                            v-if="sourceType === 'schedule' && isGaokaoMode"
                            content="高考模式下科目信息由编排数据决定，无需手动设置"
                            placement="top"
                         >
                            <el-button size="small" type="info" link disabled>编辑科目</el-button>
                         </el-tooltip>
                         <el-button v-else size="small" type="primary" link @click="openSubjectDialog">编辑科目</el-button>
                      </div>
                      <div class="rounded-lg border border-slate-200 bg-white p-2 min-h-[40px] flex flex-wrap gap-1">
                         <el-tag v-for="(s, idx) in subjectPreview" :key="idx" size="small" type="info" effect="light" class="!border-none !bg-slate-100">{{ s }}</el-tag>
                         <span v-if="subjectPreview.length === 0" class="text-xs text-slate-400 w-full text-center py-1">
                            {{ sourceType === 'schedule' && isGaokaoMode ? '高考模式：科目由编排数据决定' : '点击"编辑科目"添加' }}
                         </span>
                      </div>
                   </div>
                </div>

                <!-- Ticket Config -->
                <div v-if="activeTab === 'ticket'" class="space-y-4 animate-fade-in bg-slate-50 rounded-xl p-4 border border-slate-100">
                   <div class="space-y-1">
                      <label class="text-xs text-slate-500">考试名称</label>
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
                            <span class="text-[10px] text-slate-400 font-mono whitespace-nowrap">{{ row.time || '—' }}</span>
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

             </section>

             <!-- 4. Export Options -->
             <section class="space-y-3">
                <div class="flex items-center gap-2 mb-2">
                   <div class="w-1 h-3 bg-emerald-500 rounded-full"></div>
                   <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">输出格式</span>
                </div>
                <div class="flex gap-4 p-3 bg-slate-50/50 rounded-xl border border-slate-100">
                   <el-checkbox v-model="commonConfig.exportXlsx" label="Excel" size="small" />
                   <el-checkbox v-model="commonConfig.exportPdf" label="PDF (实验性)" size="small" />
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
            class="flex-1 overflow-auto p-8 flex items-center justify-center custom-scrollbar relative z-0"
            :class="previewCursorClass"
            @wheel="handlePreviewWheel"
            @mousedown="handlePreviewMouseDown"
          >
             <div 
               ref="previewPageRef" 
               class="bg-white shadow-[0_20px_50px_-12px_rgba(0,0,0,0.25)] origin-center flex-shrink-0 border border-slate-100"
               :class="isPanningPreview ? '' : 'transition-transform duration-200 ease-out'"
               :style="{ 
                  width: previewPageSizeMm.width, 
                  height: previewPageSizeMm.height,
                  minHeight: previewPageSizeMm.height,
                  transform: `translate(${previewOffset.x}px, ${previewOffset.y}px) scale(${previewScale})`
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
                                              <td class="corner-td">{{ item.考场 }}</td>
                                              <td class="corner-td corner-label-td">考场号</td>
                                              <td class="corner-td">{{ item.考场号 }}</td>
                                           </tr>
                                           <tr>
                                              <td class="corner-td"></td>
                                              <td class="corner-td"></td>
                                              <td class="corner-td corner-label-td">座位号</td>
                                              <td class="corner-td">{{ item.座位号 }}</td>
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
                                              <td class="ticket-xlsx-td">{{ item.考生考号 }}</td>
                                              <td class="ticket-xlsx-td ticket-xlsx-label-td" colspan="2">班级</td>
                                              <td class="ticket-xlsx-td">{{ (item as any)['班级'] }}</td>
                                           </tr>
                                           <tr>
                                              <td class="ticket-xlsx-td ticket-xlsx-label-td">姓名</td>
                                              <td class="ticket-xlsx-td">{{ item.考生姓名 }}</td>
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
                                     <td class="corner-td">{{ cornerPreview.考场 }}</td>
                                     <td class="corner-td corner-label-td">考场号</td>
                                     <td class="corner-td">{{ cornerPreview.考场号 }}</td>
                                  </tr>
                                  <tr>
                                     <td class="corner-td"></td>
                                     <td class="corner-td"></td>
                                     <td class="corner-td corner-label-td">座位号</td>
                                     <td class="corner-td">{{ cornerPreview.座位号 }}</td>
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
                                     <td class="ticket-xlsx-td">{{ ticketPreview.考生考号 }}</td>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td" colspan="2">班级</td>
                                     <td class="ticket-xlsx-td">{{ ticketPreview.班级 }}</td>
                                  </tr>
                                  <tr>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td">姓名</td>
                                     <td class="ticket-xlsx-td">{{ ticketPreview.考生姓名 }}</td>
                                     <td class="ticket-xlsx-td ticket-xlsx-label-td" colspan="2">学号</td>
                                     <td class="ticket-xlsx-td">{{ ticketPreview.学号 }}</td>
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

    <!-- Mapping Dialog -->
    <el-dialog v-model="showMappingDialog" title="字段映射" width="500px">
       <div class="space-y-4">
          <p class="text-sm text-slate-500">请将 Excel 列映射到系统字段:</p>
          <div v-for="(target, key) in requiredFields" :key="key" class="flex items-center gap-4">
             <div class="w-24 text-sm font-bold text-right text-slate-700">{{ target.label }} <span v-if="target.required" class="text-rose-500">*</span></div>
             <el-select v-model="mapping[key]" placeholder="选择列" size="small" class="flex-1" clearable>
                <el-option v-for="h in headers" :key="h" :label="h" :value="h" />
             </el-select>
          </div>
       </div>
       <template #footer>
          <span class="dialog-footer">
             <el-button @click="showMappingDialog = false">取消</el-button>
             <el-button type="primary" @click="handleConfirmMapping">确认并预览</el-button>
          </span>
       </template>
    </el-dialog>

    <el-dialog v-model="showSubjectDialog" title="科目与时间设置" width="720px" class="!rounded-2xl" align-center append-to-body>
       <div class="flex flex-col h-[520px]">
          <!-- Top Control Bar -->
          <div class="flex items-center justify-between p-1 mb-4 bg-slate-50 border border-slate-100 rounded-xl">
             <div class="flex items-center gap-4 px-3">
                <span class="text-sm font-bold text-slate-600">科目数量</span>
                <el-input-number v-model="subjectDraftCount" :min="1" :max="20" size="small" class="!w-32" controls-position="right" />
             </div>
             <el-button type="primary" link :loading="syncingSubjects" @click="handleSyncSubjects" class="!px-4 !py-2 !h-9 hover:!bg-white hover:shadow-sm rounded-lg transition-all">
                <el-icon class="mr-1.5"><Notebook /></el-icon> 从科目设置同步
             </el-button>
          </div>

          <!-- Main List -->
          <div class="flex-1 rounded-xl border border-slate-200 overflow-hidden bg-white flex flex-col shadow-sm">
             <!-- Header -->
             <div class="grid grid-cols-[56px_1fr_0.9fr_1fr] gap-0 bg-slate-50/80 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider backdrop-blur-sm z-10">
                <div class="py-2.5 text-center border-r border-slate-100">序号</div>
                <div class="py-2.5 px-4 border-r border-slate-100">科目名称</div>
                <div class="py-2.5 px-4 border-r border-slate-100">日期</div>
                <div class="py-2.5 px-4">时间段</div>
             </div>
             
             <!-- Scrollable Area -->
             <div class="flex-1 overflow-y-auto custom-scrollbar p-0 bg-slate-50/30">
                <transition-group name="list" tag="div" class="space-y-px">
                   <div 
                     v-for="(row, idx) in subjectDraftRows" 
                     :key="idx" 
                     class="grid grid-cols-[56px_1fr_0.9fr_1fr] gap-0 items-center bg-white group hover:bg-blue-50/50 transition-colors duration-200"
                   >
                      <div class="py-2 text-center text-xs font-mono text-slate-400 group-hover:text-primary-500 font-bold border-r border-transparent group-hover:border-blue-100/50">
                         {{ String(idx + 1).padStart(2, '0') }}
                      </div>
                      <div class="p-1.5 border-r border-transparent group-hover:border-blue-100/50">
                         <el-input 
                           v-model="row.name" 
                           placeholder="科目名" 
                           class="!w-full"
                           :class="{'font-bold text-slate-700': row.name}"
                         >
                            <template #prefix>
                               <el-icon class="text-slate-300 group-hover:text-primary-400 transition-colors"><Reading /></el-icon>
                            </template>
                         </el-input>
                      </div>
                      <div class="p-1.5 border-r border-transparent group-hover:border-blue-100/50">
                         <el-input 
                          :model-value="getRowDate(row)"
                          placeholder="如: 6月7日"
                          class="!w-full"
                          @update:model-value="(v: string) => setRowDate(row, v)"
                         >
                            <template #prefix>
                              <el-icon class="text-slate-300 group-hover:text-primary-400 transition-colors"><Calendar /></el-icon>
                            </template>
                         </el-input>
                      </div>
                      <div class="p-1.5">
                         <el-time-picker
                           :model-value="getRowTimeRange(row)"
                           is-range
                           value-format="HH:mm"
                           format="HH:mm"
                           range-separator="-"
                           start-placeholder="开始时间"
                           end-placeholder="结束时间"
                           :prefix-icon="Timer"
                           class="!w-full"
                           @update:model-value="(v: any) => setRowTimeRange(row, v)"
                         />
                      </div>
                   </div>
                </transition-group>
                
                <!-- Empty State/Padding -->
                <div v-if="subjectDraftRows.length === 0" class="h-full flex flex-col items-center justify-center text-slate-400 py-12">
                   <el-icon size="32" class="mb-2 opacity-50"><FolderOpened /></el-icon>
                   <span class="text-xs">暂无科目</span>
                </div>
             </div>
          </div>
          
          <!-- Hint -->
          <div class="mt-2 flex items-center gap-2 text-[10px] text-slate-400 px-1">
             <el-icon><InfoFilled /></el-icon>
             <span>提示：拖动滑块或输入数字可调整科目总数；点击"从系统同步"可获取最新考试安排。</span>
          </div>
       </div>
       <template #footer>
          <span class="dialog-footer">
             <el-button @click="showSubjectDialog = false">取消</el-button>
             <el-button type="primary" @click="handleSaveSubjects">保存设置</el-button>
          </span>
       </template>
    </el-dialog>

    <el-dialog v-model="showDeskLayoutDialog" title="设置座位布局" width="720px" class="!rounded-2xl" align-center append-to-body>
       <div class="space-y-6 px-6 py-4">
          <div class="grid grid-cols-2 gap-8">
             <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">布局方式</label>
                <el-select v-model="deskLayoutDraft.layoutName" class="!w-full" size="default">
                   <el-option v-for="opt in deskLayoutOptions" :key="opt.name" :label="opt.name" :value="opt.name" />
                   <el-option label="自定义" value="自定义" />
                </el-select>
             </div>
             <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">排列方式</label>
                <el-select v-model="deskLayoutDraft.layoutPattern" class="!w-full" size="default">
                   <el-option label="S型横排" value="S型横排" />
                   <el-option label="S型竖排" value="S型竖排" />
                   <el-option label="Z型横排" value="Z型横排" />
                   <el-option label="Z型竖排" value="Z型竖排" />
                </el-select>
             </div>
          </div>

          <div v-if="deskLayoutDraft.layoutName === '自定义'" class="space-y-2 animate-fade-in">
             <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">自定义每列人数</label>
             <el-input v-model="deskLayoutDraft.customCountsText" placeholder="例如：7,7,8,8" size="default">
                <template #prefix>
                   <el-icon class="text-slate-400"><Grid /></el-icon>
                </template>
             </el-input>
             <div class="text-[10px] text-slate-400 flex items-center gap-1.5">
                <el-icon><InfoFilled /></el-icon>
                <span>将自动计算行数=最大列人数，列数=输入列数。</span>
             </div>
          </div>

          <div class="space-y-2">
             <div class="flex items-center justify-between">
                <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">起始位</label>
             </div>
             <div class="grid grid-cols-2 gap-3">
                <div 
                   class="cursor-pointer border-2 rounded-xl p-3 flex flex-col items-center gap-2 transition-all duration-200 hover:shadow-md"
                   :class="deskLayoutDraft.startPos === 'left' ? 'border-primary-500 bg-primary-50/50' : 'border-slate-100 bg-white hover:border-slate-200'"
                   @click="deskLayoutDraft.startPos = 'left'"
                >
                   <span class="text-sm font-bold" :class="deskLayoutDraft.startPos === 'left' ? 'text-primary-700' : 'text-slate-700'">左手位</span>
                   <span class="text-[10px] text-center leading-tight" :class="deskLayoutDraft.startPos === 'left' ? 'text-primary-600/80' : 'text-slate-400'">
                      监考人员面向考生，左手方向靠边第一个座位为起始位置
                   </span>
                </div>
                
                <div 
                   class="cursor-pointer border-2 rounded-xl p-3 flex flex-col items-center gap-2 transition-all duration-200 hover:shadow-md"
                   :class="deskLayoutDraft.startPos === 'right' ? 'border-primary-500 bg-primary-50/50' : 'border-slate-100 bg-white hover:border-slate-200'"
                   @click="deskLayoutDraft.startPos = 'right'"
                >
                   <span class="text-sm font-bold" :class="deskLayoutDraft.startPos === 'right' ? 'text-primary-700' : 'text-slate-700'">右手位</span>
                   <span class="text-[10px] text-center leading-tight" :class="deskLayoutDraft.startPos === 'right' ? 'text-primary-600/80' : 'text-slate-400'">
                      监考人员面向考生，右手方向靠边第一个座位为起始位置
                   </span>
                </div>
             </div>
             <div class="flex justify-end pt-1">
                <span class="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded flex items-center gap-1">
                   <el-icon><InfoFilled /></el-icon>
                   仅影响座位布局预览
                </span>
             </div>
          </div>
       </div>
       <template #footer>
          <span class="dialog-footer">
             <el-button @click="showDeskLayoutDialog = false" size="default">取消</el-button>
             <el-button type="primary" @click="applyDeskLayoutDraft" size="default">应用设置</el-button>
          </span>
       </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { 
  Printer, VideoPlay, FolderOpened, DocumentChecked, Close, 
  Document, Minus, Plus, FullScreen, Grid, DataLine, Select, 
  Calendar, CircleCheckFilled, Download, Setting, Fold, Expand, Delete, School,
  Refresh, Reading, Timer, InfoFilled, Notebook, Back, Right
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { open, saveAndRun } from '@/lib/dialog'
import { pythonBackend } from '@/lib/pythonBackend'

// --- State ---
const getStored = (key: string, def: string) => sessionStorage.getItem(`printing_pref_${key}`) || def

const sidebarCollapsed = ref(getStored('sidebarCollapsed', 'false') === 'true')
const activeTab = ref(getStored('activeTab', 'corner'))
const generating = ref(false)

// Data Source
const sourceType = ref('empty') // 'empty' | 'file' | 'schedule'
const totalCount = ref(800)
const loadingSchedule = ref(false)
const scheduleArrangementMode = ref('') // 考场编排模式：'gaokao_mode' | 'normal_mode' | 'subject_mode' | 'random_mode'

const dataPath = ref('')
const dataFileName = computed(() => dataPath.value.split(/[\\/]/).pop())
const isGaokaoMode = computed(() => scheduleArrangementMode.value === 'gaokao_mode')
const headers = ref<string[]>([])
const showMappingDialog = ref(false)
const previewData = ref<any[]>([])
const previewTotal = ref(0)

const previewViewportRef = ref<HTMLElement | null>(null)
const previewPageRef = ref<HTMLElement | null>(null)
const previewOverlayRef = ref<HTMLElement | null>(null)
const previewScale = ref(1)
const autoFit = ref(true)
const previewOffset = reactive({ x: 0, y: 0 })
const isPanningPreview = ref(false)
const isCtrlDown = ref(false)
const previewMode = ref<'style' | 'print'>('style')
const deskPreviewMode = ref<'seat' | 'print'>('seat')
const previewBaseWidth = ref(0)
const previewBaseHeight = ref(0)
let previewResizeObserver: ResizeObserver | null = null

function _getMaxAutoFitScale() {
   if (activeTab.value === 'desk') return 1
   return 1.5
}

const handleZoomIn = () => {
   autoFit.value = false
   previewScale.value = Math.min(2.0, previewScale.value + 0.1)
}

const handleZoomOut = () => {
   autoFit.value = false
   previewScale.value = Math.max(0.2, previewScale.value - 0.1)
}

const handleAutoFit = () => {
   autoFit.value = true
   previewOffset.x = 0
   previewOffset.y = 0
   _updatePreviewScale()
}

const handlePreviewWheel = (e: WheelEvent) => {
   if (e.ctrlKey) {
      e.preventDefault()
      e.stopPropagation()
      
      // Zoom In/Out based on scroll direction
      // deltaY < 0 means scrolling up (Zoom In)
      // deltaY > 0 means scrolling down (Zoom Out)
      const factor = 0.001
      const delta = -e.deltaY * factor
      
      const next = Math.min(3.0, Math.max(0.2, previewScale.value + delta))
      if (next !== previewScale.value) {
         previewScale.value = next
         autoFit.value = false
      }
   }
}

const previewCursorClass = computed(() => {
   if (isPanningPreview.value) return 'cursor-grabbing select-none'
   if (isCtrlDown.value) return 'cursor-grab'
   return ''
})

let _panStart: { x: number; y: number; ox: number; oy: number } | null = null

function _endPreviewPan() {
   if (!isPanningPreview.value) return
   isPanningPreview.value = false
   _panStart = null
   document.body.style.userSelect = ''
   window.removeEventListener('mousemove', _handlePreviewMouseMove, true)
   window.removeEventListener('mouseup', _handlePreviewMouseUp, true)
}

function _handlePreviewMouseMove(e: MouseEvent) {
   if (!isPanningPreview.value || !_panStart) return
   previewOffset.x = _panStart.ox + (e.clientX - _panStart.x)
   previewOffset.y = _panStart.oy + (e.clientY - _panStart.y)
}

function _handlePreviewMouseUp() {
   _endPreviewPan()
}

function handlePreviewMouseDown(e: MouseEvent) {
   if (!e.ctrlKey) return
   if (e.button !== 0) return
   e.preventDefault()
   e.stopPropagation()

   autoFit.value = false
   isPanningPreview.value = true
   document.body.style.userSelect = 'none'
   _panStart = { x: e.clientX, y: e.clientY, ox: previewOffset.x, oy: previewOffset.y }
   window.addEventListener('mousemove', _handlePreviewMouseMove, true)
   window.addEventListener('mouseup', _handlePreviewMouseUp, true)
}

// Persistence Watchers
watch(sidebarCollapsed, (val) => sessionStorage.setItem('printing_pref_sidebarCollapsed', String(val)))
watch(activeTab, (val) => sessionStorage.setItem('printing_pref_activeTab', val))

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
         })
      } catch {}
   }, 600)
}

watch(activeTab, async (val) => {
   if (val !== 'corner' && val !== 'ticket') previewMode.value = 'style'
   if (val === 'exam_bag_label') showMappingDialog.value = false
   // Always auto-fit when switching tabs
   autoFit.value = true
   previewOffset.x = 0
   previewOffset.y = 0
   if (sourceType.value === 'file' && dataPath.value) {
      const canLoad = val === 'exam_bag_label' || isMappingComplete()
      if (canLoad) {
         await loadPreview()
      }
   }
   // 如果数据来源为考场编排，切换tab时自动刷新数据
   if (sourceType.value === 'schedule') {
      await handleLoadFromSchedule()
   }
   await nextTick()
   _measurePreviewBaseSize()
   _updatePreviewScale()
}, { immediate: true })

watch(previewMode, async () => {
   await nextTick()
   handleAutoFit()
})

watch(deskPreviewMode, async () => {
   autoFit.value = true
   previewOffset.x = 0
   previewOffset.y = 0
   await nextTick()
   _measurePreviewBaseSize()
   _updatePreviewScale()
})

const tabs = [
  { id: 'corner', name: '台角纸' },
  { id: 'desk', name: '桌角标签' },
  { id: 'ticket', name: '准考证' },
  { id: 'table', name: '考生信息表' },
  { id: 'exam_bag_label', name: '试卷袋' }
]

const commonConfig = reactive({
   exportXlsx: true,
   exportPdf: false
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
   }
})

watch(config, _scheduleSaveConfig, { deep: true })
watch(commonConfig, _scheduleSaveConfig, { deep: true })
watch(totalCount, _scheduleSaveConfig)
watch(sourceType, _scheduleSaveConfig)

const studentInfoTitles = reactive<{ class: string; examroom: string }>({ class: '', examroom: '' })
onMounted(() => {
   const raw = sessionStorage.getItem('printing_pref_studentInfoTitles_v1')
   if (raw) {
      try {
         const parsed = JSON.parse(raw)
         studentInfoTitles.class = String(parsed?.class ?? '')
         studentInfoTitles.examroom = String(parsed?.examroom ?? '')
      } catch {}
   }
   if (!studentInfoTitles.class) studentInfoTitles.class = config.table.title
   if (!studentInfoTitles.examroom) studentInfoTitles.examroom = config.table.title
})

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
   sessionStorage.setItem('printing_pref_studentInfoTitles_v1', JSON.stringify({ ...studentInfoTitles }))
})

type SubjectRow = { name: string; time: string }

const showSubjectDialog = ref(false)
const syncingSubjects = ref(false)
const subjectRows = ref<SubjectRow[]>([])
const subjectDraftRows = ref<SubjectRow[]>([])
const subjectDraftCount = ref(9)

const subjectPreview = computed(() => {
   return subjectRows.value.map(r => r.name).filter(v => v.trim()).slice(0, 7)
})

const subjectPreviewWithTime = computed(() => {
   return subjectRows.value
      .filter(r => r.name.trim() || r.time.trim())
      .slice(0, 7)
})

function _loadStoredSubjectRows(): SubjectRow[] | null {
   try {
      const raw = sessionStorage.getItem('printing_pref_subjectRows_v1')
      if (!raw) return null
      const parsed = JSON.parse(raw)
      if (!Array.isArray(parsed)) return null
      return parsed.map((r: any) => ({ name: String(r?.name ?? ''), time: String(r?.time ?? '') }))
   } catch {
      return null
   }
}

function _persistSubjectRows(rows: SubjectRow[]) {
   sessionStorage.setItem('printing_pref_subjectRows_v1', JSON.stringify(rows))
}

function _ensureSubjectRowsLen(rows: SubjectRow[], count: number): SubjectRow[] {
   const safeCount = Math.min(20, Math.max(1, Math.floor(count || 0)))
   const next: SubjectRow[] = rows.map(r => ({ name: String(r?.name ?? ''), time: String(r?.time ?? '') }))
   if (next.length > safeCount) return next.slice(0, safeCount)
   while (next.length < safeCount) next.push({ name: '', time: '' })
   return next
}

function _formatMonthDay(examDate: string): string {
   const s = String(examDate || '').trim()
   const m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/)
   if (!m) return ''
   const month = String(parseInt(m[2], 10))
   const day = String(parseInt(m[3], 10))
   return `${month}月${day}日`
}

function _parseSubjectTime(raw: string): { dateText: string; range?: [string, string] } {
   const s = String(raw ?? '').trim()
   const m = s.match(/(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})/)
   if (!m) return { dateText: s }
   const start = m[1]
   const end = m[2]
   const idx = m.index ?? 0
   const dateText = `${s.slice(0, idx)}${s.slice(idx + m[0].length)}`.trim()
   return { dateText, range: [start, end] }
}

function _buildSubjectTime(dateText: string, range?: [string, string]): string {
   const d = String(dateText ?? '').trim()
   if (range && range[0] && range[1]) return `${d}${range[0]}-${range[1]}`.trim()
   return d
}

function getRowDate(row: SubjectRow): string {
   return _parseSubjectTime(row.time).dateText
}

function setRowDate(row: SubjectRow, dateText: string) {
   const parsed = _parseSubjectTime(row.time)
   row.time = _buildSubjectTime(dateText, parsed.range)
}

function getRowTimeRange(row: SubjectRow): [string, string] | undefined {
   return _parseSubjectTime(row.time).range
}

function setRowTimeRange(row: SubjectRow, val: unknown) {
   const parsed = _parseSubjectTime(row.time)
   if (Array.isArray(val) && val.length === 2 && val[0] && val[1]) {
      row.time = _buildSubjectTime(parsed.dateText, [String(val[0]), String(val[1])])
      return
   }
   row.time = _buildSubjectTime(parsed.dateText)
}

function openSubjectDialog() {
   subjectDraftCount.value = subjectRows.value.length || 9
   subjectDraftRows.value = subjectRows.value.map(r => ({ ...r }))
   subjectDraftRows.value = _ensureSubjectRowsLen(subjectDraftRows.value, subjectDraftCount.value)
   showSubjectDialog.value = true
}

watch(subjectDraftCount, (val) => {
   subjectDraftRows.value = _ensureSubjectRowsLen(subjectDraftRows.value, val)
})

async function handleSyncSubjects() {
   syncingSubjects.value = true
   try {
      const res = await pythonBackend.request<any>('subjects.list', {})
      const list = (res?.subjects || []) as any[]
      const mapped = list.slice(0, 20).map((s) => {
         const name = String(s?.name ?? '')
         const datePart = _formatMonthDay(String(s?.exam_date ?? ''))
         const timePart = String(s?.exam_time ?? '')
         return { name, time: `${datePart}${timePart}`.trim() }
      })
      subjectDraftCount.value = Math.min(20, Math.max(1, mapped.length || 9))
      subjectDraftRows.value = _ensureSubjectRowsLen(mapped, subjectDraftCount.value)
      ElMessage.success('已从科目设置同步')
   } catch (e) {
      ElMessage.error('同步失败: ' + e)
   } finally {
      syncingSubjects.value = false
   }
}

function handleSaveSubjects() {
   const rows = _ensureSubjectRowsLen(subjectDraftRows.value, subjectDraftCount.value)
   subjectRows.value = rows
   _persistSubjectRows(rows)
   showSubjectDialog.value = false
}

function _measurePreviewBaseSize() {
   const pageEl = previewPageRef.value
   if (!pageEl) return
   const rect = pageEl.getBoundingClientRect()
   const s = previewScale.value || 1
   if (rect.width > 0 && rect.height > 0 && s > 0) {
      previewBaseWidth.value = rect.width / s
      previewBaseHeight.value = rect.height / s
   }
}

function _updatePreviewScale() {
   if (!autoFit.value) return
   const viewportEl = previewViewportRef.value
   if (!viewportEl) return
   
   const baseW = previewBaseWidth.value
   const baseH = previewBaseHeight.value
   const { w, h } = previewTargetPx.value
   const targetWidth = baseW > 0 ? baseW : w
   const targetHeight = baseH > 0 ? baseH : h
   
   const availableW = Math.max(0, viewportEl.clientWidth - 64) // 32px padding * 2
   let availableH = Math.max(0, viewportEl.clientHeight - 64)
   const overlayEl = previewOverlayRef.value
   if (overlayEl) {
      const overlayRect = overlayEl.getBoundingClientRect()
      if (overlayRect.height > 0) availableH = Math.max(0, availableH - overlayRect.height - 24)
   }
   
   const sx = availableW / targetWidth
   const sy = availableH / targetHeight
   
   const next = Math.min(sx, sy) * 0.98
   previewScale.value = Math.min(_getMaxAutoFitScale(), Math.max(0.3, Number.isFinite(next) ? next : 1))
}

function _initPreviewAutoScale() {
   if (previewResizeObserver) previewResizeObserver.disconnect()
   if (!previewViewportRef.value) return
   previewResizeObserver = new ResizeObserver(() => _updatePreviewScale())
   previewResizeObserver.observe(previewViewportRef.value)
   _updatePreviewScale()
}

onMounted(async () => {
   // Restore printing state
   try {
      const state = await pythonBackend.request<any>('printing.getState', {})
      if (state && state.sourceType === 'file' && state.dataPath) {
         sourceType.value = 'file'
         dataPath.value = state.dataPath
         headers.value = state.headers || []
         previewData.value = state.data || []
         previewTotal.value = state.total || 0

         if (state.mapping) {
            for (const k of Object.keys(mapping)) delete (mapping as any)[k]
            Object.assign(mapping, state.mapping)
         }

         // Update filePreviewCache as well
         filePreviewCache.dataPath = state.dataPath
         filePreviewCache.headers = state.headers || []
         filePreviewCache.mapping = state.mapping || {}
         filePreviewCache.data = state.data || []
         filePreviewCache.total = state.total || 0
      } else if (state && state.sourceType === 'schedule') {
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
      }
      if (state && state.commonConfig && typeof state.commonConfig === 'object') {
         const cc = state.commonConfig
         if (cc.exportXlsx != null) commonConfig.exportXlsx = cc.exportXlsx
         if (cc.exportPdf != null) commonConfig.exportPdf = cc.exportPdf
      }
      if (state && state.totalCount != null) {
         totalCount.value = state.totalCount
      }

      // Re-sync studentInfoTitles from restored config.table.title if sessionStorage had no saved value
      if (!sessionStorage.getItem('printing_pref_studentInfoTitles_v1')) {
         studentInfoTitles.class = config.table.title
         studentInfoTitles.examroom = config.table.title
      }
   } catch (e) {
      console.error('Failed to restore printing state:', e)
   }

   const stored = _loadStoredSubjectRows()
   if (stored && stored.length) {
      subjectRows.value = _ensureSubjectRowsLen(stored, stored.length)
   } else {
      subjectRows.value = _ensureSubjectRowsLen([], 9)
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

function _handleKeyDown(e: KeyboardEvent) {
   if (e.key === 'Control') isCtrlDown.value = true
}

function _handleKeyUp(e: KeyboardEvent) {
   if (e.key === 'Control') {
      isCtrlDown.value = false
      _endPreviewPan()
   }
}

function _handleWindowBlur() {
   isCtrlDown.value = false
   _endPreviewPan()
}

onMounted(() => {
   window.addEventListener('keydown', _handleKeyDown)
   window.addEventListener('keyup', _handleKeyUp)
   window.addEventListener('blur', _handleWindowBlur)
})

onBeforeUnmount(() => {
   window.removeEventListener('keydown', _handleKeyDown)
   window.removeEventListener('keyup', _handleKeyUp)
   window.removeEventListener('blur', _handleWindowBlur)
   _endPreviewPan()
})

// Mapping
const mapping = reactive<Record<string, string>>({})
const requiredFields = {
   '考场号': { label: '考场号', required: true },
   '考场': { label: '考场名称', required: true },
   '座位号': { label: '座位号', required: true },
   '考生姓名': { label: '姓名', required: true },
   '考生考号': { label: '考号', required: true },
   '班级': { label: '班级', required: true },
   '学号': { label: '学号', required: true },
   '首选': { label: '首选科目', required: false },
   '选科1': { label: '再选科目1', required: false },
   '选科2': { label: '再选科目2', required: false },
}

type FilePreviewCache = {
   dataPath: string
   headers: string[]
   mapping: Record<string, string>
   data: any[]
   total: number
}

const filePreviewCache = reactive<FilePreviewCache>({
   dataPath: '',
   headers: [],
   mapping: {},
   data: [],
   total: 0,
})

const schedulePreviewCache = reactive<{ data: any[]; total: number }>({ data: [], total: 0 })

function _snapshotMapping(): Record<string, string> {
   const snap: Record<string, string> = {}
   for (const k of Object.keys(mapping)) {
      const v = mapping[k]
      if (typeof v === 'string' && v.trim()) snap[k] = v
   }
   return snap
}

function _applyMappingSnapshot(snap: Record<string, string>) {
   for (const k of Object.keys(mapping)) delete (mapping as any)[k]
   for (const [k, v] of Object.entries(snap || {})) {
      mapping[k] = String(v ?? '')
   }
}

function _cacheCurrentFileState() {
   filePreviewCache.dataPath = dataPath.value
   filePreviewCache.headers = headers.value.slice()
   filePreviewCache.mapping = _snapshotMapping()
   filePreviewCache.data = previewData.value.slice()
   filePreviewCache.total = previewTotal.value
}

function _cacheCurrentScheduleState() {
   schedulePreviewCache.data = previewData.value.slice()
   schedulePreviewCache.total = previewTotal.value
}

const handleResetPage = async () => {
   try {
      await ElMessageBox.confirm(
         '确定要初始化当前页面吗？这将清除所有数据与设置。',
         '初始化页面',
         { type: 'warning', confirmButtonText: '初始化', cancelButtonText: '取消' }
      )
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

   dataPath.value = ''
   headers.value = []
   showMappingDialog.value = false
   previewData.value = []
   previewTotal.value = 0

   for (const k of Object.keys(mapping)) delete (mapping as any)[k]
   filePreviewCache.dataPath = ''
   filePreviewCache.headers = []
   filePreviewCache.mapping = {}
   filePreviewCache.data = []
   filePreviewCache.total = 0
   schedulePreviewCache.data = []
   schedulePreviewCache.total = 0

   commonConfig.exportXlsx = true
   commonConfig.exportPdf = false

   config.corner.title = '2025年秋季期末考试'
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

   studentInfoTitles.class = config.table.title
   studentInfoTitles.examroom = config.table.title

  subjectRows.value = _ensureSubjectRowsLen([], 9)

   autoFit.value = true
   previewMode.value = 'style'
   await nextTick()
   _measurePreviewBaseSize()
   _updatePreviewScale()

   sessionStorage.removeItem('printing_pref_sidebarCollapsed')
   sessionStorage.removeItem('printing_pref_activeTab')
   sessionStorage.removeItem('printing_pref_subjectRows_v1')
   sessionStorage.removeItem('printing_pref_studentInfoTitles_v1')
}

// --- Computed ---
const hasPreviewData = computed(() => {
    if (sourceType.value === 'empty') return true
    return previewData.value.length > 0
})

const displayData = computed(() => {
    if (sourceType.value === 'empty') {
        return []
    }
    return previewData.value
})

const tablePreviewRows = computed(() => {
   const rows = displayData.value.slice(0, 20).map((item: any, idx: number) => {
      const name = String(item?.['考生姓名'] ?? item?.['姓名'] ?? '张三')
      const examNo = String(item?.['考生考号'] ?? item?.['考号'] ?? `1000${idx}`)
      const roomNo = String(item?.['考场号'] ?? '01')
      const seatNo = String(item?.['座位号'] ?? String(idx + 1).padStart(2, '0'))
      const clsRaw = item?.['班级']
      const clsStr = clsRaw === undefined || clsRaw === null ? '' : String(clsRaw)
      const clsDigits = clsStr.match(/\d+/)?.[0]
      const classLabel = clsDigits ? `${clsDigits}班` : (clsStr || '高三(1)班')
      const studentNo = String(item?.['学号'] ?? (idx + 1))
      const subjects = String(item?.['首选'] ?? '物理') + ' ' + String(item?.['选科1'] ?? '化学') + ' ' + String(item?.['选科2'] ?? '生物')
      return { name, examNo, roomNo, seatNo, classLabel, studentNo, subjects: subjects.trim() }
   })

   if (config.table.groupMode === 'examroom') {
      return rows.sort((a, b) => {
         const ra = parseInt(a.roomNo, 10)
         const rb = parseInt(b.roomNo, 10)
         if (!Number.isNaN(ra) && !Number.isNaN(rb) && ra !== rb) return ra - rb
         if (a.roomNo !== b.roomNo) return a.roomNo.localeCompare(b.roomNo, 'zh-CN')
         const sa = parseInt(a.seatNo, 10)
         const sb = parseInt(b.seatNo, 10)
         if (!Number.isNaN(sa) && !Number.isNaN(sb) && sa !== sb) return sa - sb
         return a.seatNo.localeCompare(b.seatNo, 'zh-CN')
      })
   }

   return rows.sort((a, b) => {
      if (a.classLabel !== b.classLabel) return a.classLabel.localeCompare(b.classLabel, 'zh-CN')
      const sa = parseInt(a.studentNo, 10)
      const sb = parseInt(b.studentNo, 10)
      if (!Number.isNaN(sa) && !Number.isNaN(sb) && sa !== sb) return sa - sb
      return a.studentNo.localeCompare(b.studentNo, 'zh-CN')
   })
})

const studentInfoColumns = computed(() => {
   const toPercent = (w: number, total: number) => `${((w / total) * 100).toFixed(4)}%`
   if (config.table.includeSubjectFields) {
      const weights = [5, 5, 7, 12, 5, 5, 5, 9, 6, 5]
      const total = weights.reduce((a, b) => a + b, 0)
      const widths = weights.map(w => toPercent(w, total))
      return [
         { key: 'class', label: '班级', width: widths[0] },
         { key: 'studentNo', label: '学号', width: widths[1] },
         { key: 'name', label: '姓名', width: widths[2] },
         { key: 'examNo', label: '考号', width: widths[3] },
         { key: 'first', label: '首选', width: widths[4] },
         { key: 'sub1', label: '选科1', width: widths[5] },
         { key: 'sub2', label: '选科2', width: widths[6] },
         { key: 'room', label: '考场', width: widths[7] },
         { key: 'roomNo', label: '考场号', width: widths[8] },
         { key: 'seatNo', label: '座位', width: widths[9] },
      ] as const
   }
   const weights = [5, 5, 7, 12, 9, 6, 5]
   const total = weights.reduce((a, b) => a + b, 0)
   const widths = weights.map(w => toPercent(w, total))
   return [
      { key: 'class', label: '班级', width: widths[0] },
      { key: 'studentNo', label: '学号', width: widths[1] },
      { key: 'name', label: '姓名', width: widths[2] },
      { key: 'examNo', label: '考号', width: widths[3] },
      { key: 'room', label: '考场', width: widths[4] },
      { key: 'roomNo', label: '考场号', width: widths[5] },
      { key: 'seatNo', label: '座位', width: widths[6] },
   ] as const
})

const studentInfoPrintLayout = computed(() => {
   const ptToMm = (pt: number) => `${(pt * 0.3527777778).toFixed(2)}mm`
   const contentHeightMm = 297 - 20
   const safetyGapPt = 24

   const isExamroom = config.table.groupMode === 'examroom'
   const titlePt = 22
   const headerPt = 20
   const summaryPt = isExamroom ? 16.5 : 16
   const bodyMinPt = isExamroom ? 16.5 : 11

   const titleMm = titlePt * 0.3527777778
   const headerMm = headerPt * 0.3527777778
   const summaryMm = summaryPt * 0.3527777778
   const bodyMinMm = bodyMinPt * 0.3527777778
   const safetyGapMm = safetyGapPt * 0.3527777778

   const maxRowsLast = Math.max(
      5,
      Math.floor((contentHeightMm - titleMm - headerMm - summaryMm - safetyGapMm) / bodyMinMm)
   )
   const maxRowsMid = Math.max(
      5,
      Math.floor((contentHeightMm - titleMm - headerMm - safetyGapMm) / bodyMinMm)
   )

   const fontSize = config.table.includeSubjectFields ? 8 : 9

   const bodyH =
      sourceType.value === 'empty'
         ? `${Math.max(1, (contentHeightMm - titleMm - headerMm - safetyGapMm) / (isExamroom ? 42 : 50)).toFixed(2)}mm`
         : ptToMm(bodyMinPt)

   return {
      titleH: ptToMm(titlePt),
      headerH: ptToMm(headerPt),
      bodyH,
      summaryH: ptToMm(summaryPt),
      maxRowsMid,
      maxRowsLast,
      fontSizePx: `${fontSize}px`,
      titleFontSizePx: '14px',
   }
})

type _StudentInfoSortKey = [number, number | string]

function _compareStudentInfoSortKey(a: _StudentInfoSortKey, b: _StudentInfoSortKey) {
   if (a[0] !== b[0]) return a[0] - b[0]
   const av = a[1]
   const bv = b[1]
   if (typeof av === 'number' && typeof bv === 'number') return av - bv
   return String(av).localeCompare(String(bv), 'zh-CN')
}

function _studentInfoClassSortKey(v: any): _StudentInfoSortKey {
   const s = String(v ?? '').trim()
   if (/^\d+$/.test(s)) return [0, Number(s)]
   return [1, s]
}

function _studentInfoExamroomSortKey(v: any): _StudentInfoSortKey {
   const s = String(v ?? '').trim()
   if (/^\d+$/.test(s)) return [0, Number(s)]
   if (s) return [1, s]
   return [2, '']
}

function _studentInfoSeatSortKey(v: any): _StudentInfoSortKey {
   const s = String(v ?? '').trim()
   if (/^\d+$/.test(s)) return [0, Number(s)]
   return [1, s]
}

const studentInfoFirstGroupRows = computed(() => {
   const data = displayData.value as any[]
   if (!Array.isArray(data) || !data.length) return []

   const isExamroom = config.table.groupMode === 'examroom'
   const keyOf = (it: any) => String((isExamroom ? it?.['考场号'] : it?.['班级']) ?? '').trim()

   const groups = new Map<string, any[]>()
   for (const it of data) {
      const k = keyOf(it)
      if (!groups.has(k)) groups.set(k, [])
      groups.get(k)!.push(it)
   }

   const keys = Array.from(groups.keys())
   keys.sort((a, b) => {
      const ka = isExamroom ? _studentInfoExamroomSortKey(a) : _studentInfoClassSortKey(a)
      const kb = isExamroom ? _studentInfoExamroomSortKey(b) : _studentInfoClassSortKey(b)
      return _compareStudentInfoSortKey(ka, kb)
   })

   const firstKey = keys[0] ?? ''
   const rows = (groups.get(firstKey) || []).slice()
   if (isExamroom) {
      rows.sort((a, b) => {
         const ka = _studentInfoExamroomSortKey(a?.['考场号'])
         const kb = _studentInfoExamroomSortKey(b?.['考场号'])
         const kcmp = _compareStudentInfoSortKey(ka, kb)
         if (kcmp) return kcmp

         const sa = _studentInfoSeatSortKey(a?.['座位号'] ?? a?.['座位'])
         const sb = _studentInfoSeatSortKey(b?.['座位号'] ?? b?.['座位'])
         const scmp = _compareStudentInfoSortKey(sa, sb)
         if (scmp) return scmp

         const ca = _studentInfoClassSortKey(a?.['班级'])
         const cb = _studentInfoClassSortKey(b?.['班级'])
         const ccmp = _compareStudentInfoSortKey(ca, cb)
         if (ccmp) return ccmp

         const na = _studentInfoSeatSortKey(a?.['学号'])
         const nb = _studentInfoSeatSortKey(b?.['学号'])
         return _compareStudentInfoSortKey(na, nb)
      })
   } else {
      rows.sort((a, b) => {
         const na = _studentInfoSeatSortKey(a?.['学号'])
         const nb = _studentInfoSeatSortKey(b?.['学号'])
         const ncmp = _compareStudentInfoSortKey(na, nb)
         if (ncmp) return ncmp
         const ea = String(a?.['考生考号'] ?? a?.['考号'] ?? '').trim()
         const eb = String(b?.['考生考号'] ?? b?.['考号'] ?? '').trim()
         return ea.localeCompare(eb, 'zh-CN')
      })
   }
   return rows
})

const studentInfoFirstPageMeta = computed(() => {
   if (sourceType.value === 'empty') {
      const blankRows = config.table.groupMode === 'examroom' ? 42 : 50
      return { maxRows: blankRows, showSummary: false }
   }
   const total = studentInfoFirstGroupRows.value.length
   const { maxRowsMid, maxRowsLast } = studentInfoPrintLayout.value
   if (total <= maxRowsLast) return { maxRows: maxRowsLast, showSummary: true }
   return { maxRows: maxRowsMid, showSummary: false }
})

const studentInfoPrintBodyRows = computed(() => {
   const rows = studentInfoFirstGroupRows.value
   const maxRows = studentInfoFirstPageMeta.value.maxRows
   const normalized = rows.slice(0, maxRows).map((item: any) => {
      const classValue = String(item?.['班级'] ?? '').trim()
      const studentNo = String(item?.['学号'] ?? '').trim()
      const name = String(item?.['考生姓名'] ?? item?.['姓名'] ?? '').trim()
      const examNo = String(item?.['考生考号'] ?? item?.['考号'] ?? '').trim()
      const first = String(item?.['首选'] ?? item?.['类别'] ?? '').trim()
      const sub1 = String(item?.['选科1'] ?? item?.['选1'] ?? '').trim()
      const sub2 = String(item?.['选科2'] ?? item?.['选2'] ?? '').trim()
      const room = String(item?.['考场'] ?? '').trim()
      const roomNo = String(item?.['考场号'] ?? '').trim()
      const seatNo = String(item?.['座位号'] ?? item?.['座位'] ?? '').trim()
      if (config.table.includeSubjectFields) {
         return { class: classValue, studentNo, name, examNo, first, sub1, sub2, room, roomNo, seatNo }
      }
      return { class: classValue, studentNo, name, examNo, room, roomNo, seatNo }
   })

   if (sourceType.value === 'empty') {
      const blank = config.table.includeSubjectFields
         ? { class: '', studentNo: '', name: '', examNo: '', first: '', sub1: '', sub2: '', room: '', roomNo: '', seatNo: '' }
         : { class: '', studentNo: '', name: '', examNo: '', room: '', roomNo: '', seatNo: '' }
      while (normalized.length < maxRows) normalized.push({ ...blank })
   }
   return normalized
})

const studentInfoPrintSummaryRow = computed(() => {
   const colCount = studentInfoColumns.value.length
   const isExamroom = config.table.groupMode === 'examroom'
   const labelCol = isExamroom ? (config.table.includeSubjectFields ? 'room' : 'room') : 'class'

   const rawGroupKey = String(
      isExamroom ? (studentInfoFirstGroupRows.value?.[0]?.['考场号'] ?? '') : (studentInfoFirstGroupRows.value?.[0]?.['班级'] ?? '')
   ).trim()

   let label = ''
   if (isExamroom) {
      const roomName = String(studentInfoFirstGroupRows.value?.[0]?.['考场'] ?? '').trim()
      label = (roomName || rawGroupKey || '考场').trim()
   } else {
      label = rawGroupKey
   }

   const count = sourceType.value === 'empty' ? 0 : studentInfoFirstGroupRows.value.length

   const base: Record<string, string> = {}
   for (const col of studentInfoColumns.value) base[(col as any).key] = ''
   base[labelCol] = `${label} 计数`.trim()

   const keys = studentInfoColumns.value.map(c => (c as any).key)
   if (colCount >= 3) {
      const countKey = keys[2]
      base[countKey] = String(count)
   } else if (colCount >= 2) {
      const countKey = keys[1]
      base[countKey] = String(count)
   }
   return base
})

const examBagPreviewList = computed(() => {
   if (sourceType.value === 'empty') {
      return Array(9).fill(null)
   }
   const items: any[] = previewData.value.slice(0, 9).map(item => ({
      subject: item.subject || '科目',
      room: item.room || '考场',
      count: item.count || 0
   }))
   while (items.length < 9) items.push(null)
   return items
})

const examBagPrintCells = computed(() => {
   const school = String(config.examBag.schoolName ?? '').trim()
   return examBagPreviewList.value.map((it: any) => {
      if (!it) {
         if (sourceType.value !== 'empty') return ''
         const s = school || 'xxx学校'
         return `学校：${s}\n\n科目：\n\n考场：\n\n应到：\n\n实到：\n\n监考教师：\n\n考试情况：`
      }
      const subject = String(it?.subject ?? '').trim()
      const room = String(it?.room ?? '').trim()
      const count = String(it?.count ?? '').trim()
      const s = school || 'xxx学校'
      return `学校：${s}\n\n科目：${subject}\n\n考场：${room}（${count}人）\n\n应到：\n\n实到：\n\n监考教师：\n\n考试情况：`
   })
})

const examBagPreviewFooterText = computed(() => {
   const pageNum = 1
   if (sourceType.value === 'empty') return `第 ${pageNum} 页，共 1 页`
   const list = Array.isArray(previewData.value) ? previewData.value : []
   if (!list.length) return ''

   const bySubject = new Map<string, any[]>()
   const order: string[] = []
   for (const it of list) {
      const subj = String((it as any)?.subject ?? '').trim()
      const key = subj || ''
      if (!bySubject.has(key)) {
         bySubject.set(key, [])
         order.push(key)
      }
      bySubject.get(key)!.push(it)
   }

   const capacity = 9
   let totalPages = 0
   for (const subj of order) {
      const n = bySubject.get(subj)?.length || 0
      totalPages += Math.max(1, Math.ceil(n / capacity))
   }
   totalPages = Math.max(1, totalPages)
   const subject = order[0] || ''
   const base = `第 ${pageNum} 页，共 ${totalPages} 页`
   return subject ? `${base}，当前科目：${subject}` : base
})

const getCornerPreviewData = (item: Record<string, any>) => {
   const kaochang = String(item['考场'] ?? '')
   const kaochangNo = String(item['考场号'] ?? '')
   const seatNo = String(item['座位号'] ?? '')

   // 高考模式：从科目数据数组中获取第一个科目的学生信息
   let name = ''
   let examNo = ''
   let classStudent = ''

   if (item['科目数据'] && Array.isArray(item['科目数据']) && item['科目数据'].length > 0) {
      // 高考模式：使用第一个科目的数据作为预览
      const firstSubject = item['科目数据'][0]
      name = String(firstSubject['考生姓名'] ?? '')
      examNo = String(firstSubject['考生考号'] ?? '')
      classStudent = String(firstSubject['考生班级学号'] ?? '')
   } else {
      // 普通模式：直接从顶层获取
      name = String(item['考生姓名'] ?? item['姓名'] ?? '')
      examNo = String(item['考生考号'] ?? item['考号'] ?? '')
      classStudent = String(item['考生班级学号'] ?? '')

      if (!classStudent) {
         const c = String(item['班级'] ?? '')
         const n = String(item['学号'] ?? '')
         if (c || n) {
            classStudent = `${c}班${n}号`
         }
      }
   }

   return {
      考场: kaochang,
      考场号: kaochangNo,
      座位号: seatNo,
      考生姓名: name,
      考生考号: examNo,
      考生班级学号: classStudent,
      科目数据: item['科目数据']  // 保留原始的科目数据数组，供辅助函数使用
   }
}

// Helper functions for Gaokao mode compatibility
// Corner paper helpers - get student info for a specific subject
const getCornerStudentName = (item: any, subjectIndex: number): string => {
  if (!item) return ''
  // Gaokao mode: get from subject data array
  if (item.科目数据 && Array.isArray(item.科目数据)) {
    return item.科目数据[subjectIndex]?.考生姓名 || ''
  }
  // Normal mode: get directly
  return item.考生姓名 || ''
}

const getCornerStudentExamNo = (item: any, subjectIndex: number): string => {
  if (!item) return ''
  if (item.科目数据 && Array.isArray(item.科目数据)) {
    return item.科目数据[subjectIndex]?.考生考号 || ''
  }
  return item.考生考号 || ''
}

const getCornerStudentClassNo = (item: any, subjectIndex: number): string => {
  if (!item) return ''
  if (item.科目数据 && Array.isArray(item.科目数据)) {
    return item.科目数据[subjectIndex]?.考生班级学号 || ''
  }
  return item.考生班级学号 || ''
}

// Admission ticket helpers - get room info for a specific subject
const getTicketRoom = (item: any, subjectIndex: number): string => {
  if (!item) return ''
  // Gaokao mode: get from subject data array
  if (item.科目数据 && Array.isArray(item.科目数据)) {
    return item.科目数据[subjectIndex]?.考场 || ''
  }
  // Normal mode: get directly
  return item.考场 || ''
}

const getTicketRoomNo = (item: any, subjectIndex: number): string => {
  if (!item) return ''
  if (item.科目数据 && Array.isArray(item.科目数据)) {
    return item.科目数据[subjectIndex]?.考场号 || ''
  }
  return item.考场号 || ''
}

const getTicketSeatNo = (item: any, subjectIndex: number): string => {
  if (!item) return ''
  if (item.科目数据 && Array.isArray(item.科目数据)) {
    return item.科目数据[subjectIndex]?.座位号 || ''
  }
  return item.座位号 || ''
}

const cornerPreview = computed(() => {
   const fallback = {
      考场: '',
      考场号: '',
      座位号: '',
      考生姓名: '',
      考生考号: '',
      考生班级学号: '',
   }
   if (sourceType.value === 'empty') return fallback
   const first = displayData.value[0]
   if (!first) return fallback
   return getCornerPreviewData(first)
})

const cornerSubjectRowsForStyle = computed(() => {
   if (sourceType.value === 'empty') {
      const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
      return Array.from({ length: count }, () => '')
   }

   // 高考模式：从第一条数据的科目数据数组中获取科目名称
   const first = displayData.value[0]
   if (first && first['科目数据'] && Array.isArray(first['科目数据'])) {
      return first['科目数据'].map((subj: any) => String(subj['科目'] ?? '').trim())
   }

   // 普通模式：从 subjectRows 获取
   const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
   return Array.from({ length: count }, (_, i) => {
      return String(subjectRows.value[i]?.name ?? '').trim()
   })
})

const cornerSubjectRows = computed(() => {
   if (sourceType.value === 'empty') {
      const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
      return Array.from({ length: count }, () => '')
   }

   // 高考模式：从第一条数据的科目数据数组中获取科目名称
   const first = displayData.value[0]
   if (first && first['科目数据'] && Array.isArray(first['科目数据'])) {
      return first['科目数据'].map((subj: any) => String(subj['科目'] ?? '').trim())
   }

   // 普通模式：从 subjectRows 获取
   const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
   return Array.from({ length: count }, (_, i) => {
      const v = String(subjectRows.value[i]?.name ?? '').trim()
      return v
   })
})

const cornerTemplatesPerCol = computed(() => {
   const subjectCount = cornerSubjectRows.value.length
   if (subjectCount <= 3) return 5
   if (subjectCount <= 5) return 4
   if (subjectCount <= 9) return 3
   return 2
})

const itemsPerPage = computed(() => {
   if (activeTab.value === 'corner') {
      return cornerTemplatesPerCol.value * 3
   }
   if (activeTab.value === 'ticket') {
      // Assuming same layout logic for ticket for now, or use fixed
      // Ticket usually has similar height constraints
      // Based on backend AdmissionTicketPDFGenerator, it also uses 3 cols.
      // Rows might differ, but let's reuse logic or default to 3 rows
       const subjectCount = subjectRows.value.length
       if (subjectCount <= 3) return 15 // 5 rows
       if (subjectCount <= 5) return 12 // 4 rows
       if (subjectCount <= 9) return 9 // 3 rows
       return 6 // 2 rows
   }
   return 10
})

const previewTotalPages = computed(() => {
   if (activeTab.value !== 'corner' && activeTab.value !== 'ticket') return 0
   if (sourceType.value === 'empty') return 0
   const total = previewTotal.value > 0 ? previewTotal.value : previewData.value.length
   if (!total) return 0
   return Math.max(1, Math.ceil(total / itemsPerPage.value))
})

const printPreviewList = computed(() => {
   if (sourceType.value === 'empty') {
      if (activeTab.value === 'corner') {
         const blank = {
            考场: '',
            考场号: '',
            座位号: '',
            考生姓名: '',
            考生考号: '',
            考生班级学号: '',
         }
         return Array.from({ length: itemsPerPage.value }, () => ({ ...blank }))
      }
      if (activeTab.value === 'ticket') {
         const blank = {
            考场: '',
            考场号: '',
            座位号: '',
            考生姓名: '',
            考生考号: '',
            班级: '',
            学号: '',
         }
         return Array.from({ length: itemsPerPage.value }, () => ({ ...blank }))
      }
   }
   const list = displayData.value.slice(0, itemsPerPage.value)
   if (activeTab.value === 'corner') {
      return list.map(item => getCornerPreviewData(item))
   }
   if (activeTab.value === 'ticket') {
      return list.map(item => getTicketPreviewData(item))
   }
   return []
})

const getTicketPreviewData = (item: Record<string, any>) => {
   const name = String(item['考生姓名'] ?? item['姓名'] ?? '')
   const examNo = String(item['考生考号'] ?? item['考号'] ?? '')
   const cls = String(item['班级'] ?? '')
   const studentNo = String(item['学号'] ?? '')

   // 高考模式：从科目数据数组中获取第一个科目的考场信息
   let kaochang = ''
   let kaochangNo = ''
   let seatNo = ''

   if (item['科目数据'] && Array.isArray(item['科目数据']) && item['科目数据'].length > 0) {
      // 高考模式：使用第一个科目的考场数据作为预览
      const firstSubject = item['科目数据'][0]
      kaochang = String(firstSubject['考场'] ?? '')
      kaochangNo = String(firstSubject['考场号'] ?? '')
      seatNo = String(firstSubject['座位号'] ?? '')
   } else {
      // 普通模式：直接从顶层获取
      kaochang = String(item['考场'] ?? '')
      kaochangNo = String(item['考场号'] ?? '')
      seatNo = String(item['座位号'] ?? '')
   }

   return {
      考场: kaochang,
      考场号: kaochangNo,
      座位号: seatNo,
      考生姓名: name,
      考生考号: examNo,
      班级: cls,
      学号: studentNo,
      科目数据: item['科目数据']  // 保留原始的科目数据数组，供辅助函数使用
   }
}

const ticketPreview = computed(() => {
   const fallback = {
      考场: '',
      考场号: '',
      座位号: '',
      考生姓名: '',
      考生考号: '',
      班级: '',
      学号: '',
   }
   if (sourceType.value === 'empty') return fallback
   const first = displayData.value[0]
   if (!first) return fallback
   return getTicketPreviewData(first)
})

const ticketSubjectRows = computed(() => {
   if (sourceType.value === 'empty') {
      const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
      return Array.from({ length: count }, () => ({ name: '', time: '' }))
   }

   // 高考模式：从第一条数据的科目数据数组中获取科目名称和时间
   const first = displayData.value[0]
   if (first && first['科目数据'] && Array.isArray(first['科目数据'])) {
      return first['科目数据'].map((subj: any) => ({
         name: String(subj['科目'] ?? '').trim(),
         time: String(subj['时间'] ?? '').trim()
      }))
   }

   // 普通模式：从 subjectRows 获取
   const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
   return Array.from({ length: count }, (_, i) => {
      const name = String(subjectRows.value[i]?.name ?? '').trim()
      const time = String(subjectRows.value[i]?.time ?? '').trim()
      return { name, time }
   })
})

const ticketSubjectRowsForPrint = computed(() => {
   if (previewMode.value === 'print' && sourceType.value === 'empty') {
      const count = Math.min(20, Math.max(1, subjectRows.value.length || 9))
      return Array.from({ length: count }, () => ({ name: '', time: '' }))
   }
   return ticketSubjectRows.value
})

const previewBadgeText = computed(() => {
   if (activeTab.value !== 'corner' && activeTab.value !== 'ticket') return ''
   if (previewMode.value === 'style') {
      if (sourceType.value === 'empty') return '预览：样式参考'
      if (previewTotal.value > 0) return `预览：第 1 条考生 / 共 ${previewTotal.value} 条`
      if (previewData.value.length > 0) return '预览：第 1 条考生'
      return '预览：未加载数据'
   }
   if (previewMode.value === 'print') {
      if (sourceType.value === 'empty') return ''
      const pages = previewTotalPages.value
      if (pages > 0) return `预览：第 1 页/共 ${pages} 页`
      return '预览：未加载数据'
   }
   return ''
})

const previewPrintFooterText = computed(() => {
   if (previewMode.value !== 'print') return ''
   if (activeTab.value !== 'corner' && activeTab.value !== 'ticket') return ''
   const pageNum = 1
   const totalPages = sourceType.value === 'empty' ? 1 : (previewTotalPages.value || 1)
   const first = printPreviewList.value?.[0] as any
   const base = `第 ${pageNum} 页，共 ${totalPages} 页`
   if (activeTab.value === 'corner') {
      const room = String(first?.['考场'] ?? '').trim()
      return room ? `${base}，当前考场：${room}` : base
   }
   const raw = String(first?.['班级'] ?? '').trim()
   const cls = raw && /^\d+$/.test(raw) ? `${raw}班` : raw
   return cls ? `${base}，当前班级：${cls}` : base
})

const deskLayoutOptions = [
   { name: '5行×6列', rows: 5, cols: 6 },
   { name: '6行×5列', rows: 6, cols: 5 },
   { name: '6行×7列', rows: 6, cols: 7 },
   { name: '7行×6列', rows: 7, cols: 6 },
   { name: '5行×9列', rows: 5, cols: 9 },
   { name: '9行×5列', rows: 9, cols: 5 },
]

function parseCustomCounts(text: string): number[] | null {
   const raw = String(text || '').trim().replace(/，/g, ',')
   if (!raw) return null
   const parts = raw.split(',').map(s => s.trim()).filter(Boolean)
   const nums = parts.map(p => parseInt(p, 10)).filter(n => Number.isFinite(n) && n > 0)
   if (!nums.length) return null
   return nums
}

function getSeatMapping(
   rows: number,
   cols: number,
   pattern: string,
   startPos: 'left' | 'right',
   customColCounts: number[] | null
): Record<number, [number, number]> {
   const mapping: Record<number, [number, number]> = {}
   let currentSeat = 0

   const safeRows = Math.max(1, Math.floor(rows || 0))
   const safeCols = Math.max(1, Math.floor(cols || 0))
   const custom = Array.isArray(customColCounts) && customColCounts.length ? customColCounts : null

   const isValidPos = (r: number, actualC: number) => {
      if (!custom) return true
      if (actualC < 0 || actualC >= custom.length) return false
      return r < custom[actualC]
   }

   const getActualCol = (logicCol: number) => {
      if (startPos === 'left') return safeCols - 1 - logicCol
      return logicCol
   }

   if (pattern === 'Z型横排') {
      for (let r = 0; r < safeRows; r++) {
         for (let c = 0; c < safeCols; c++) {
            const actualC = getActualCol(c)
            if (isValidPos(r, actualC)) mapping[currentSeat++] = [r, actualC]
         }
      }
   } else if (pattern === 'S型横排') {
      for (let r = 0; r < safeRows; r++) {
         const even = r % 2 === 0
         if (even) {
            for (let c = 0; c < safeCols; c++) {
               const actualC = getActualCol(c)
               if (isValidPos(r, actualC)) mapping[currentSeat++] = [r, actualC]
            }
         } else {
            for (let c = safeCols - 1; c >= 0; c--) {
               const actualC = getActualCol(c)
               if (isValidPos(r, actualC)) mapping[currentSeat++] = [r, actualC]
            }
         }
      }
   } else if (pattern === 'Z型竖排') {
      for (let c = 0; c < safeCols; c++) {
         const actualC = getActualCol(c)
         for (let r = 0; r < safeRows; r++) {
            if (isValidPos(r, actualC)) mapping[currentSeat++] = [r, actualC]
         }
      }
   } else if (pattern === 'S型竖排') {
      for (let c = 0; c < safeCols; c++) {
         const even = c % 2 === 0
         const actualC = getActualCol(c)
         if (even) {
            for (let r = 0; r < safeRows; r++) {
               if (isValidPos(r, actualC)) mapping[currentSeat++] = [r, actualC]
            }
         } else {
            for (let r = safeRows - 1; r >= 0; r--) {
               if (isValidPos(r, actualC)) mapping[currentSeat++] = [r, actualC]
            }
         }
      }
   }

   return mapping
}

const firstRoomData = computed(() => {
   const list = displayData.value || []
   if (!Array.isArray(list) || list.length === 0) return []
   const first = list[0] || {}
   const key = (first as any)['考场号'] ?? (first as any)['考场']
   if (key === undefined || key === null) return list
   return list.filter((item: any) => {
      const k = item?.['考场号'] ?? item?.['考场']
      return String(k ?? '') === String(key)
   })
})

const deskEffectiveLayout = computed(() => {
   const custom = config.desk.customColCounts
   if (Array.isArray(custom) && custom.length) {
      const cols = custom.length
      const rows = Math.max(...custom.map(n => Math.max(0, n)))
      const capacity = custom.reduce((acc, n) => acc + Math.max(0, n || 0), 0)
      return { layoutName: '自定义', rows: Math.max(1, rows), cols: Math.max(1, cols), capacity: Math.max(1, capacity), customColCounts: custom }
   }
   const rows = Math.max(1, Math.floor(config.desk.layoutRows || 0))
   const cols = Math.max(1, Math.floor(config.desk.layoutCols || 0))
   return { layoutName: config.desk.layoutName || `${rows}行×${cols}列`, rows, cols, capacity: rows * cols, customColCounts: null as number[] | null }
})

const deskSeatGrid = computed(() => {
   const { rows, cols, capacity, customColCounts } = deskEffectiveLayout.value
   const grid: { valid: boolean; student: any | null }[][] = Array.from({ length: rows }, () =>
      Array.from({ length: cols }, () => ({ valid: true, student: null }))
   )

   const custom = customColCounts
   if (custom) {
      for (let r = 0; r < rows; r++) {
         for (let c = 0; c < cols; c++) {
            grid[r][c].valid = r < (custom[c] || 0)
         }
      }
   }

   if (!hasPreviewData.value) return grid
   const mapping = getSeatMapping(rows, cols, config.desk.layoutPattern, config.desk.startPos as any, customColCounts)
   const students = firstRoomData.value.slice(0, capacity)
   for (let i = 0; i < students.length; i++) {
      const pos = mapping[i]
      if (!pos) continue
      const [r, c] = pos
      if (r >= 0 && r < rows && c >= 0 && c < cols && grid[r][c].valid) {
         grid[r][c].student = students[i]
      }
   }
   return grid
})

const deskSeatNumberGrid = computed(() => {
   const { rows, cols, customColCounts } = deskEffectiveLayout.value
   const grid: { valid: boolean; seatNo: number | null }[][] = Array.from({ length: rows }, () =>
      Array.from({ length: cols }, () => ({ valid: true, seatNo: null }))
   )

   const custom = customColCounts
   if (custom) {
      for (let r = 0; r < rows; r++) {
         for (let c = 0; c < cols; c++) {
            grid[r][c].valid = r < (custom[c] || 0)
         }
      }
   }

   const mapping = getSeatMapping(rows, cols, config.desk.layoutPattern, config.desk.startPos as any, customColCounts)
   const capacity = Object.keys(mapping).length
   for (let i = 0; i < capacity; i++) {
      const pos = mapping[i]
      if (!pos) continue
      const [r, c] = pos
      if (r >= 0 && r < rows && c >= 0 && c < cols && grid[r][c].valid) {
         grid[r][c].seatNo = i + 1
      }
   }
   return grid
})

const deskPrintGrid = computed(() => {
   const { rows, cols, capacity, customColCounts } = deskEffectiveLayout.value
   const grid: { valid: boolean; student: any | null }[][] = Array.from({ length: rows }, () =>
      Array.from({ length: cols }, () => ({ valid: true, student: null }))
   )

   const custom = customColCounts
   if (custom) {
      for (let r = 0; r < rows; r++) {
         for (let c = 0; c < cols; c++) {
            grid[r][c].valid = r < (custom[c] || 0)
         }
      }
   }

   if (!hasPreviewData.value || sourceType.value === 'empty') return grid
   const mapping = getSeatMapping(rows, cols, config.desk.layoutPattern, 'right', customColCounts)
   const students = firstRoomData.value.slice(0, capacity)
   for (let i = 0; i < students.length; i++) {
      const pos = mapping[i]
      if (!pos) continue
      const [r, c] = pos
      if (r >= 0 && r < rows && c >= 0 && c < cols && grid[r][c].valid) {
         grid[r][c].student = students[i]
      }
   }
   return grid
})

function deskPrintCellText(r: number, c: number) {
   const cell = deskPrintGrid.value?.[r]?.[c]
   if (!cell || !cell.valid) return ''
   const s = cell.student || {}
   const name = String(s?.['考生姓名'] ?? s?.['姓名'] ?? '')
   const no = String(s?.['考生考号'] ?? s?.['考号'] ?? '')
   const room = String(s?.['考场'] ?? '')
   const roomNo = String(s?.['考场号'] ?? '')
   const seat = String(s?.['座位号'] ?? '')
   return `姓名：${name}\n考号：${no}\n考场：${room}\n考场号：${roomNo}\n座位号：${seat}`
}

const deskLayoutSummary = computed(() => {
   const layoutName = String(config.desk.layoutName || deskEffectiveLayout.value.layoutName)
   const { rows, cols } = deskEffectiveLayout.value
   const pattern = String(config.desk.layoutPattern || '')
   const startPos = config.desk.startPos === 'right' ? '右手位' : '左手位'
   const layoutText = layoutName === '自定义' ? `${rows}行×${cols}列` : layoutName
   return `${layoutText} · ${pattern} · ${startPos}`
})

const previewPageSizeMm = computed(() => {
   if (activeTab.value === 'desk' && deskPreviewMode.value === 'print') {
      return { width: '210mm', height: '297mm' }
   }
   if (activeTab.value === 'table') {
      return { width: '210mm', height: '297mm' }
   }
   if (activeTab.value === 'exam_bag_label') {
      return { width: '210mm', height: '297mm' }
   }
   // Default to A4 Landscape for all other views (including desk seat layout)
   return { width: '297mm', height: '210mm' }
})

const previewTargetPx = computed(() => {
   if (activeTab.value === 'desk' && deskPreviewMode.value === 'print') return { w: 794, h: 1122 }
   if (activeTab.value === 'table') return { w: 794, h: 1122 }
   if (activeTab.value === 'exam_bag_label') return { w: 794, h: 1122 }
   return { w: 1122, h: 794 }
})

const showDeskLayoutDialog = ref(false)
const deskLayoutDraft = reactive({
   layoutName: '7行×6列',
   layoutRows: 7,
   layoutCols: 6,
   layoutPattern: 'S型竖排',
   startPos: 'left' as 'left' | 'right',
   customCountsText: '',
})

function openDeskLayoutDialog() {
   deskLayoutDraft.layoutName = String(config.desk.layoutName || '7行×6列')
   deskLayoutDraft.layoutRows = Number(config.desk.layoutRows || 7)
   deskLayoutDraft.layoutCols = Number(config.desk.layoutCols || 6)
   deskLayoutDraft.layoutPattern = String(config.desk.layoutPattern || 'S型竖排')
   deskLayoutDraft.startPos = (config.desk.startPos === 'right' ? 'right' : 'left') as any
   if (Array.isArray(config.desk.customColCounts) && config.desk.customColCounts.length) {
      deskLayoutDraft.layoutName = '自定义'
      deskLayoutDraft.customCountsText = config.desk.customColCounts.join(',')
      deskLayoutDraft.layoutRows = deskEffectiveLayout.value.rows
      deskLayoutDraft.layoutCols = deskEffectiveLayout.value.cols
   } else {
      deskLayoutDraft.customCountsText = ''
   }
   showDeskLayoutDialog.value = true
}

watch(
   () => deskLayoutDraft.layoutName,
   (name) => {
      if (name === '自定义') return
      const opt = deskLayoutOptions.find(o => o.name === name)
      if (!opt) return
      deskLayoutDraft.layoutRows = opt.rows
      deskLayoutDraft.layoutCols = opt.cols
      deskLayoutDraft.customCountsText = ''
   }
)

watch(
   () => deskLayoutDraft.customCountsText,
   (text) => {
      if (deskLayoutDraft.layoutName !== '自定义') return
      const nums = parseCustomCounts(text)
      if (!nums) return
      deskLayoutDraft.layoutCols = nums.length
      deskLayoutDraft.layoutRows = Math.max(1, Math.max(...nums))
   }
)

async function applyDeskLayoutDraft() {
   if (deskLayoutDraft.layoutName === '自定义') {
      const nums = parseCustomCounts(deskLayoutDraft.customCountsText)
      if (!nums) {
         ElMessage.warning('请输入有效的自定义每列人数')
         return
      }
      config.desk.layoutName = '自定义'
      config.desk.customColCounts = nums
      config.desk.layoutCols = nums.length
      config.desk.layoutRows = Math.max(1, Math.max(...nums))
   } else {
      const opt = deskLayoutOptions.find(o => o.name === deskLayoutDraft.layoutName)
      if (opt) {
         config.desk.layoutName = opt.name
         config.desk.layoutRows = opt.rows
         config.desk.layoutCols = opt.cols
      } else {
         config.desk.layoutName = String(deskLayoutDraft.layoutName || '')
      }
      config.desk.customColCounts = null
   }
   config.desk.layoutPattern = deskLayoutDraft.layoutPattern
   config.desk.startPos = deskLayoutDraft.startPos
   showDeskLayoutDialog.value = false
   await nextTick()
   _measurePreviewBaseSize()
   handleAutoFit()
}

// --- Methods ---

const handleSelectFile = async () => {
   const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }] })
   if (path) {
      sourceType.value = 'file'
      dataPath.value = path as string
      if (activeTab.value === 'exam_bag_label') {
         headers.value = []
         for (const key in mapping) delete mapping[key]
         showMappingDialog.value = false
         try {
            const res = await pythonBackend.request<any>('printing.previewData', {
               path,
               mapping: {},
               type: activeTab.value,
            })
            if (res.data) {
               previewData.value = res.data
               previewTotal.value = res.total
            } else if (res.error) {
               ElMessage.error(res.error)
            }
         } catch (e) {
            ElMessage.error('加载预览失败: ' + e)
         }
      } else {
         try {
            const res = await pythonBackend.request<any>('printing.readHeaders', { path })
            if (res.headers) {
               headers.value = res.headers
               if (filePreviewCache.dataPath === String(path) && Object.keys(filePreviewCache.mapping).length) {
                  _applyMappingSnapshot(filePreviewCache.mapping)
                  if (isMappingComplete()) {
                     showMappingDialog.value = false
                     loadPreview()
                  } else {
                     showMappingDialog.value = true
                  }
               } else {
                  autoMapFields()
                  showMappingDialog.value = true
               }
            } else if (res.error) {
               ElMessage.error(res.error)
            }
         } catch (e) {
            ElMessage.error('读取文件失败: ' + e)
         }
      }
   }
}

const openMappingDialog = () => {
   if (!dataPath.value) return
   showMappingDialog.value = true
}

const autoMapFields = () => {
   // Reset
   for (const key in mapping) delete mapping[key]
   
   // Simple heuristic
   for (const key in requiredFields) {
      if (headers.value.includes(key)) {
         mapping[key] = key
      } else {
         // Try partial match
         const match = headers.value.find(h => h.includes(key) || key.includes(h))
         if (match) mapping[key] = match
      }
   }
}

const handleConfirmMapping = async () => {
   // Validate required
   for (const [key, field] of Object.entries(requiredFields)) {
      if (field.required && !mapping[key]) {
         ElMessage.warning(`请映射必填字段: ${field.label}`)
         return
      }
   }
   
   showMappingDialog.value = false
   sourceType.value = 'file'
   loadPreview()
}

const isMappingComplete = () => {
   for (const [key, field] of Object.entries(requiredFields)) {
      if (field.required && !mapping[key]) return false
   }
   return true
}

const loadPreview = async () => {
   if (!dataPath.value) return
   try {
      const res = await pythonBackend.request<any>('printing.previewData', { 
         path: dataPath.value,
         mapping: mapping,
         type: activeTab.value
      })
      if (res.data) {
         previewData.value = res.data
         previewTotal.value = res.total
         if (sourceType.value === 'file') _cacheCurrentFileState()
      } else if (res.error) {
         ElMessage.error(res.error)
      }
   } catch (e) {
      ElMessage.error('加载预览失败: ' + e)
   }
}

const handleLoadFromSchedule = async () => {
    loadingSchedule.value = true
    try {
        // 获取考场编排配置信息
        const roomsState = await pythonBackend.request<any>('rooms.getState', {})
        if (roomsState && roomsState.config) {
            // 保存编排模式
            const mode = roomsState.config.mode || ''
            scheduleArrangementMode.value = mode === 'gaokao' ? 'gaokao_mode' : ''
        }

        const res = await pythonBackend.request<any>('printing.loadFromSchedule', { type: activeTab.value })
        if (res.data) {
            previewData.value = res.data
            previewTotal.value = res.total
            _cacheCurrentScheduleState()
            ElMessage.success(`成功加载 ${res.total} 条考场编排数据`)
        } else if (res.error) {
            previewData.value = []
            previewTotal.value = 0
            schedulePreviewCache.data = []
            schedulePreviewCache.total = 0
            const msg = String(res.error || '')
            if (msg.includes('暂无考场编排数据')) {
               ElMessage.warning(msg)
            } else {
               ElMessage.error(msg)
            }
        }
    } catch (e) {
        previewData.value = []
        previewTotal.value = 0
        schedulePreviewCache.data = []
        schedulePreviewCache.total = 0
        ElMessage.error('加载考场数据失败: ' + e)
    } finally {
        loadingSchedule.value = false
    }
}

const handleGenerate = async () => {
   if (sourceType.value === 'file' && (!dataPath.value || previewData.value.length === 0)) {
      return ElMessage.warning('请先加载数据')
   }
   if (sourceType.value === 'schedule' && previewData.value.length === 0) {
      return ElMessage.warning('请先加载考场编排数据')
   }
   if (activeTab.value !== 'exam_bag_label' && sourceType.value === 'file' && !isMappingComplete()) {
      showMappingDialog.value = true
      return ElMessage.warning('请先完成字段映射')
   }
   if (activeTab.value === 'table' && sourceType.value === 'file' && config.table.includeSubjectFields) {
      const missing = ['首选', '选科1', '选科2'].filter(k => !mapping[k])
      if (missing.length) {
         try {
            await ElMessageBox.confirm(
               `已勾选"包含选科列"，但未映射字段：${missing.join('、')}。\n继续生成将导致这些列为空。\n是否继续？`,
               '字段映射提示',
               { type: 'warning', confirmButtonText: '继续生成', cancelButtonText: '取消', closeOnClickModal: false }
            )
         } catch {
            return
         }
      }
   }
   
   const exportXlsx = Boolean(commonConfig.exportXlsx)
   const exportPdf = Boolean(commonConfig.exportPdf)
   if (!exportXlsx && !exportPdf) {
      return ElMessage.warning('请至少选择一种输出格式（Excel 或 PDF）')
   }

   const defaultExt = exportPdf && !exportXlsx ? 'pdf' : 'xlsx'
   let tabName = tabs.find(t => t.id === activeTab.value)?.name || '生成结果'
   if (activeTab.value === 'table') {
      const mode = String(config.table.groupMode || 'class')
      tabName = mode === 'examroom' ? '考生信息表（考场）' : '考生信息表（班级）'
   }
   await saveAndRun({
      dialog: {
         defaultPath: `${tabName}_批量生成.${defaultExt}`,
         filters: [
            ...(exportXlsx ? [{ name: 'Excel', extensions: ['xlsx'] }] : []),
            ...(exportPdf ? [{ name: 'PDF', extensions: ['pdf'] }] : []),
         ]
      },
      run: async (outputPath) => {
         generating.value = true
         try {
            let specificConfig: any = {}
            if (activeTab.value === 'corner') {
               // 高考模式下使用固定的8个科目（物理历史合并）
               const subjects = isGaokaoMode.value
                  ? ['语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物']
                  : subjectRows.value.map(r => r.name)
               specificConfig = {
                  title: config.corner.title,
                  subjects
               }
            } else if (activeTab.value === 'desk') {
               specificConfig = {
                  ...config.desk,
                  layoutRows: deskEffectiveLayout.value.rows,
                  layoutCols: deskEffectiveLayout.value.cols,
               }
            } else if (activeTab.value === 'ticket') {
               // 高考模式下使用固定的8个科目（物理历史合并）
               const subjects = isGaokaoMode.value
                  ? ['语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物']
                  : subjectRows.value.map(r => r.name)
               const subjectTimes = isGaokaoMode.value
                  ? ['', '', '', '', '', '', '', ''] // 高考模式时间在数据中已包含
                  : subjectRows.value.map(r => r.time)
               specificConfig = {
                  title: config.ticket.title,
                  subjects,
                  subjectTimes
               }
            } else if (activeTab.value === 'table') {
               specificConfig = config.table
            } else if (activeTab.value === 'exam_bag_label') {
               specificConfig = config.examBag
            }

            const configPayload = {
               ...commonConfig,
               ...specificConfig,
               totalCount: totalCount.value,
               numTemplates: totalCount.value
            }

            const confirmFlags: Record<string, boolean> = {}
            let result: any = await pythonBackend.request('printing.generate', {
               type: activeTab.value,
               sourceType: sourceType.value,
               dataPath: dataPath.value,
               mapping: mapping,
               outputPath,
               config: configPayload,
               confirmFlags
            })

            while (true) {
               if (result?.error) throw String(result.error)
               if (!result?.confirm) break

               const c = result.confirm
               try {
                  await ElMessageBox.confirm(String(c.message || ''), String(c.title || '提示'), {
                     type: c.level === 'warning' ? 'warning' : c.level === 'question' ? 'warning' : 'info',
                     confirmButtonText: '继续生成',
                     cancelButtonText: '取消',
                     closeOnClickModal: false,
                  })
               } catch {
                  return { cancelled: true }
               }

               if (c.code === 'deskSort' || c.title === '排序警告') confirmFlags.deskSort = true
               if (c.code === 'deskOverflow' || c.title === '人数超限提示') confirmFlags.deskOverflow = true

               result = await pythonBackend.request('printing.generate', {
                  type: activeTab.value,
                  sourceType: sourceType.value,
                  dataPath: dataPath.value,
                  mapping: mapping,
                  outputPath,
                  config: configPayload,
                  confirmFlags
               })
            }

            const paths = result?.paths
            if (Array.isArray(paths) && paths.length > 1) {
               ElMessage.success(`生成成功：${paths.length} 个文件`)
            } else {
               ElMessage.success('生成成功!')
            }

            return result
         } finally {
            generating.value = false
         }
      },
      errorText: '生成失败',
      openFolderTitle: '生成成功',
      isCancelled: (result) => Boolean((result as any)?.cancelled),
      revealPath: (result, selectedPath) => {
         const paths = (result as any)?.paths
         if (Array.isArray(paths) && paths.length) return String(paths[0])
         return selectedPath
      },
   })
}

// Auto load schedule if mode selected
watch(sourceType, (val, oldVal) => {
   if (oldVal === 'file') _cacheCurrentFileState()
   if (oldVal === 'schedule') _cacheCurrentScheduleState()

   if (val === 'schedule') {
      previewData.value = []
      previewTotal.value = 0
      handleLoadFromSchedule()
      return
   }

   if (val === 'file') {
      if (filePreviewCache.dataPath) {
         dataPath.value = filePreviewCache.dataPath
         headers.value = filePreviewCache.headers.slice()
         _applyMappingSnapshot(filePreviewCache.mapping)
         previewData.value = filePreviewCache.data.slice()
         previewTotal.value = filePreviewCache.total
      } else {
         previewData.value = []
         previewTotal.value = 0
      }
      return
   }

   previewData.value = []
   previewTotal.value = 0
})

watch(subjectRows, async () => {
   await nextTick()
   _measurePreviewBaseSize()
   _updatePreviewScale()
}, { deep: true })

onBeforeUnmount(() => {
   if (previewResizeObserver) previewResizeObserver.disconnect()
   previewResizeObserver = null
})

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
  font-family: SimSun, "宋体", serif;
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
  font-family: SimSun, "宋体", serif;
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
  font-family: SimSun, "宋体", serif;
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
</style>

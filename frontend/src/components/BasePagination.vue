<template>
  <div class="h-12 bg-white border-t border-slate-200 flex items-center justify-between px-4 z-20 shrink-0">
    <span class="text-xs text-slate-400">共 {{ total }} 条记录</span>
    <el-pagination
      v-model:current-page="currentPageModel"
      v-model:page-size="pageSizeModel"
      :page-sizes="pageSizes"
      :pager-count="pagerCount"
      :layout="layout"
      :background="background"
      :small="small"
      :total="total"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, required: true },
  currentPage: { type: Number, required: true },
  pageSize: { type: Number, required: true },
  pageSizes: { 
    type: Array as () => number[], 
    default: () => [20, 50, 100, 200] 
  },
  pagerCount: { type: Number, default: 5 },
  layout: { 
    type: String, 
    default: 'prev, pager, next, sizes' 
  },
  background: { type: Boolean, default: true },
  small: { type: Boolean, default: true }
})

const emit = defineEmits(['update:currentPage', 'update:pageSize', 'change'])

const currentPageModel = computed({
  get: () => props.currentPage,
  set: (val) => emit('update:currentPage', val)
})

const pageSizeModel = computed({
  get: () => props.pageSize,
  set: (val) => emit('update:pageSize', val)
})

const handleSizeChange = (val: number) => {
  emit('change', { page: currentPageModel.value, size: val })
}

const handleCurrentChange = (val: number) => {
  emit('change', { page: val, size: pageSizeModel.value })
}
</script>

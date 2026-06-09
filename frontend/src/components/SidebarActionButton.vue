<template>
  <el-tooltip
    v-if="tooltip"
    :content="tooltip"
    placement="right"
    :show-after="300"
  >
    <button
      type="button"
      class="group flex min-h-10 w-full items-center justify-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-2 transition-[border-color,box-shadow] duration-200"
      :class="[palette.button, active ? palette.active : '', disabled ? disabledClasses : '']"
      :disabled="disabled"
      @click="handleClick"
    >
      <span class="inline-flex items-center justify-center gap-1">
        <el-icon
          v-if="icon"
          class="shrink-0 text-sm leading-none transition-colors duration-200"
          :class="active ? palette.iconActive : palette.iconIdle"
        >
          <component :is="icon" />
        </el-icon>
        <span
          class="whitespace-nowrap text-xs leading-none font-medium transition-colors duration-200"
          :class="active ? palette.textActive : palette.textIdle"
        >
          {{ label }}
        </span>
        <span
          v-if="active && clearable"
          class="flex h-4 w-4 items-center justify-center rounded transition-colors duration-200"
          :class="palette.clear"
          @click.stop.prevent="handleClear"
        >
          <el-icon :size="10"><Close /></el-icon>
        </span>
        <slot name="suffix" />
      </span>
    </button>
  </el-tooltip>
  <button
    v-else
    type="button"
    class="group flex min-h-10 w-full items-center justify-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-2 transition-[border-color,box-shadow] duration-200"
    :class="[palette.button, active ? palette.active : '', disabled ? disabledClasses : '']"
    :disabled="disabled"
    @click="handleClick"
  >
    <span class="inline-flex items-center justify-center gap-1">
      <el-icon
        v-if="icon"
        class="shrink-0 text-sm leading-none transition-colors duration-200"
        :class="active ? palette.iconActive : palette.iconIdle"
      >
        <component :is="icon" />
      </el-icon>
      <span
        class="whitespace-nowrap text-xs leading-none font-medium transition-colors duration-200"
        :class="active ? palette.textActive : palette.textIdle"
      >
        {{ label }}
      </span>
      <span
        v-if="active && clearable"
        class="flex h-4 w-4 items-center justify-center rounded transition-colors duration-200"
        :class="palette.clear"
        @click.stop.prevent="handleClear"
      >
        <el-icon :size="10"><Close /></el-icon>
      </span>
      <slot name="suffix" />
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import { Close } from '@element-plus/icons-vue'

type Tone = 'sky' | 'blue' | 'indigo' | 'emerald'

const props = withDefaults(defineProps<{
  label: string
  icon?: Component | null
  tone?: Tone
  active?: boolean
  clearable?: boolean
  disabled?: boolean
  tooltip?: string
}>(), {
  icon: null,
  tone: 'sky',
  active: false,
  clearable: false,
  disabled: false,
  tooltip: '',
})

const emit = defineEmits<{
  click: []
  clear: []
}>()

const disabledClasses = 'cursor-not-allowed opacity-50 hover:border-slate-200 hover:shadow-none'

const toneMap: Record<Tone, Record<string, string>> = {
  sky: {
    button: 'hover:border-sky-400 hover:shadow-md hover:shadow-sky-50',
    active: '!border-sky-500 bg-sky-50/50',
    iconIdle: 'text-slate-400 group-hover:text-sky-500',
    iconActive: 'text-sky-600',
    textIdle: 'text-slate-600 group-hover:text-sky-700',
    textActive: 'font-semibold text-sky-700',
    clear: 'text-sky-600 hover:bg-sky-100',
  },
  blue: {
    button: 'hover:border-blue-400 hover:shadow-md hover:shadow-blue-50',
    active: '!border-blue-500 bg-blue-50/50',
    iconIdle: 'text-slate-400 group-hover:text-blue-500',
    iconActive: 'text-blue-600',
    textIdle: 'text-slate-600 group-hover:text-blue-700',
    textActive: 'font-semibold text-blue-700',
    clear: 'text-blue-600 hover:bg-blue-100',
  },
  indigo: {
    button: 'hover:border-indigo-400 hover:shadow-md hover:shadow-indigo-50',
    active: '!border-indigo-500 bg-indigo-50/50',
    iconIdle: 'text-slate-400 group-hover:text-indigo-500',
    iconActive: 'text-indigo-600',
    textIdle: 'text-slate-600 group-hover:text-indigo-700',
    textActive: 'font-semibold text-indigo-700',
    clear: 'text-indigo-600 hover:bg-indigo-100',
  },
  emerald: {
    button: 'hover:border-emerald-400 hover:shadow-md hover:shadow-emerald-50',
    active: '!border-emerald-500 bg-emerald-50/50',
    iconIdle: 'text-slate-400 group-hover:text-emerald-500',
    iconActive: 'text-emerald-600',
    textIdle: 'text-slate-600 group-hover:text-emerald-700',
    textActive: 'font-semibold text-emerald-700',
    clear: 'text-emerald-600 hover:bg-emerald-100',
  },
}

const palette = computed(() => toneMap[props.tone])

const handleClick = () => {
  if (!props.disabled) emit('click')
}

const handleClear = () => {
  if (!props.disabled) emit('clear')
}
</script>

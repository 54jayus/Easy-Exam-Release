<template>
  <div class="h-screen w-screen bg-transparent flex flex-col overflow-hidden">
    <AiAssistant 
      mode="standalone" 
      :initial-open="true"
    />
  </div>
</template>

<script setup lang="ts">
import AiAssistant from '@/components/AiAssistant.vue'
</script>

<style>
/* Ensure body is transparent for electron window */
html, body, #app {
  background: transparent !important;
  height: 100%;
  overflow: hidden;
}
</style>
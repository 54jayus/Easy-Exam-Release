import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { pythonBackend } from '@/lib/pythonBackend'

// Configure marked options
marked.setOptions({
  gfm: true,
  breaks: true
})

export function useMarkdown() {
  const manualMarkdown = ref('')
  const manualHtml = ref('')
  const loading = ref({
    manual: false
  })

  async function loadManual() {
    loading.value.manual = true
    try {
      const res = await pythonBackend.request('system.getHelpManual', {})
      const content = res.content || ''

      if (!content) {
        throw new Error('Empty manual content')
      }

      manualMarkdown.value = content
      manualHtml.value = await marked(content)

      return content
    } catch (e) {
      console.error(e)
      ElMessage.error('说明书加载失败')
      throw e
    } finally {
      loading.value.manual = false
    }
  }

  return {
    manualMarkdown,
    manualHtml,
    loading,
    loadManual
  }
}

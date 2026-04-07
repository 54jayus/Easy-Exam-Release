import type { Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { pythonBackend } from '@/lib/pythonBackend'

type ProctoringConfig = {
  roomCount: number
  mode: string
  balanceMode: string
  genderMix: boolean
  internalMix: boolean
}

type SelectedCell = { roomId: number; c: string }

export function useProctoringSwap(options: {
  config: ProctoringConfig
  adjustMode: Ref<boolean>
  selectedCells: Ref<SelectedCell[]>
  schedule: Ref<any[]>
  teachers: Ref<any[]>
  subjects: Ref<any[]>
  getTeacherObj: (subjectId: string, roomNum: number, idx: number) => any
  logInfo: (msg: string) => void
  logSuccess: (msg: string) => void
  logWarning: (msg: string) => void
  logError: (msg: string) => void
}) {
  const {
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
  } = options

  const toggleAdjustMode = () => {
    adjustMode.value = !adjustMode.value
    selectedCells.value = []
    if (adjustMode.value) {
      ElMessageBox.alert('请在监考总览表中点击要交换的两个监考教师姓名。', '进入手动调整模式')
    } else {
      ElMessage.info('退出手动调整模式')
    }
  }

  const getCellStyle = ({ row, column }: any) => {
    const isSelected = selectedCells.value.some((cell) => cell.roomId === row.roomId && cell.c === column.property)
    if (isSelected) {
      return { backgroundColor: '#fef08a' }
    }
    if (typeof column.property === 'string' && column.property.startsWith('sub_')) {
      const parts = column.property.split('_')
      const subjectId = parts[1]
      const idx = config.mode === 'double' ? (Number(parts[2] || '1') - 1) : 0
      const t = getTeacherObj(subjectId, Number(row.roomId), idx)
      if (t?.isLocked) return { backgroundColor: '#fff1f2' }
      if (t?.presetRoom && Number(t.presetRoom) === Number(row.roomId)) return { backgroundColor: '#ecfdf5' }
    }
    return {}
  }

  const parseCell = (roomId: number, prop: string) => {
    const room = roomId
    let subId
    let tIdx
    if (config.mode === 'double') {
      const parts = prop.split('_')
      subId = parts[1]
      tIdx = parseInt(parts[2], 10) - 1
    } else {
      const parts = prop.split('_')
      subId = parts[1]
      tIdx = 0
    }
    return { room, subId, tIdx }
  }

  const checkProtected = (cell: SelectedCell) => {
    const parts = cell.c.split('_')
    const subId = parts[1]
    const tIdx = config.mode === 'double' ? (parseInt(parts[2], 10) - 1) : 0
    const t = getTeacherObj(subId, cell.roomId, tIdx)
    if (t?.isLocked) return `考场${cell.roomId}的${t.name}（已锁定）`
    if (t?.presetRoom && Number(t.presetRoom) === cell.roomId) return `考场${cell.roomId}的${t.name}（预设）`
    return null
  }

  const swapCells = async () => {
    const [c1, c2] = selectedCells.value

    const protect1 = checkProtected(c1)
    const protect2 = checkProtected(c2)

    if (protect1 || protect2) {
      const msg = [protect1, protect2].filter(Boolean).join(' 和 ')
      try {
        await ElMessageBox.confirm(
          `选中的 ${msg} 属于固定安排，强制交换可能违反预设规则。\n确定要继续吗？`,
          '确认交换',
          {
            confirmButtonText: '强制交换',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
      } catch {
        selectedCells.value = []
        return
      }
    }

    logInfo('开始交换监考安排')
    try {
      const p1 = parseCell(c1.roomId, c1.c)
      const p2 = parseCell(c2.roomId, c2.c)

      const res = await pythonBackend.request<any>('proctoring.swap', {
        p1,
        p2,
        schedule: schedule.value,
        teachers: teachers.value,
        subjects: subjects.value,
        config
      })

      if (res.success) {
        schedule.value = res.schedule
        teachers.value = res.teachers
        logSuccess('交换成功')
        ElMessage.success('交换成功')
      } else {
        logWarning('交换失败：' + res.message)
        ElMessage.warning(res.message)
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      logError('交换异常：' + msg)
    }
    selectedCells.value = []
  }

  const handleCellClick = (_row: any, column: any) => {
    const row = _row
    if (!adjustMode.value) return
    if (!column.property.startsWith('sub_')) return

    const roomId = row.roomId
    const cellKey = column.property

    const existingIdx = selectedCells.value.findIndex((c) => c.roomId === roomId && c.c === cellKey)
    if (existingIdx >= 0) {
      selectedCells.value.splice(existingIdx, 1)
    } else {
      if (selectedCells.value.length >= 2) {
        selectedCells.value.shift()
      }
      selectedCells.value.push({ roomId, c: cellKey })
    }

    if (selectedCells.value.length === 2) {
      swapCells()
    }
  }

  return {
    toggleAdjustMode,
    getCellStyle,
    handleCellClick,
  }
}

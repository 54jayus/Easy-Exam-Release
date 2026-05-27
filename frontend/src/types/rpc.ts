// RPC 方法签名定义
export type RpcMethods = {
  // System
  "system.resetData": {
    params: {}
    result: {}
  }
  "system.exportState": {
    params: { path: string }
    result: { success: boolean }
  }
  "system.importState": {
    params: { path: string }
    result: { success: boolean }
  }
  "system.getHelpManual": {
    params: {}
    result: { content: string }
  }
  "system.getUpdateGuardStatus": {
    params: {}
    result: {
      checked: boolean
      locked: boolean
      currentVersion: string
      latestVersion: string
      requiredVersion: string
      minSupportedVersion: string
      mandatory: boolean
      downloadUrl: string
      releaseDate: string
      notes: string[]
      enabled: boolean
      sourceUrl: string
      checkedAt: string
      errorMessage: string
    }
  }
  "system.refreshUpdateGuard": {
    params: {}
    result: {
      checked: boolean
      locked: boolean
      currentVersion: string
      latestVersion: string
      requiredVersion: string
      minSupportedVersion: string
      mandatory: boolean
      downloadUrl: string
      releaseDate: string
      notes: string[]
      enabled: boolean
      sourceUrl: string
      checkedAt: string
      errorMessage: string
    }
  }

  // Licensing
  "licensing.machineCode": {
    params: {}
    result: { machineCode: string }
  }
  "licensing.verify": {
    params: {}
    result: { valid: boolean; expireDate?: string; daysLeft?: number; message?: string }
  }
  "licensing.register": {
    params: { licenseKey: string }
    result: { success: boolean; message: string }
  }

  // Dashboard
  "dashboard.getStats": {
    params: {}
    result: {
      subjectsCount: number
      teachersCount: number
      studentsCount: number
      roomsCount: number
    }
  }

  // Subjects
  "subjects.list": {
    params: {}
    result: { subjects: Array<{ id?: string; name: string; duration?: number; duration_minutes?: number; room_count?: number; roomCount?: number; date?: string; time?: string; exam_date?: string; exam_time?: string; remark?: string }> }
  }
  "subjects.update": {
    params: { subjects: Array<{ name: string; duration: number; date: string; time: string }> }
    result: { proctoringReset: boolean }
  }
  "subjects.import": {
    params: { path: string | string[] }
    result: { subjects: any[]; errors: string[]; proctoringReset: boolean }
  }
  "subjects.export": {
    params: { path: string; subjects: any[] }
    result: {}
  }
  "subjects.template": {
    params: { path: string }
    result: {}
  }
  "subjects.validate": {
    params: { subjects: any[] }
    result: { errors: string[] }
  }

  // Proctoring
  "proctoring.getState": {
    params: {}
    result: { teachers: any[]; schedule: any[]; config: any }
  }
  "proctoring.startSolverJob": {
    params: { operation: "generate" | "continue"; teachers?: any[]; subjects?: any[]; schedule?: any[]; config?: any }
    result: { jobId?: string; status?: string; operation?: string; error?: string; activeJobId?: string }
  }
  "proctoring.getJobStatus": {
    params: { jobId: string }
    result: { jobId: string; status: string; operation?: string; message?: string; error?: string; elapsedSeconds?: number | null; progressPercent?: number; progress?: any; result?: any }
  }
  "proctoring.clearState": {
    params: {}
    result: {}
  }
  "proctoring.importTeachers": {
    params: { path: string }
    result: { teachers: any[]; errors: string[] }
  }
  "proctoring.generateSchedule": {
    params: { config: any }
    result: { schedule: any[] }
  }
  "proctoring.template": {
    params: { path: string }
    result: {}
  }
  "proctoring.export": {
    params: { path: string; teachers?: any[]; subjects?: any[]; schedule?: any[]; config?: any }
    result: {}
  }
  "proctoring.continue": {
    params: {}
    result: { schedule: any[] }
  }
  "proctoring.importSchedule": {
    params: { path: string }
    result: { schedule: any[] }
  }
  "proctoring.swap": {
    params: { sessionId: string; teacher1: string; teacher2: string }
    result: { schedule: any[] }
  }
  "proctoring.export_empty_preset": {
    params: { path: string; subjects?: any[]; roomCount?: number; mode?: string }
    result: {}
  }
  "proctoring.import_preset": {
    params: { path: string }
    result: {}
  }

  // Rooms
  "rooms.resetState": {
    params: {}
    result: {}
  }
  "rooms.getState": {
    params: {}
    result: { settings: any[]; studentsPath: string; config: any; results: any[] }
  }
  "rooms.getSubjectPriority": {
    params: {}
    result: { priority: string[] }
  }
  "rooms.setSubjectPriority": {
    params: { priority: string[] }
    result: {}
  }
  "rooms.generateTemplate": {
    params: { path: string }
    result: {}
  }
  "rooms.importSettings": {
    params: { path: string }
    result: { settings: any[] }
  }
  "rooms.importStudents": {
    params: { path: string }
    result: { preview: any[] }
  }
  "rooms.arrange": {
    params: { mode: string; config: any }
    result: { results: any[] }
  }
  "rooms.export": {
    params: { path: string }
    result: {}
  }
  "rooms.importResults": {
    params: { path: string }
    result: { results: any[] }
  }
  "rooms.getGaokaoTimeSettings": {
    params: {}
    result: { settings: any }
  }
  "rooms.setGaokaoTimeSettings": {
    params: { settings: any }
    result: {}
  }

  // Printing
  "printing.getState": {
    params: {}
    result: { sourceType: string; dataPath: string; headers: string[]; mapping: any; data: any[]; total: number; config?: any; commonConfig?: any }
  }
  "printing.saveConfig": {
    params: { config: any; commonConfig?: any; totalCount?: number; sourceType?: string; dataPath?: string; headers?: string[]; mapping?: any; data?: any[]; previewTotal?: number }
    result: {}
  }
  "printing.resetState": {
    params: {}
    result: {}
  }
  "printing.readHeaders": {
    params: { path: string }
    result: { headers: string[] }
  }
  "printing.previewData": {
    params: { path: string; mapping: any }
    result: { data: any[]; total: number }
  }
  "printing.loadFromSchedule": {
    params: {}
    result: { data: any[]; total: number }
  }
  "printing.previewPdf": {
    params: { type: string; config: any }
    result: { path: string }
  }
  "printing.generate": {
    params: { type: string; config: any; outputPath: string; sourceType?: string; dataPath?: string; mapping?: any; confirmFlags?: any }
    result: { path: string }
  }
}

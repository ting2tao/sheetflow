<template>
  <div class="app">
    <LanguageSwitcher />
    <header class="header">
      <h1>📊 SheetFlow</h1>
      <p class="subtitle">{{ t('app.subtitle') }}</p>
    </header>

    <main class="main">
      <!-- Step 1: Upload Section -->
      <section class="card upload-section" v-if="step === 1">
        <h2>{{ t('upload.title') }}</h2>
        <div
          class="drop-zone"
          :class="{ 'drag-over': isDragOver, 'has-file': file }"
          @drop.prevent="handleDrop"
          @dragover.prevent="isDragOver = true"
          @dragleave="isDragOver = false"
          @click="triggerFileInput"
        >
          <div v-if="!file" class="drop-content">
            <span class="drop-icon">📄</span>
            <p>{{ t('upload.drop') }}</p>
            <p class="drop-hint">{{ t('upload.hint') }}</p>
          </div>
          <div v-else class="file-info">
            <span class="file-icon">✅</span>
            <div class="file-details">
              <p class="file-name">{{ file.name }}</p>
              <p class="file-size">{{ formatFileSize(file.size) }}</p>
            </div>
            <button class="btn-remove" @click.stop="removeFile">✕</button>
          </div>
        </div>
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx"
          style="display: none"
          @change="handleFileSelect"
        >
        <button
          v-if="file"
          class="btn-primary"
          @click="uploadFile"
          :disabled="isUploading"
        >
          {{ isUploading ? t('upload.uploading') : t('upload.submit') }}
        </button>
      </section>

      <!-- Step 2: Sheet Selection & Settings -->
      <section class="card settings-section" v-if="step === 2">
        <h2>{{ t('settings.sheetsTitle') }}</h2>

        <div class="sheets-list">
          <div class="select-all">
            <label>
              <input
                type="checkbox"
                :checked="allSelected"
                @change="toggleAllSheets"
              >
              <span>{{ t('settings.selectAll') }}</span>
            </label>
          </div>

          <div
            v-for="sheet in sheets"
            :key="sheet.index"
            class="sheet-item"
            :class="{ selected: selectedSheets.includes(sheet.index) }"
          >
            <label>
              <input
                type="checkbox"
                :value="sheet.index"
                v-model="selectedSheets"
              >
              <div class="sheet-info">
                <span class="sheet-name">{{ sheet.name }}</span>
                <span class="sheet-meta">
                  {{ t('settings.sheetMeta', { rows: sheet.rows, columns: sheet.columns }) }}
                </span>
              </div>
            </label>
          </div>
        </div>

        <h2>{{ t('settings.title') }}</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <label>{{ t('settings.headerRows') }}</label>
            <input
              v-model.number="headerRows"
              type="number"
              min="0"
              max="100"
              placeholder="1"
            >
            <span class="setting-hint">{{ t('settings.headerRowsHint') }}</span>
          </div>
          <div class="setting-item">
            <label>{{ t('settings.pageSize') }}</label>
            <input
              v-model.number="pageSize"
              type="number"
              min="1"
              max="1000"
              placeholder="10"
            >
            <span class="setting-hint">{{ t('settings.pageSizeHint') }}</span>
          </div>
          <div class="setting-item">
            <label>{{ t('settings.format') }}</label>
            <div class="format-selector">
              <label class="format-option">
                <input type="radio" v-model="format" value="png">
                <span>PNG</span>
                <small>{{ t('settings.pngHint') }}</small>
              </label>
              <label class="format-option">
                <input type="radio" v-model="format" value="jpg">
                <span>JPG</span>
                <small>{{ t('settings.jpgHint') }}</small>
              </label>
            </div>
          </div>
          <div class="setting-item" v-if="format === 'jpg'">
            <label>{{ t('settings.quality') }}</label>
            <input
              v-model.number="quality"
              type="range"
              min="1"
              max="100"
            >
            <span class="setting-hint">{{ quality }}%</span>
          </div>
        </div>

        <div class="action-buttons">
          <button class="btn-secondary" @click="goBack">
            {{ t('settings.back') }}
          </button>
          <button
            class="btn-primary"
            @click="startRender"
            :disabled="selectedSheets.length === 0 || isProcessing"
          >
            {{
              isProcessing
                ? t('settings.processing')
                : t('settings.start', { count: selectedSheets.length })
            }}
          </button>
        </div>
      </section>

      <!-- Step 3: Progress Section -->
      <section class="card progress-section" v-if="step === 3">
        <h2>{{ t('progress.title') }}</h2>
        <div class="progress-content">
          <div class="progress-status">
            <span class="status-icon" :class="statusClass">{{ statusIcon }}</span>
            <span class="status-text">{{ statusMessage }}</span>
          </div>

          <div class="progress-bar-container" v-if="status !== 'completed' && status !== 'error'">
            <div class="progress-bar" :style="{ width: progressPercent + '%' }">
              <span class="progress-text" v-if="progressPercent > 10">{{ progressPercent }}%</span>
            </div>
          </div>

          <div class="progress-details" v-if="status === 'processing' && jobInfo">
            <div class="detail-item">
              <span class="detail-label">{{ t('progress.overall') }}</span>
              <span class="detail-value">
                {{
                  t('progress.pagePosition', {
                    current: jobInfo.pages_processed || 0,
                    total: jobInfo.total_pages || '?',
                  })
                }}
              </span>
            </div>
            <div class="detail-item" v-if="jobInfo.current_sheet">
              <span class="detail-label">{{ t('progress.currentSheet') }}</span>
              <span class="detail-value">{{ jobInfo.current_sheet }}</span>
            </div>
            <div class="detail-item" v-if="jobInfo.current_page">
              <span class="detail-label">{{ t('progress.current') }}</span>
              <span class="detail-value">
                {{
                  t('progress.pagePosition', {
                    current: jobInfo.current_page,
                    total: jobInfo.sheet_pages,
                  })
                }}
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">{{ t('progress.completedSheets') }}</span>
              <span class="detail-value">
                {{ jobInfo.sheets_processed || 0 }} /
                {{
                  t(
                    'progress.sheetCount',
                    { count: jobInfo.total_sheets || '?' },
                    jobInfo.total_sheets || 0,
                  )
                }}
              </span>
            </div>
          </div>

          <div class="job-info" v-if="jobInfo && status !== 'processing'">
            <p v-if="jobInfo.total_sheets">
              {{ t('progress.processedSheetCount', { count: jobInfo.total_sheets }) }}
            </p>
            <p v-if="jobInfo.total_pages">
              {{ t('progress.totalPages', { count: jobInfo.total_pages }) }}
            </p>
          </div>

          <!-- Completed sheets info -->
          <div v-if="status === 'completed' && jobInfo?.sheets" class="completed-sheets">
            <h3>{{ t('progress.completed') }}</h3>
            <div v-for="sheet in jobInfo.sheets" :key="sheet.index" class="completed-sheet">
              <span class="sheet-name">{{ sheet.name }}</span>
              <span class="sheet-pages">
                {{ t('progress.pageCount', { count: sheet.pages }, sheet.pages) }}
              </span>
            </div>
          </div>

          <div class="action-buttons">
            <button
              v-if="status === 'completed'"
              class="btn-primary"
              @click="downloadResult"
            >
              {{ t('progress.download') }}
            </button>
            <button
              class="btn-secondary"
              @click="resetForm"
            >
              {{ t('progress.restart') }}
            </button>
          </div>
        </div>
      </section>
    </main>

    <footer class="footer">
      <p>{{ t('app.footer') }}</p>
    </footer>
  </div>
</template>

<script>
import { ref, computed, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import { localizeApiError, localizeJobMessage } from './i18n/api-message'
import { observeLocaleChanges } from './i18n/locale'

export default {
  name: 'App',
  components: {
    LanguageSwitcher,
  },
  setup() {
    const { t, locale } = useI18n()
    document.documentElement.lang = locale.value
    const stopObservingLocale = observeLocaleChanges((nextLocale) => {
      locale.value = nextLocale
      document.documentElement.lang = nextLocale
    })

    // Step management
    const step = ref(1)  // 1: upload, 2: settings, 3: progress

    // Upload state
    const file = ref(null)
    const fileInput = ref(null)
    const isDragOver = ref(false)
    const isUploading = ref(false)

    // Sheet selection
    const jobId = ref(null)
    const sheets = ref([])
    const selectedSheets = ref([])

    // Settings
    const headerRows = ref(1)
    const pageSize = ref(1)
    const format = ref('png')
    const quality = ref(90)

    // Progress
    const status = ref('')
    const statusPayload = ref(null)
    const jobInfo = ref(null)
    const isProcessing = ref(false)
    let pollTimer = null

    // Computed
    const allSelected = computed(() => {
      return sheets.value.length > 0 && selectedSheets.value.length === sheets.value.length
    })

    const statusClass = computed(() => {
      switch (status.value) {
        case 'completed': return 'success'
        case 'error': return 'error'
        default: return 'processing'
      }
    })

    const statusIcon = computed(() => {
      switch (status.value) {
        case 'completed': return '✅'
        case 'error': return '❌'
        case 'queued': return '⏳'
        case 'parsing': return '📖'
        case 'processing': return '⚙️'
        case 'zipping': return '📦'
        default: return '⏳'
      }
    })

    const progressPercent = computed(() => {
      // Use detailed progress if available
      if (jobInfo.value?.progress !== undefined && status.value === 'processing') {
        return jobInfo.value.progress
      }

      const progressMap = {
        'queued': 5,
        'parsing': 10,
        'processing': 50,
        'zipping': 95,
        'completed': 100,
        'error': 100,
      }
      return progressMap[status.value] || 0
    })

    const statusMessage = computed(() => {
      locale.value
      return statusPayload.value ? localizeJobMessage(statusPayload.value, t) : ''
    })

    // Methods
    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (e) => {
      const selectedFile = e.target.files[0]
      if (selectedFile && selectedFile.name.endsWith('.xlsx')) {
        file.value = selectedFile
      } else {
        alert(t('errors.invalidSelection'))
      }
    }

    const handleDrop = (e) => {
      isDragOver.value = false
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile && droppedFile.name.endsWith('.xlsx')) {
        file.value = droppedFile
      } else {
        alert(t('errors.invalidSelection'))
      }
    }

    const removeFile = () => {
      file.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const formatFileSize = (bytes) => {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    const uploadFile = async () => {
      if (!file.value) return

      isUploading.value = true
      const formData = new FormData()
      formData.append('file', file.value)

      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}))
          throw new Error(localizeApiError(payload, t))
        }

        const data = await response.json()
        jobId.value = data.job_id
        sheets.value = data.sheets || []

        // Track upload event
        window.gtag?.('event', 'file_upload', {
          file_size: file.value.size,
          sheet_count: data.sheets?.length || 0,
          language: locale.value,
        })

        // Auto select first sheet
        if (sheets.value.length > 0) {
          selectedSheets.value = [sheets.value[0].index]
        }

        // Move to step 2
        step.value = 2
      } catch (error) {
        alert(t('errors.prefix', { message: error.message }))
      } finally {
        isUploading.value = false
      }
    }

    const toggleAllSheets = () => {
      if (allSelected.value) {
        selectedSheets.value = []
      } else {
        selectedSheets.value = sheets.value.map(s => s.index)
      }
    }

    const goBack = () => {
      step.value = 1
      jobId.value = null
      sheets.value = []
      selectedSheets.value = []
    }

    const startRender = async () => {
      if (!jobId.value || selectedSheets.value.length === 0) return

      isProcessing.value = true
      const formData = new FormData()
      formData.append('job_id', jobId.value)
      formData.append('header_rows', headerRows.value)
      formData.append('page_size', pageSize.value)
      formData.append('format', format.value)
      formData.append('sheet_indices', selectedSheets.value.join(','))
      if (format.value === 'jpg') {
        formData.append('quality', quality.value)
      }

      try {
        const response = await fetch('/api/render', {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}))
          throw new Error(localizeApiError(payload, t))
        }

        const data = await response.json()
        status.value = data.status
        statusPayload.value = data

        // Track render event
        window.gtag?.('event', 'render_start', {
          sheet_count: selectedSheets.value.length,
          format: format.value,
          language: locale.value,
        })

        // Move to step 3
        step.value = 3

        // Start polling for status
        startPolling()
      } catch (error) {
        alert(t('errors.prefix', { message: error.message }))
        isProcessing.value = false
      }
    }

    const startPolling = () => {
      pollTimer = setInterval(async () => {
        try {
          const response = await fetch(`/api/job/${jobId.value}`)
          if (!response.ok) {
            const payload = await response.json().catch(() => ({}))
            throw new Error(localizeApiError(payload, t))
          }

          const data = await response.json()
          status.value = data.status
          statusPayload.value = data
          jobInfo.value = data

          if (data.status === 'completed' || data.status === 'error') {
            clearInterval(pollTimer)
            isProcessing.value = false
          }
        } catch (error) {
          console.error(t('errors.polling'), error)
        }
      }, 1000)
    }

    const downloadResult = () => {
      if (jobId.value) {
        window.gtag?.('event', 'file_download', {
          job_id: jobId.value,
          language: locale.value,
        })
        window.location.href = `/api/download/${jobId.value}`
      }
    }

    const resetForm = () => {
      step.value = 1
      file.value = null
      jobId.value = null
      sheets.value = []
      selectedSheets.value = []
      status.value = ''
      statusPayload.value = null
      jobInfo.value = null
      isProcessing.value = false
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      if (pollTimer) {
        clearInterval(pollTimer)
      }
    }

    onUnmounted(() => {
      if (pollTimer) {
        clearInterval(pollTimer)
      }
      stopObservingLocale()
    })

    // GA4 page tracking for SPA
    const pageNames = { 1: 'upload', 2: 'settings', 3: 'progress' }
    watch(step, (newStep) => {
      const pageName = pageNames[newStep] || 'unknown'
      window.gtag?.('event', 'page_view', {
        page_title: `SheetFlow - ${pageName}`,
        page_location: window.location.href,
        page_path: `${window.location.pathname}#${pageName}`,
        language: locale.value,
      })
    })

    return {
      step,
      file,
      fileInput,
      isDragOver,
      isUploading,
      jobId,
      sheets,
      selectedSheets,
      headerRows,
      pageSize,
      format,
      quality,
      status,
      statusMessage,
      jobInfo,
      isProcessing,
      allSelected,
      statusClass,
      statusIcon,
      progressPercent,
      t,
      triggerFileInput,
      handleFileSelect,
      handleDrop,
      removeFile,
      formatFileSize,
      uploadFile,
      toggleAllSheets,
      goBack,
      startRender,
      downloadResult,
      resetForm,
    }
  },
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue",
               Helvetica, Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.app {
  position: relative;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  color: white;
  padding: 40px 0 30px;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card h2 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.3rem;
}

/* Drop Zone */
.drop-zone {
  border: 3px dashed #ddd;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.drop-zone:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.drop-zone.drag-over {
  border-color: #667eea;
  background: #eef0ff;
  transform: scale(1.02);
}

.drop-zone.has-file {
  border-color: #4caf50;
  background: #f0fff0;
  padding: 20px;
}

.drop-content {
  color: #666;
}

.drop-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 15px;
}

.drop-hint {
  font-size: 0.9rem;
  color: #999;
  margin-top: 8px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.file-icon {
  font-size: 2rem;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-name {
  font-weight: 600;
  color: #333;
}

.file-size {
  color: #666;
  font-size: 0.9rem;
}

.btn-remove {
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove:hover {
  background: #ff6b81;
}

/* Sheets List */
.sheets-list {
  margin-bottom: 25px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.select-all {
  padding: 12px 15px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  font-weight: 600;
}

.sheet-item {
  padding: 12px 15px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.sheet-item:last-child {
  border-bottom: none;
}

.sheet-item:hover {
  background: #f8f9ff;
}

.sheet-item.selected {
  background: #eef0ff;
}

.sheet-item label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.sheet-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.sheet-info {
  flex: 1;
}

.sheet-name {
  display: block;
  font-weight: 600;
  color: #333;
}

.sheet-meta {
  font-size: 0.85rem;
  color: #888;
}

/* Settings */
.settings-grid {
  display: grid;
  gap: 25px;
  margin-bottom: 25px;
}

.setting-item label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.setting-item input[type="number"] {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.setting-item input[type="number"]:focus {
  outline: none;
  border-color: #667eea;
}

.setting-hint {
  font-size: 0.85rem;
  color: #888;
  margin-top: 5px;
  display: block;
}

.format-selector {
  display: flex;
  gap: 15px;
}

.format-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.format-option:has(input:checked) {
  border-color: #667eea;
  background: #f8f9ff;
}

.format-option input {
  margin-bottom: 8px;
}

.format-option span {
  font-weight: 600;
  color: #333;
}

.format-option small {
  color: #888;
  font-size: 0.8rem;
  text-align: center;
}

input[type="range"] {
  width: 100%;
  margin: 10px 0;
}

/* Buttons */
.btn-primary {
  width: 100%;
  padding: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  width: 100%;
  padding: 12px;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.action-buttons {
  display: flex;
  gap: 15px;
}

.action-buttons button {
  flex: 1;
}

/* Progress */
.progress-content {
  text-align: center;
}

.progress-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
}

.status-icon {
  font-size: 1.5rem;
}

.status-text {
  font-size: 1.1rem;
  color: #333;
}

.progress-bar-container {
  background: #e0e0e0;
  border-radius: 10px;
  height: 24px;
  margin-bottom: 20px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 10px;
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
}

.progress-text {
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.progress-details {
  background: #f8f9ff;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  color: #666;
  font-size: 0.9rem;
}

.detail-value {
  color: #333;
  font-weight: 600;
  font-size: 0.9rem;
}

.job-info {
  color: #666;
  margin-bottom: 20px;
}

.job-info p {
  margin: 5px 0;
}

.completed-sheets {
  background: #f0fff0;
  border: 1px solid #4caf50;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  text-align: left;
}

.completed-sheets h3 {
  color: #4caf50;
  margin-bottom: 10px;
}

.completed-sheet {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
}

.completed-sheet:last-child {
  border-bottom: none;
}

.completed-sheet .sheet-name {
  color: #333;
}

.completed-sheet .sheet-pages {
  color: #4caf50;
  font-weight: 600;
}

/* Footer */
.footer {
  text-align: center;
  color: white;
  padding: 30px 0;
  opacity: 0.8;
}

/* Responsive */
@media (min-width: 600px) {
  .settings-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

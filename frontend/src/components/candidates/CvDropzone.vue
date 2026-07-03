<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  select: [file: File]
}>()

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedName = ref('')

function onDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function handleFile(file: File | undefined) {
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    alert('Only PDF files are accepted.')
    return
  }
  selectedName.value = file.name
  emit('select', file)
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  handleFile(e.dataTransfer?.files[0])
}

function onInputChange(e: Event) {
  const input = e.target as HTMLInputElement
  handleFile(input.files?.[0])
}

function openPicker() {
  fileInput.value?.click()
}
</script>

<template>
  <div
    class="hrms-dropzone"
    :class="{ 'hrms-dropzone--active': isDragging }"
    role="button"
    tabindex="0"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
    @click="openPicker"
    @keydown.enter="openPicker"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".pdf,application/pdf"
      class="sr-only"
      @change="onInputChange"
    />
    <div class="hrms-dropzone__icon" aria-hidden="true">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6M12 18v-6M9 15l3-3 3 3" />
      </svg>
    </div>
    <p class="hrms-dropzone__title">Drop CV here or click to browse</p>
    <p class="hrms-dropzone__hint">PDF only · Stored in MinIO · Parsed with Mistral AI</p>
    <p v-if="selectedName" class="hrms-badge" style="margin-top: 8px">{{ selectedName }}</p>
  </div>
</template>

<style scoped>
.hrms-dropzone__icon {
  color: var(--hrms-primary);
  opacity: 0.8;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>

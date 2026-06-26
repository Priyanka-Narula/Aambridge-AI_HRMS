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
    class="dropzone"
    :class="{ 'dropzone--active': isDragging }"
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
      class="dropzone__input"
      @change="onInputChange"
    />
    <div class="dropzone__icon" aria-hidden="true">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6M12 18v-6M9 15l3-3 3 3" />
      </svg>
    </div>
    <p class="dropzone__title">Drop CV here or click to browse</p>
    <p class="dropzone__hint">PDF only · Stored in MinIO · Parsed with Mistral AI</p>
    <p v-if="selectedName" class="dropzone__file">{{ selectedName }}</p>
  </div>
</template>

<style scoped>
.dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 48px 24px;
  border: 2px dashed var(--hrms-border-strong);
  border-radius: var(--hrms-radius-lg);
  background: linear-gradient(135deg, var(--hrms-secondary) 0%, var(--hrms-surface-elevated) 100%);
  cursor: pointer;
  transition:
    border-color var(--hrms-transition),
    background var(--hrms-transition);
}

.dropzone:hover,
.dropzone--active {
  border-color: var(--hrms-primary-muted);
  background: var(--hrms-secondary);
}

.dropzone__input {
  display: none;
}

.dropzone__icon {
  color: var(--hrms-primary);
  opacity: 0.8;
}

.dropzone__title {
  margin: 0;
  font-weight: 600;
  color: var(--hrms-primary-dark);
}

.dropzone__hint {
  margin: 0;
  font-size: 0.85rem;
  color: var(--hrms-text-muted);
}

.dropzone__file {
  margin: 8px 0 0;
  padding: 6px 14px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--hrms-primary);
  background: var(--hrms-surface-elevated);
  border-radius: 999px;
}
</style>

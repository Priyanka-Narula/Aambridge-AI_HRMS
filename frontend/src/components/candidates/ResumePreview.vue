<script setup lang="ts">
withDefaults(
  defineProps<{
    src: string | null
    filename?: string | null
    loading?: boolean
    error?: string | null
    height?: string
  }>(),
  {
    filename: null,
    loading: false,
    error: null,
    height: 'min(70vh, 820px)',
  },
)
</script>

<template>
  <div class="resume-preview">
    <div class="resume-preview__header">
      <h3 class="resume-preview__title">Resume preview</h3>
      <span v-if="filename" class="resume-preview__filename">{{ filename }}</span>
    </div>

    <div v-if="loading" class="resume-preview__state">Loading resume…</div>
    <div v-else-if="error" class="resume-preview__state resume-preview__state--error">{{ error }}</div>
    <div v-else-if="!src" class="resume-preview__state">No resume available to preview.</div>
    <iframe
      v-else
      class="resume-preview__frame"
      :src="src"
      :style="{ height }"
      title="Resume PDF preview"
    />
  </div>
</template>

<style scoped>
.resume-preview {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.resume-preview__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.resume-preview__title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 650;
}

.resume-preview__filename {
  font-size: 0.75rem;
  color: var(--hrms-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 55%;
}

.resume-preview__frame {
  width: 100%;
  border: 1px solid var(--hrms-border);
  border-radius: 10px;
  background: #fff;
}

.resume-preview__state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  padding: 24px;
  border: 1px dashed var(--hrms-border);
  border-radius: 10px;
  color: var(--hrms-text-muted);
  font-size: 0.875rem;
  text-align: center;
}

.resume-preview__state--error {
  color: #b91c1c;
  border-color: rgba(185, 28, 28, 0.35);
  background: rgba(185, 28, 28, 0.04);
}
</style>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { uploadCv } from '@/api/candidates'
import CvDropzone from '@/components/candidates/CvDropzone.vue'
import { useAuthStore } from '@/stores/auth'
import { useCvIngestStore } from '@/stores/cvIngest'

const router = useRouter()
const auth = useAuthStore()
const cvIngest = useCvIngestStore()

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const error = ref('')

function onFileSelect(file: File) {
  selectedFile.value = file
  error.value = ''
}

async function handleUpload() {
  if (!selectedFile.value) {
    error.value = 'Please select a PDF file first.'
    return
  }

  uploading.value = true
  error.value = ''

  try {
    const result = await uploadCv(selectedFile.value, auth.user!.email)
    cvIngest.setFromUpload(result)
    await router.push({ name: 'cv-verify' })
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="cv-upload">
    <header class="cv-upload__header">
      <div>
        <h2>Upload CV</h2>
        <p>PDF is stored in MinIO, text extracted with PyMuPDF, and fields parsed using Mistral AI.</p>
      </div>
      <RouterLink to="/candidates" class="cv-upload__back">← Back to candidates</RouterLink>
    </header>

    <CvDropzone @select="onFileSelect" />

    <div v-if="error" class="cv-upload__error" role="alert">{{ error }}</div>

    <div class="cv-upload__actions">
      <button
        type="button"
        class="cv-upload__btn"
        :disabled="!selectedFile || uploading"
        @click="handleUpload"
      >
        {{ uploading ? 'Processing CV…' : 'Upload & Parse' }}
      </button>
      <p v-if="uploading" class="cv-upload__note">
        This may take up to 2 minutes while the AI extracts fields.
      </p>
    </div>

    <ol class="cv-upload__steps">
      <li><strong>Upload</strong> — PDF saved to MinIO object storage</li>
      <li><strong>Extract</strong> — Text pulled from every page via PyMuPDF</li>
      <li><strong>Parse</strong> — Mistral AI maps fields to the candidate schema</li>
      <li><strong>Verify</strong> — Review and edit before saving to the database</li>
    </ol>
  </div>
</template>

<style scoped>
.cv-upload__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.cv-upload__header h2 {
  margin: 0 0 6px;
  font-family: var(--hrms-font-display);
  font-size: 1.75rem;
  color: var(--hrms-primary-dark);
}

.cv-upload__header p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--hrms-text-muted);
  max-width: 520px;
}

.cv-upload__back {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--hrms-primary);
}

.cv-upload__error {
  margin-top: 16px;
  padding: 12px 16px;
  font-size: 0.9rem;
  color: #9b3d5c;
  background: #fce8ef;
  border: 1px solid #e8b4c4;
  border-radius: var(--hrms-radius-md);
}

.cv-upload__actions {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.cv-upload__btn {
  padding: 12px 28px;
  border: none;
  border-radius: var(--hrms-radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, var(--hrms-primary) 0%, var(--hrms-primary-dark) 100%);
  cursor: pointer;
  transition: opacity var(--hrms-transition);
}

.cv-upload__btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.cv-upload__note {
  margin: 0;
  font-size: 0.82rem;
  color: var(--hrms-text-muted);
  font-style: italic;
}

.cv-upload__steps {
  margin: 32px 0 0;
  padding: 20px 20px 20px 36px;
  background: var(--hrms-secondary);
  border-radius: var(--hrms-radius-lg);
  border-left: 4px solid var(--hrms-accent);
}

.cv-upload__steps li {
  margin-bottom: 8px;
  font-size: 0.88rem;
  color: var(--hrms-text-muted);
  line-height: 1.5;
}

.cv-upload__steps li:last-child {
  margin-bottom: 0;
}

.cv-upload__steps strong {
  color: var(--hrms-primary-dark);
}
</style>

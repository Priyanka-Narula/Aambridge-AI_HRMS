<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { uploadCv } from '@/api/candidates'
import CvDropzone from '@/components/candidates/CvDropzone.vue'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageLayout from '@/components/ui/PageLayout.vue'
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
    cvIngest.setFromUpload(result, selectedFile.value)
    await router.push({ name: 'cv-verify' })
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <PageLayout variant="wide">
    <PageHeader title="Upload CV" subtitle="PDF is stored in MinIO, text extracted with PyMuPDF, and fields parsed using Mistral AI.">
      <template #actions>
        <RouterLink to="/candidates" class="hrms-link-back">Back to candidates</RouterLink>
      </template>
    </PageHeader>

    <CvDropzone @select="onFileSelect" />

    <HrmsAlert v-if="error" type="error">{{ error }}</HrmsAlert>

    <div style="margin-top: 20px">
      <button
        type="button"
        class="hrms-btn hrms-btn--primary hrms-btn--lg"
        :disabled="!selectedFile || uploading"
        @click="handleUpload"
      >
        {{ uploading ? 'Processing CV...' : 'Upload & Parse' }}
      </button>
      <p v-if="uploading" class="hrms-page-subtitle" style="margin-top: 8px; font-style: italic">
        This may take up to 2 minutes while the AI extracts fields.
      </p>
    </div>

    <ol class="hrms-steps">
      <li><strong>Upload</strong> - PDF saved to MinIO object storage</li>
      <li><strong>Extract</strong> - Text pulled from every page via PyMuPDF</li>
      <li><strong>Parse</strong> - Mistral AI maps fields to the candidate schema</li>
      <li><strong>Verify</strong> - Review and edit before saving to the database</li>
    </ol>
  </PageLayout>
</template>

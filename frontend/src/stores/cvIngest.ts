import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { CandidateDraft, CvUploadResponse } from '@/types/candidate'

export const useCvIngestStore = defineStore('cvIngest', () => {
  const uploadResult = ref<CvUploadResponse | null>(null)
  const draft = ref<CandidateDraft | null>(null)
  const sourceFile = ref<File | null>(null)
  const resumePreviewUrl = ref<string | null>(null)

  function setFromUpload(result: CvUploadResponse, file?: File | null) {
    clearPreviewUrl()
    uploadResult.value = result
    sourceFile.value = file ?? null
    if (file) {
      resumePreviewUrl.value = URL.createObjectURL(file)
    }
    const preview = result.candidate_preview
    draft.value = {
      ...structuredClone(preview),
      skills: preview.skills ?? [],
      education: preview.education ?? [],
      work_experience: preview.work_experience ?? [],
    }
  }

  function clearPreviewUrl() {
    if (resumePreviewUrl.value) {
      URL.revokeObjectURL(resumePreviewUrl.value)
      resumePreviewUrl.value = null
    }
  }

  function clear() {
    clearPreviewUrl()
    uploadResult.value = null
    draft.value = null
    sourceFile.value = null
  }

  return {
    uploadResult,
    draft,
    sourceFile,
    resumePreviewUrl,
    setFromUpload,
    clear,
  }
})

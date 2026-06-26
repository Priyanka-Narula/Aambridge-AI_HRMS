import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { CandidateDraft, CvUploadResponse } from '@/types/candidate'

export const useCvIngestStore = defineStore('cvIngest', () => {
  const uploadResult = ref<CvUploadResponse | null>(null)
  const draft = ref<CandidateDraft | null>(null)

  function setFromUpload(result: CvUploadResponse) {
    uploadResult.value = result
    const preview = result.candidate_preview
    draft.value = {
      ...structuredClone(preview),
      skills: preview.skills ?? [],
      education: preview.education ?? [],
      work_experience: preview.work_experience ?? [],
    }
  }

  function clear() {
    uploadResult.value = null
    draft.value = null
  }

  return { uploadResult, draft, setFromUpload, clear }
})

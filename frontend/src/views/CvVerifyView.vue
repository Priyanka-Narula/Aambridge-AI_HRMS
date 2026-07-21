<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { approveCandidate } from '@/api/candidates'
import CandidateVerifyForm from '@/components/candidates/CandidateVerifyForm.vue'
import ResumePreview from '@/components/candidates/ResumePreview.vue'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageLayout from '@/components/ui/PageLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { useCvIngestStore } from '@/stores/cvIngest'

const router = useRouter()
const auth = useAuthStore()
const cvIngest = useCvIngestStore()

const saving = ref(false)
const error = ref('')
const success = ref('')
const showTextPreview = ref(false)

const uploadMeta = computed(() => cvIngest.uploadResult)
const resumeSrc = computed(() => cvIngest.resumePreviewUrl)
const resumeFilename = computed(
  () => uploadMeta.value?.filename ?? cvIngest.sourceFile?.name ?? null,
)

onMounted(() => {
  if (!cvIngest.draft) {
    router.replace({ name: 'cv-upload' })
  }
})

async function handleSave() {
  if (!cvIngest.draft) return

  saving.value = true
  error.value = ''
  success.value = ''

  try {
    const result = await approveCandidate(cvIngest.draft, auth.user!.email)
    success.value = `Candidate saved successfully (ID: ${result.candidate_id})`
    cvIngest.clear()
    setTimeout(() => router.push({ name: 'candidates' }), 1500)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to save candidate.'
  } finally {
    saving.value = false
  }
}

function handleDiscard() {
  cvIngest.clear()
  router.push({ name: 'cv-upload' })
}
</script>

<template>
  <PageLayout v-if="cvIngest.draft" variant="wide">
    <PageHeader title="Verify & Save Candidate" subtitle="Review the resume and parsed fields, correct any errors, then save.">
      <div v-if="uploadMeta" class="hrms-meta-row" style="margin-top: 12px">
        <span class="hrms-badge">{{ uploadMeta.filename }}</span>
        <span v-if="uploadMeta.parsing_method" class="hrms-badge hrms-badge--muted">
          Parser: {{ uploadMeta.parsing_method }}
        </span>
        <span class="hrms-badge hrms-badge--muted">
          {{ uploadMeta.total_characters.toLocaleString() }} chars extracted
        </span>
      </div>
    </PageHeader>

    <HrmsAlert v-if="uploadMeta?.validation_errors?.length" type="warning">
      <strong>Validation warnings from parser:</strong>
      <ul style="margin: 8px 0 0; padding-left: 18px">
        <li v-for="(err, i) in uploadMeta.validation_errors" :key="i">{{ err }}</li>
      </ul>
    </HrmsAlert>

    <div class="cv-verify-layout">
      <div class="cv-verify-layout__form">
        <CandidateVerifyForm v-model="cvIngest.draft" />
      </div>

      <aside class="cv-verify-layout__preview">
        <div class="hrms-card hrms-card--flat cv-verify-sticky">
          <div class="hrms-card__body">
            <ResumePreview
              :src="resumeSrc"
              :filename="resumeFilename"
              height="min(72vh, 860px)"
            />

            <div class="cv-verify-tools">
              <button
                type="button"
                class="hrms-btn hrms-btn--sm"
                @click="showTextPreview = !showTextPreview"
              >
                {{ showTextPreview ? 'Hide extracted text' : 'Show extracted text' }}
              </button>
              <p v-if="uploadMeta?.storage_uri" class="cv-verify__uri">
                {{ uploadMeta.storage_uri }}
              </p>
            </div>

            <div v-if="showTextPreview" class="cv-verify-text">
              <h4 class="cv-verify-text__title">Extracted text</h4>
              <pre class="cv-verify__pre">{{ uploadMeta?.text_preview }}</pre>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <HrmsAlert v-if="error" type="error">{{ error }}</HrmsAlert>
    <HrmsAlert v-if="success" type="success">{{ success }}</HrmsAlert>

    <div class="hrms-actions">
      <button type="button" class="hrms-btn hrms-btn--primary hrms-btn--lg" :disabled="saving" @click="handleSave">
        {{ saving ? 'Saving...' : 'Save to Database' }}
      </button>
      <button type="button" class="hrms-btn hrms-btn--ghost hrms-btn--lg" :disabled="saving" @click="handleDiscard">
        Discard & Upload Another
      </button>
    </div>
  </PageLayout>
</template>

<style scoped>
.cv-verify-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 0.95fr);
  gap: 24px;
  align-items: start;
}

@media (max-width: 1100px) {
  .cv-verify-layout {
    grid-template-columns: 1fr;
  }

  .cv-verify-sticky {
    position: static;
  }
}

.cv-verify-sticky {
  position: sticky;
  top: 16px;
}

.cv-verify-tools {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.cv-verify-text {
  margin-top: 12px;
}

.cv-verify-text__title {
  margin: 0 0 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.cv-verify__pre {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--hrms-text-muted);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow-y: auto;
}

.cv-verify__uri {
  margin: 0;
  font-size: 0.72rem;
  color: var(--hrms-text-muted);
  word-break: break-all;
}
</style>

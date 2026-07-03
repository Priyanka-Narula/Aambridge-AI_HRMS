<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { approveCandidate } from '@/api/candidates'
import CandidateVerifyForm from '@/components/candidates/CandidateVerifyForm.vue'
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

const uploadMeta = computed(() => cvIngest.uploadResult)

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
    <PageHeader title="Verify & Save Candidate" subtitle="Review parsed fields, correct any errors, then save to the database.">
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

    <div class="hrms-grid-2">
      <div>
        <CandidateVerifyForm v-model="cvIngest.draft" />
      </div>

      <aside>
        <div class="hrms-card hrms-card--flat" style="margin-bottom: 16px">
          <div class="hrms-card__body">
            <h3 class="hrms-card__title">Extracted text preview</h3>
            <pre class="cv-verify__pre">{{ uploadMeta?.text_preview }}</pre>
          </div>
        </div>
        <div class="hrms-card hrms-card--flat">
          <div class="hrms-card__body">
            <h3 class="hrms-card__title">Storage</h3>
            <p class="cv-verify__uri">{{ uploadMeta?.storage_uri }}</p>
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
.cv-verify__pre {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--hrms-text-muted);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 360px;
  overflow-y: auto;
}

.cv-verify__uri {
  margin: 0;
  font-size: 0.78rem;
  color: var(--hrms-text-muted);
  word-break: break-all;
}
</style>

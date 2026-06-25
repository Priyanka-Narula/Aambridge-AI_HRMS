<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { approveCandidate } from '@/api/candidates'
import CandidateVerifyForm from '@/components/candidates/CandidateVerifyForm.vue'
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
    const result = await approveCandidate(cvIngest.draft, auth.user.email)
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
  <div v-if="cvIngest.draft" class="cv-verify">
    <header class="cv-verify__header">
      <div>
        <h2>Verify &amp; Save Candidate</h2>
        <p>Review parsed fields, correct any errors, then save to the database.</p>
      </div>
      <div class="cv-verify__meta" v-if="uploadMeta">
        <span class="cv-verify__badge">{{ uploadMeta.filename }}</span>
        <span v-if="uploadMeta.parsing_method" class="cv-verify__badge cv-verify__badge--muted">
          Parser: {{ uploadMeta.parsing_method }}
        </span>
        <span class="cv-verify__badge cv-verify__badge--muted">
          {{ uploadMeta.total_characters.toLocaleString() }} chars extracted
        </span>
      </div>
    </header>

    <div
      v-if="uploadMeta?.validation_errors?.length"
      class="cv-verify__warnings"
      role="alert"
    >
      <strong>Validation warnings from parser:</strong>
      <ul>
        <li v-for="(err, i) in uploadMeta.validation_errors" :key="i">{{ err }}</li>
      </ul>
    </div>

    <div class="cv-verify__layout">
      <div class="cv-verify__form-col">
        <CandidateVerifyForm v-model="cvIngest.draft" />
      </div>

      <aside class="cv-verify__sidebar">
        <div class="cv-verify__preview-card">
          <h3>Extracted text preview</h3>
          <pre>{{ uploadMeta?.text_preview }}</pre>
        </div>
        <div class="cv-verify__preview-card">
          <h3>Storage</h3>
          <p class="cv-verify__storage-uri">{{ uploadMeta?.storage_uri }}</p>
        </div>
      </aside>
    </div>

    <div v-if="error" class="cv-verify__error" role="alert">{{ error }}</div>
    <div v-if="success" class="cv-verify__success" role="status">{{ success }}</div>

    <div class="cv-verify__actions">
      <button type="button" class="cv-verify__btn cv-verify__btn--primary" :disabled="saving" @click="handleSave">
        {{ saving ? 'Saving…' : 'Save to Database' }}
      </button>
      <button type="button" class="cv-verify__btn cv-verify__btn--ghost" :disabled="saving" @click="handleDiscard">
        Discard &amp; Upload Another
      </button>
    </div>
  </div>
</template>

<style scoped>
.cv-verify__header {
  margin-bottom: 24px;
}

.cv-verify__header h2 {
  margin: 0 0 6px;
  font-family: var(--hrms-font-display);
  font-size: 1.75rem;
  color: var(--hrms-primary-dark);
}

.cv-verify__header p {
  margin: 0 0 12px;
  font-size: 0.9rem;
  color: var(--hrms-text-muted);
}

.cv-verify__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cv-verify__badge {
  padding: 4px 12px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--hrms-primary);
  background: var(--hrms-secondary);
  border-radius: 999px;
}

.cv-verify__badge--muted {
  color: var(--hrms-text-muted);
  background: var(--hrms-surface-muted);
}

.cv-verify__warnings {
  margin-bottom: 20px;
  padding: 14px 16px;
  font-size: 0.88rem;
  color: #7a5c00;
  background: #fff8e6;
  border: 1px solid #e8d49a;
  border-radius: var(--hrms-radius-md);
}

.cv-verify__warnings ul {
  margin: 8px 0 0;
  padding-left: 18px;
}

.cv-verify__layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  align-items: start;
}

.cv-verify__preview-card {
  margin-bottom: 16px;
  padding: 16px;
  background: var(--hrms-surface-elevated);
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-lg);
}

.cv-verify__preview-card h3 {
  margin: 0 0 10px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--hrms-primary-dark);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.cv-verify__preview-card pre {
  margin: 0;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--hrms-text-muted);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 360px;
  overflow-y: auto;
}

.cv-verify__storage-uri {
  margin: 0;
  font-size: 0.78rem;
  color: var(--hrms-text-muted);
  word-break: break-all;
}

.cv-verify__error {
  margin-top: 16px;
  padding: 12px 16px;
  font-size: 0.9rem;
  color: #9b3d5c;
  background: #fce8ef;
  border-radius: var(--hrms-radius-md);
}

.cv-verify__success {
  margin-top: 16px;
  padding: 12px 16px;
  font-size: 0.9rem;
  color: #2d6a3e;
  background: #e8f5ec;
  border-radius: var(--hrms-radius-md);
}

.cv-verify__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--hrms-border);
}

.cv-verify__btn {
  padding: 12px 24px;
  border-radius: var(--hrms-radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--hrms-transition);
}

.cv-verify__btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.cv-verify__btn--primary {
  border: none;
  color: #fff;
  background: linear-gradient(135deg, var(--hrms-primary) 0%, var(--hrms-primary-dark) 100%);
}

.cv-verify__btn--ghost {
  border: 1px solid var(--hrms-border-strong);
  color: var(--hrms-text-muted);
  background: transparent;
}

@media (max-width: 1024px) {
  .cv-verify__layout {
    grid-template-columns: 1fr;
  }
}
</style>

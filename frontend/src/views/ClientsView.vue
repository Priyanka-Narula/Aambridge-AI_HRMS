<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  createClient,
  fetchClients,
  updateClient,
  updateClientStatus,
} from '@/api/clients'
import HrmsAlert from '@/components/ui/HrmsAlert.vue'
import HrmsModal from '@/components/ui/HrmsModal.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import PageLayout from '@/components/ui/PageLayout.vue'
import type { ClientContactItem, ClientCreatePayload, ClientListItem, SubmissionField } from '@/types/clients'
import { avatarHue, initials } from '@/utils/format'

// ---------------------------------------------------------------------------
// System fields catalogue — derived from Candidate model + portal fields
// ---------------------------------------------------------------------------
interface SystemFieldDef {
  group: string
  key: string
  label: string
  type: string
}

const SYSTEM_FIELDS: SystemFieldDef[] = [
  // Personal
  { group: 'Personal', key: 'first_name', label: 'First Name', type: 'text' },
  { group: 'Personal', key: 'last_name', label: 'Last Name', type: 'text' },
  { group: 'Personal', key: 'email', label: 'Email', type: 'email' },
  { group: 'Personal', key: 'phone', label: 'Phone', type: 'text' },
  { group: 'Personal', key: 'nationality', label: 'Nationality', type: 'text' },
  { group: 'Personal', key: 'date_of_birth', label: 'Date of Birth', type: 'date' },
  { group: 'Personal', key: 'languages_known', label: 'Languages Known', type: 'text' },
  { group: 'Personal', key: 'visa_status', label: 'Visa Status', type: 'text' },
  // Location
  { group: 'Location', key: 'current_location', label: 'Current Location', type: 'text' },
  { group: 'Location', key: 'preferred_location', label: 'Preferred Location', type: 'text' },
  // Professional
  { group: 'Professional', key: 'total_experience_years', label: 'Total Experience (Years)', type: 'number' },
  { group: 'Professional', key: 'current_company', label: 'Current Company', type: 'text' },
  { group: 'Professional', key: 'current_designation', label: 'Current Designation', type: 'text' },
  { group: 'Professional', key: 'current_ctc', label: 'Current CTC', type: 'number' },
  { group: 'Professional', key: 'expected_ctc', label: 'Expected CTC', type: 'number' },
  { group: 'Professional', key: 'notice_period', label: 'Notice Period', type: 'text' },
  { group: 'Professional', key: 'linkedin_url', label: 'LinkedIn URL', type: 'url' },
  { group: 'Professional', key: 'skills', label: 'Skills', type: 'text' },
  { group: 'Professional', key: 'resume_url', label: 'Resume / CV', type: 'file' },
  // Education
  { group: 'Education', key: 'education_details', label: 'Education Details', type: 'section' },
  // Work History
  { group: 'Work History', key: 'work_experience', label: 'Work Experience', type: 'section' },
  // Client Portal
  { group: 'Client Portal', key: 'portal_status', label: 'Portal Status', type: 'text' },
  { group: 'Client Portal', key: 'role_applied_for', label: 'Role Applied For', type: 'text' },
  { group: 'Client Portal', key: 'availability_date', label: 'Availability Date', type: 'date' },
  { group: 'Client Portal', key: 'cover_letter', label: 'Cover Letter', type: 'textarea' },
  { group: 'Client Portal', key: 'custom_notes', label: 'Custom Notes', type: 'textarea' },
]

const SYSTEM_FIELD_GROUPS = [...new Set(SYSTEM_FIELDS.map((f) => f.group))]

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const clients = ref<ClientListItem[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const showDialog = ref(false)
const editingClient = ref<ClientListItem | null>(null)
const searchQuery = ref('')

// Track which system fields are selected (key → required)
const selectedFields = ref<Record<string, boolean>>({})

function emptyContact(): ClientContactItem {
  return { name: '', designation: null, email: null, phone: null, linkedin_url: null, primary_contact: false }
}

function emptyForm(): ClientCreatePayload {
  return {
    company_name: '',
    industry: null,
    location: null,
    website: null,
    company_size: null,
    billing_address: null,
    gst_number: null,
    payment_terms: null,
    portal_url: null,
    submission_format: null,
    contacts: [emptyContact()],
  }
}

const form = ref<ClientCreatePayload>(emptyForm())

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------
const filteredClients = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return clients.value
  return clients.value.filter(
    (c) =>
      c.company_name.toLowerCase().includes(q) ||
      (c.industry ?? '').toLowerCase().includes(q) ||
      (c.location ?? '').toLowerCase().includes(q),
  )
})

const modalTitle = computed(() =>
  editingClient.value ? `Edit — ${editingClient.value.company_name}` : 'Add Client',
)

// ---------------------------------------------------------------------------
// Template builder helpers
// ---------------------------------------------------------------------------
function isFieldSelected(key: string): boolean {
  return key in selectedFields.value
}

function toggleField(key: string) {
  if (key in selectedFields.value) {
    const copy = { ...selectedFields.value }
    delete copy[key]
    selectedFields.value = copy
  } else {
    selectedFields.value = { ...selectedFields.value, [key]: false }
  }
}

function setRequired(key: string, required: boolean) {
  selectedFields.value = { ...selectedFields.value, [key]: required }
}

function buildSubmissionFormat(): SubmissionField[] {
  return SYSTEM_FIELDS.filter((f) => isFieldSelected(f.key)).map((f) => ({
    field: f.label,
    type: f.type,
    required: selectedFields.value[f.key] ?? false,
  }))
}

function hydrateSelectedFields(fields: SubmissionField[] | null | undefined) {
  const map: Record<string, boolean> = {}
  if (!fields) return map
  for (const f of fields) {
    const def = SYSTEM_FIELDS.find((d) => d.label === f.field)
    if (def) map[def.key] = f.required
  }
  return map
}

// ---------------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------------
async function loadClients() {
  loading.value = true
  error.value = ''
  try {
    clients.value = await fetchClients()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load clients'
  } finally {
    loading.value = false
  }
}

onMounted(loadClients)

// ---------------------------------------------------------------------------
// Dialog open / close
// ---------------------------------------------------------------------------
function openCreate() {
  editingClient.value = null
  form.value = emptyForm()
  selectedFields.value = {}
  showDialog.value = true
}

function openEdit(client: ClientListItem) {
  editingClient.value = client
  form.value = {
    company_name: client.company_name,
    industry: client.industry ?? null,
    location: client.location ?? null,
    website: client.website ?? null,
    company_size: client.company_size ?? null,
    billing_address: client.billing_address ?? null,
    gst_number: client.gst_number ?? null,
    payment_terms: client.payment_terms ?? null,
    portal_url: client.portal_url ?? null,
    submission_format: client.submission_format ?? null,
    contacts:
      client.contacts.length > 0
        ? client.contacts.map((c) => ({ ...c }))
        : [emptyContact()],
  }
  selectedFields.value = hydrateSelectedFields(client.submission_format)
  showDialog.value = true
}

// ---------------------------------------------------------------------------
// Contact sub-form
// ---------------------------------------------------------------------------
function addContact() {
  form.value.contacts.push(emptyContact())
}

function removeContact(index: number) {
  form.value.contacts.splice(index, 1)
}

// ---------------------------------------------------------------------------
// Submit
// ---------------------------------------------------------------------------
async function submitClient() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const payload: ClientCreatePayload = {
      ...form.value,
      submission_format: buildSubmissionFormat().length > 0 ? buildSubmissionFormat() : null,
    }

    if (editingClient.value) {
      const updated = await updateClient(editingClient.value.id, payload)
      clients.value = clients.value.map((c) => (c.id === updated.id ? updated : c))
      success.value = `${updated.company_name} updated`
    } else {
      const created = await createClient(payload)
      clients.value = [created, ...clients.value]
      success.value = `${created.company_name} added`
    }
    showDialog.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to save client'
  } finally {
    saving.value = false
  }
}

// ---------------------------------------------------------------------------
// Status toggle
// ---------------------------------------------------------------------------
async function toggleStatus(client: ClientListItem) {
  const nextStatus = client.status === 'active' ? 'inactive' : 'active'
  error.value = ''
  try {
    const updated = await updateClientStatus(client.id, nextStatus)
    clients.value = clients.value.map((c) => (c.id === updated.id ? updated : c))
    success.value = `${updated.company_name} set to ${nextStatus}`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to update status'
  }
}
</script>

<template>
  <PageLayout>
    <PageHeader
      title="Client Management"
      subtitle="Manage client accounts, contacts, and submission templates"
      :count="`${clients.length} clients`"
      size="default"
    >
      <template #actions>
        <button type="button" class="hrms-btn hrms-btn--primary" @click="openCreate">
          Add Client
        </button>
      </template>
    </PageHeader>

    <HrmsAlert v-if="error" type="error" dismissible @dismiss="error = ''">
      {{ error }}
    </HrmsAlert>
    <HrmsAlert v-if="success" type="success" dismissible @dismiss="success = ''">
      {{ success }}
    </HrmsAlert>

    <!-- Search -->
    <div class="hrms-search-bar">
      <input
        v-model="searchQuery"
        class="hrms-input"
        type="search"
        placeholder="Search by company, industry or location…"
      />
    </div>

    <div v-if="loading" class="hrms-loading">Loading clients…</div>

    <div v-else class="hrms-list-stack">
      <article
        v-for="client in filteredClients"
        :key="client.id"
        class="hrms-card hrms-card--flat hrms-entity-card"
      >
        <div class="hrms-avatar" :style="`--hue: ${avatarHue(client.id)}`">
          {{ initials(client.company_name.split(' ')[0], client.company_name.split(' ')[1] ?? '') }}
        </div>

        <div class="hrms-entity-card__body">
          <div class="hrms-entity-card__name-row">
            <span class="hrms-entity-card__name">{{ client.company_name }}</span>
            <span
              class="hrms-status-badge"
              :style="`--sc: ${client.status === 'active' ? 'var(--hrms-success)' : 'var(--hrms-text-muted)'}`"
            >
              {{ client.status }}
            </span>
          </div>
          <div class="hrms-entity-card__role">
            {{ [client.industry, client.location].filter(Boolean).join(' · ') || 'No details' }}
          </div>
          <div class="hrms-entity-card__meta">
            <span v-if="client.company_size">{{ client.company_size }} employees</span>
            <span v-if="client.contacts.length">
              {{ client.contacts.length }} contact{{ client.contacts.length !== 1 ? 's' : '' }}
            </span>
            <a
              v-if="client.portal_url"
              :href="client.portal_url"
              target="_blank"
              rel="noopener noreferrer"
              class="hrms-link"
              @click.stop
            >
              Portal ↗
            </a>
          </div>
        </div>

        <div class="hrms-entity-card__aside">
          <button type="button" class="hrms-btn hrms-btn--sm" @click="openEdit(client)">
            Edit
          </button>
          <button
            type="button"
            class="hrms-btn hrms-btn--sm"
            :class="client.status === 'active' ? 'hrms-btn--danger' : 'hrms-btn--primary'"
            @click="toggleStatus(client)"
          >
            {{ client.status === 'active' ? 'Deactivate' : 'Activate' }}
          </button>
        </div>
      </article>

      <div v-if="filteredClients.length === 0" class="hrms-empty">
        <p v-if="searchQuery">No clients match "{{ searchQuery }}".</p>
        <p v-else>No clients yet. Add your first client.</p>
      </div>
    </div>

    <!-- ------------------------------------------------------------------ -->
    <!-- Create / Edit Modal                                                  -->
    <!-- ------------------------------------------------------------------ -->
    <HrmsModal v-model="showDialog" :title="modalTitle">

      <!-- Section 1: Company Info -->
      <div class="clients-section">
        <h3 class="clients-section__title">Company Information</h3>
        <div class="hrms-form-grid">
          <label class="hrms-field hrms-field--full">
            <span class="hrms-label">Company name <span class="hrms-required">*</span></span>
            <input v-model="form.company_name" class="hrms-input" type="text" required />
          </label>
          <label class="hrms-field">
            <span class="hrms-label">Industry</span>
            <input v-model="form.industry" class="hrms-input" type="text" />
          </label>
          <label class="hrms-field">
            <span class="hrms-label">Location</span>
            <input v-model="form.location" class="hrms-input" type="text" />
          </label>
          <label class="hrms-field">
            <span class="hrms-label">Website</span>
            <input v-model="form.website" class="hrms-input" type="url" placeholder="https://" />
          </label>
          <label class="hrms-field">
            <span class="hrms-label">Company size</span>
            <input v-model="form.company_size" class="hrms-input" type="text" placeholder="e.g. 50–200" />
          </label>
          <label class="hrms-field">
            <span class="hrms-label">GST number</span>
            <input v-model="form.gst_number" class="hrms-input" type="text" />
          </label>
          <label class="hrms-field">
            <span class="hrms-label">Payment terms</span>
            <input v-model="form.payment_terms" class="hrms-input" type="text" placeholder="e.g. Net 30" />
          </label>
          <label class="hrms-field hrms-field--full">
            <span class="hrms-label">Portal URL</span>
            <input
              v-model="form.portal_url"
              class="hrms-input"
              type="url"
              placeholder="https://client-portal.example.com"
            />
          </label>
          <label class="hrms-field hrms-field--full">
            <span class="hrms-label">Billing address</span>
            <textarea v-model="form.billing_address" class="hrms-input hrms-textarea" rows="2" />
          </label>
        </div>
      </div>

      <!-- Section 2: Contacts -->
      <div class="clients-section">
        <div class="clients-section__header">
          <h3 class="clients-section__title">Contacts</h3>
          <button type="button" class="hrms-btn hrms-btn--sm hrms-btn--primary" @click="addContact">
            + Add Contact
          </button>
        </div>

        <div
          v-for="(contact, idx) in form.contacts"
          :key="idx"
          class="clients-contact-row"
        >
          <div class="clients-contact-row__header">
            <span class="clients-contact-row__index">Contact {{ idx + 1 }}</span>
            <button
              v-if="form.contacts.length > 1"
              type="button"
              class="hrms-btn hrms-btn--sm hrms-btn--danger"
              @click="removeContact(idx)"
            >
              Remove
            </button>
          </div>
          <div class="hrms-form-grid">
            <label class="hrms-field">
              <span class="hrms-label">Name <span class="hrms-required">*</span></span>
              <input v-model="contact.name" class="hrms-input" type="text" required />
            </label>
            <label class="hrms-field">
              <span class="hrms-label">Designation</span>
              <input v-model="contact.designation" class="hrms-input" type="text" />
            </label>
            <label class="hrms-field">
              <span class="hrms-label">Email</span>
              <input v-model="contact.email" class="hrms-input" type="email" />
            </label>
            <label class="hrms-field">
              <span class="hrms-label">Phone</span>
              <input v-model="contact.phone" class="hrms-input" type="tel" />
            </label>
            <label class="hrms-field hrms-field--full">
              <span class="hrms-label">LinkedIn URL</span>
              <input v-model="contact.linkedin_url" class="hrms-input" type="url" placeholder="https://linkedin.com/in/…" />
            </label>
            <label class="hrms-field hrms-field--full hrms-field--inline">
              <input v-model="contact.primary_contact" class="hrms-checkbox" type="checkbox" />
              <span class="hrms-label">Primary contact</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Section 3: Template Builder -->
      <div class="clients-section">
        <h3 class="clients-section__title">Submission Template</h3>
        <p class="clients-section__desc">
          Select which candidate fields this client requires in a submission, and mark them as required if mandatory.
        </p>

        <div
          v-for="group in SYSTEM_FIELD_GROUPS"
          :key="group"
          class="clients-template-group"
        >
          <h4 class="clients-template-group__label">{{ group }}</h4>
          <div class="clients-template-fields">
            <div
              v-for="fieldDef in SYSTEM_FIELDS.filter((f) => f.group === group)"
              :key="fieldDef.key"
              class="clients-template-field"
              :class="{ 'clients-template-field--active': isFieldSelected(fieldDef.key) }"
            >
              <label class="clients-template-field__select">
                <input
                  type="checkbox"
                  class="hrms-checkbox"
                  :checked="isFieldSelected(fieldDef.key)"
                  @change="toggleField(fieldDef.key)"
                />
                <span>{{ fieldDef.label }}</span>
              </label>
              <label
                v-if="isFieldSelected(fieldDef.key)"
                class="clients-template-field__required"
              >
                <input
                  type="checkbox"
                  class="hrms-checkbox"
                  :checked="selectedFields[fieldDef.key]"
                  @change="setRequired(fieldDef.key, ($event.target as HTMLInputElement).checked)"
                />
                <span class="hrms-text-muted">Required</span>
              </label>
            </div>
          </div>
        </div>

        <p v-if="Object.keys(selectedFields).length === 0" class="clients-template-empty">
          No fields selected. Choose fields above to build the submission template.
        </p>
        <div v-else class="clients-template-preview">
          <span class="clients-template-preview__label">Template preview:</span>
          <span
            v-for="f in buildSubmissionFormat()"
            :key="f.field"
            class="clients-template-tag"
            :class="{ 'clients-template-tag--required': f.required }"
          >
            {{ f.field }}<template v-if="f.required"> *</template>
          </span>
        </div>
      </div>

      <template #footer>
        <button type="button" class="hrms-btn" @click="showDialog = false">Cancel</button>
        <button
          type="button"
          class="hrms-btn hrms-btn--primary"
          :disabled="saving"
          @click="submitClient"
        >
          {{ saving ? 'Saving…' : editingClient ? 'Save Changes' : 'Create Client' }}
        </button>
      </template>
    </HrmsModal>
  </PageLayout>
</template>

<style scoped>
.hrms-search-bar {
  margin-bottom: var(--hrms-space-4, 1rem);
}

.hrms-search-bar .hrms-input {
  max-width: 400px;
}

.hrms-link {
  color: var(--hrms-accent, #c4a35a);
  font-size: 0.8rem;
  text-decoration: none;
}

.hrms-link:hover {
  text-decoration: underline;
}

/* ---- Modal sections ---- */
.clients-section {
  margin-bottom: 2rem;
}

.clients-section:last-child {
  margin-bottom: 0;
}

.clients-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.clients-section__title {
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--hrms-text-muted, #888);
}

.clients-section__header .clients-section__title {
  margin-bottom: 0;
}

.clients-section__desc {
  margin: -0.25rem 0 0.75rem;
  font-size: 0.8rem;
  color: var(--hrms-text-muted, #888);
}

/* ---- Contacts ---- */
.clients-contact-row {
  border: 1px solid var(--hrms-border, #e5e7eb);
  border-radius: var(--hrms-radius-md, 8px);
  padding: 0.875rem;
  margin-bottom: 0.75rem;
  background: var(--hrms-surface-alt, #fafafa);
}

.clients-contact-row__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.clients-contact-row__index {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--hrms-text-muted, #888);
}

/* ---- Template builder ---- */
.clients-template-group {
  margin-bottom: 1rem;
}

.clients-template-group__label {
  margin: 0 0 0.4rem;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--hrms-text-muted, #888);
}

.clients-template-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.clients-template-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--hrms-border, #e5e7eb);
  border-radius: var(--hrms-radius-sm, 4px);
  font-size: 0.82rem;
  background: var(--hrms-surface, #fff);
  transition: border-color 0.15s, background 0.15s;
}

.clients-template-field--active {
  border-color: var(--hrms-accent, #c4a35a);
  background: color-mix(in srgb, var(--hrms-accent, #c4a35a) 8%, transparent);
}

.clients-template-field__select {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
}

.clients-template-field__required {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  padding-left: 0.5rem;
  border-left: 1px solid var(--hrms-border, #e5e7eb);
  cursor: pointer;
}

.clients-template-empty {
  font-size: 0.82rem;
  color: var(--hrms-text-muted, #888);
  font-style: italic;
  margin-top: 0.5rem;
}

.clients-template-preview {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: var(--hrms-surface-alt, #fafafa);
  border-radius: var(--hrms-radius-md, 8px);
  border: 1px solid var(--hrms-border, #e5e7eb);
}

.clients-template-preview__label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--hrms-text-muted, #888);
  margin-right: 0.25rem;
}

.clients-template-tag {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 99px;
  background: var(--hrms-surface, #fff);
  border: 1px solid var(--hrms-border, #e5e7eb);
  color: var(--hrms-text, #333);
}

.clients-template-tag--required {
  border-color: var(--hrms-accent, #c4a35a);
  color: var(--hrms-accent, #c4a35a);
  font-weight: 600;
}

/* ---- Form helpers ---- */
.hrms-field--inline {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.hrms-required {
  color: var(--hrms-danger, #dc2626);
}

.hrms-text-muted {
  color: var(--hrms-text-muted, #888);
}
</style>

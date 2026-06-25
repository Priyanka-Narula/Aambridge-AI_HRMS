<script setup lang="ts">
import type { CandidateDraft } from '@/types/candidate'

const draft = defineModel<CandidateDraft>({ required: true })

function addSkill() {
  draft.value.skills.push({ name: '' })
}

function removeSkill(index: number) {
  draft.value.skills.splice(index, 1)
}

function addEducation() {
  draft.value.education.push({ degree: '' })
}

function removeEducation(index: number) {
  draft.value.education.splice(index, 1)
}

function addExperience() {
  draft.value.work_experience.push({ company_name: '', currently_working: false })
}

function removeExperience(index: number) {
  draft.value.work_experience.splice(index, 1)
}
</script>

<template>
  <form class="verify-form" @submit.prevent>
    <section class="verify-form__section">
      <h3>Personal Information</h3>
      <div class="verify-form__grid">
        <label class="verify-form__field">
          <span>First name *</span>
          <input v-model="draft.first_name" type="text" required />
        </label>
        <label class="verify-form__field">
          <span>Last name *</span>
          <input v-model="draft.last_name" type="text" required />
        </label>
        <label class="verify-form__field">
          <span>Email *</span>
          <input v-model="draft.email" type="email" required />
        </label>
        <label class="verify-form__field">
          <span>Phone</span>
          <input v-model="draft.phone" type="tel" />
        </label>
        <label class="verify-form__field">
          <span>Nationality</span>
          <input v-model="draft.nationality" type="text" />
        </label>
        <label class="verify-form__field">
          <span>Date of birth</span>
          <input v-model="draft.date_of_birth" type="date" />
        </label>
        <label class="verify-form__field">
          <span>Languages</span>
          <input v-model="draft.languages_known" type="text" placeholder="English, Arabic" />
        </label>
        <label class="verify-form__field">
          <span>Visa status</span>
          <input v-model="draft.visa_status" type="text" />
        </label>
        <label class="verify-form__field verify-form__field--wide">
          <span>LinkedIn URL</span>
          <input v-model="draft.linkedin_url" type="url" />
        </label>
      </div>
    </section>

    <section class="verify-form__section">
      <h3>Professional Details</h3>
      <div class="verify-form__grid">
        <label class="verify-form__field">
          <span>Current location</span>
          <input v-model="draft.current_location" type="text" />
        </label>
        <label class="verify-form__field">
          <span>Preferred location</span>
          <input v-model="draft.preferred_location" type="text" />
        </label>
        <label class="verify-form__field">
          <span>Total experience (years)</span>
          <input v-model.number="draft.total_experience_years" type="number" step="0.1" min="0" />
        </label>
        <label class="verify-form__field">
          <span>Current company</span>
          <input v-model="draft.current_company" type="text" />
        </label>
        <label class="verify-form__field">
          <span>Current designation</span>
          <input v-model="draft.current_designation" type="text" />
        </label>
        <label class="verify-form__field">
          <span>Notice period</span>
          <input v-model="draft.notice_period" type="text" placeholder="30 days" />
        </label>
        <label class="verify-form__field">
          <span>Current CTC</span>
          <input v-model.number="draft.current_ctc" type="number" min="0" />
        </label>
        <label class="verify-form__field">
          <span>Expected CTC</span>
          <input v-model.number="draft.expected_ctc" type="number" min="0" />
        </label>
      </div>
    </section>

    <section class="verify-form__section">
      <div class="verify-form__section-head">
        <h3>Skills</h3>
        <button type="button" class="verify-form__add-btn" @click="addSkill">+ Add skill</button>
      </div>
      <div v-if="draft.skills.length === 0" class="verify-form__empty">No skills parsed</div>
      <div v-for="(skill, i) in draft.skills" :key="i" class="verify-form__row-card">
        <input v-model="skill.name" type="text" placeholder="Skill name" />
        <input v-model.number="skill.years_experience" type="number" step="0.1" placeholder="Years" />
        <input v-model="skill.proficiency_level" type="text" placeholder="Level" />
        <button type="button" class="verify-form__remove-btn" @click="removeSkill(i)">Remove</button>
      </div>
    </section>

    <section class="verify-form__section">
      <div class="verify-form__section-head">
        <h3>Education</h3>
        <button type="button" class="verify-form__add-btn" @click="addEducation">+ Add education</button>
      </div>
      <div v-if="draft.education.length === 0" class="verify-form__empty">No education parsed</div>
      <div v-for="(edu, i) in draft.education" :key="i" class="verify-form__row-card verify-form__row-card--stack">
        <input v-model="edu.degree" type="text" placeholder="Degree *" />
        <input v-model="edu.specialization" type="text" placeholder="Specialization" />
        <input v-model="edu.institution" type="text" placeholder="Institution" />
        <div class="verify-form__inline">
          <input v-model.number="edu.start_year" type="number" placeholder="Start year" />
          <input v-model.number="edu.end_year" type="number" placeholder="End year" />
          <input v-model.number="edu.percentage" type="number" step="0.01" placeholder="%" />
        </div>
        <button type="button" class="verify-form__remove-btn" @click="removeEducation(i)">Remove</button>
      </div>
    </section>

    <section class="verify-form__section">
      <div class="verify-form__section-head">
        <h3>Work Experience</h3>
        <button type="button" class="verify-form__add-btn" @click="addExperience">+ Add experience</button>
      </div>
      <div v-if="draft.work_experience.length === 0" class="verify-form__empty">No experience parsed</div>
      <div v-for="(exp, i) in draft.work_experience" :key="i" class="verify-form__row-card verify-form__row-card--stack">
        <input v-model="exp.company_name" type="text" placeholder="Company *" />
        <input v-model="exp.designation" type="text" placeholder="Designation" />
        <div class="verify-form__inline">
          <input v-model="exp.start_date" type="date" />
          <input v-model="exp.end_date" type="date" :disabled="exp.currently_working" />
          <label class="verify-form__check">
            <input v-model="exp.currently_working" type="checkbox" />
            Current
          </label>
        </div>
        <textarea v-model="exp.job_description" rows="2" placeholder="Job description" />
        <button type="button" class="verify-form__remove-btn" @click="removeExperience(i)">Remove</button>
      </div>
    </section>
  </form>
</template>

<style scoped>
.verify-form__section {
  margin-bottom: 28px;
  padding: 20px;
  background: var(--hrms-surface-elevated);
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-lg);
}

.verify-form__section h3 {
  margin: 0 0 16px;
  font-family: var(--hrms-font-display);
  font-size: 1.1rem;
  color: var(--hrms-primary-dark);
}

.verify-form__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.verify-form__section-head h3 {
  margin: 0;
}

.verify-form__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.verify-form__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.verify-form__field--wide {
  grid-column: 1 / -1;
}

.verify-form__field span {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--hrms-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.verify-form__field input,
.verify-form__row-card input,
.verify-form__row-card textarea {
  padding: 9px 12px;
  border: 1px solid var(--hrms-border);
  border-radius: var(--hrms-radius-sm);
  font-family: inherit;
  font-size: 0.9rem;
  color: var(--hrms-text);
  background: var(--hrms-surface);
}

.verify-form__field input:focus,
.verify-form__row-card input:focus,
.verify-form__row-card textarea:focus {
  outline: 2px solid var(--hrms-primary-muted);
  outline-offset: 1px;
}

.verify-form__row-card {
  display: grid;
  grid-template-columns: 1fr 100px 120px auto;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
  padding: 12px;
  background: var(--hrms-surface-muted);
  border-radius: var(--hrms-radius-sm);
}

.verify-form__row-card--stack {
  grid-template-columns: 1fr;
}

.verify-form__inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.verify-form__check {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: var(--hrms-text-muted);
}

.verify-form__add-btn {
  padding: 6px 12px;
  border: 1px solid var(--hrms-primary-muted);
  border-radius: var(--hrms-radius-sm);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--hrms-primary);
  background: transparent;
  cursor: pointer;
}

.verify-form__remove-btn {
  padding: 6px 10px;
  border: none;
  border-radius: var(--hrms-radius-sm);
  font-size: 0.78rem;
  color: #9b3d5c;
  background: #fce8ef;
  cursor: pointer;
}

.verify-form__empty {
  font-size: 0.85rem;
  color: var(--hrms-text-muted);
  font-style: italic;
}
</style>

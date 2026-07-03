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
  <form @submit.prevent>
    <section class="hrms-form-section">
      <h3 class="hrms-form-section__title">Personal Information</h3>
      <div class="hrms-form-grid">
        <label class="hrms-field">
          <span class="hrms-label">First name *</span>
          <input v-model="draft.first_name" class="hrms-input" type="text" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Last name *</span>
          <input v-model="draft.last_name" class="hrms-input" type="text" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Email *</span>
          <input v-model="draft.email" class="hrms-input" type="email" required />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Phone</span>
          <input v-model="draft.phone" class="hrms-input" type="tel" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Nationality</span>
          <input v-model="draft.nationality" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Date of birth</span>
          <input v-model="draft.date_of_birth" class="hrms-input" type="date" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Languages</span>
          <input v-model="draft.languages_known" class="hrms-input" type="text" placeholder="English, Arabic" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Visa status</span>
          <input v-model="draft.visa_status" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field hrms-field--wide">
          <span class="hrms-label">LinkedIn URL</span>
          <input v-model="draft.linkedin_url" class="hrms-input" type="url" />
        </label>
      </div>
    </section>

    <section class="hrms-form-section">
      <h3 class="hrms-form-section__title">Professional Details</h3>
      <div class="hrms-form-grid">
        <label class="hrms-field">
          <span class="hrms-label">Current location</span>
          <input v-model="draft.current_location" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Preferred location</span>
          <input v-model="draft.preferred_location" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Total experience (years)</span>
          <input v-model.number="draft.total_experience_years" class="hrms-input" type="number" step="0.1" min="0" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Current company</span>
          <input v-model="draft.current_company" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Current designation</span>
          <input v-model="draft.current_designation" class="hrms-input" type="text" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Notice period</span>
          <input v-model="draft.notice_period" class="hrms-input" type="text" placeholder="30 days" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Current CTC</span>
          <input v-model.number="draft.current_ctc" class="hrms-input" type="number" min="0" />
        </label>
        <label class="hrms-field">
          <span class="hrms-label">Expected CTC</span>
          <input v-model.number="draft.expected_ctc" class="hrms-input" type="number" min="0" />
        </label>
      </div>
    </section>

    <section class="hrms-form-section">
      <div class="hrms-form-section__head">
        <h3 class="hrms-form-section__title">Skills</h3>
        <button type="button" class="hrms-btn hrms-btn--sm hrms-btn--ghost" @click="addSkill">+ Add skill</button>
      </div>
      <div v-if="draft.skills.length === 0" class="hrms-empty-inline">No skills parsed</div>
      <div v-for="(skill, i) in draft.skills" :key="i" class="hrms-form-row">
        <input v-model="skill.name" class="hrms-input" type="text" placeholder="Skill name" />
        <input v-model.number="skill.years_experience" class="hrms-input" type="number" step="0.1" placeholder="Years" />
        <input v-model="skill.proficiency_level" class="hrms-input" type="text" placeholder="Level" />
        <button type="button" class="hrms-btn hrms-btn--sm hrms-btn--danger" @click="removeSkill(i)">Remove</button>
      </div>
    </section>

    <section class="hrms-form-section">
      <div class="hrms-form-section__head">
        <h3 class="hrms-form-section__title">Education</h3>
        <button type="button" class="hrms-btn hrms-btn--sm hrms-btn--ghost" @click="addEducation">+ Add education</button>
      </div>
      <div v-if="draft.education.length === 0" class="hrms-empty-inline">No education parsed</div>
      <div v-for="(edu, i) in draft.education" :key="i" class="hrms-form-row hrms-form-row--stack">
        <input v-model="edu.degree" class="hrms-input" type="text" placeholder="Degree *" />
        <input v-model="edu.specialization" class="hrms-input" type="text" placeholder="Specialization" />
        <input v-model="edu.institution" class="hrms-input" type="text" placeholder="Institution" />
        <div class="hrms-form-inline">
          <input v-model.number="edu.start_year" class="hrms-input" type="number" placeholder="Start year" />
          <input v-model.number="edu.end_year" class="hrms-input" type="number" placeholder="End year" />
          <input v-model.number="edu.percentage" class="hrms-input" type="number" step="0.01" placeholder="%" />
        </div>
        <button type="button" class="hrms-btn hrms-btn--sm hrms-btn--danger" @click="removeEducation(i)">Remove</button>
      </div>
    </section>

    <section class="hrms-form-section">
      <div class="hrms-form-section__head">
        <h3 class="hrms-form-section__title">Work Experience</h3>
        <button type="button" class="hrms-btn hrms-btn--sm hrms-btn--ghost" @click="addExperience">+ Add experience</button>
      </div>
      <div v-if="draft.work_experience.length === 0" class="hrms-empty-inline">No experience parsed</div>
      <div v-for="(exp, i) in draft.work_experience" :key="i" class="hrms-form-row hrms-form-row--stack">
        <input v-model="exp.company_name" class="hrms-input" type="text" placeholder="Company *" />
        <input v-model="exp.designation" class="hrms-input" type="text" placeholder="Designation" />
        <div class="hrms-form-inline">
          <input v-model="exp.start_date" class="hrms-input" type="date" />
          <input v-model="exp.end_date" class="hrms-input" type="date" :disabled="exp.currently_working" />
          <label class="hrms-check">
            <input v-model="exp.currently_working" type="checkbox" />
            Current
          </label>
        </div>
        <textarea v-model="exp.job_description" class="hrms-textarea" rows="2" placeholder="Job description" />
        <button type="button" class="hrms-btn hrms-btn--sm hrms-btn--danger" @click="removeExperience(i)">Remove</button>
      </div>
    </section>
  </form>
</template>

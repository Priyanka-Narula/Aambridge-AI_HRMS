<script setup lang="ts">
import { ref, computed } from 'vue'

// ── Types ────────────────────────────────────────────────────────────────────
interface Skill {
  name: string
  years_experience: number | null
  proficiency_level: string | null
}

interface Education {
  degree: string
  specialization: string | null
  institution: string | null
  start_year: number | null
  end_year: number | null
  percentage: number | null
}

interface WorkExperience {
  company_name: string
  designation: string | null
  start_date: string | null
  end_date: string | null
  currently_working: boolean
  job_description: string | null
}

interface Candidate {
  id: string
  first_name: string
  last_name: string
  email: string
  phone: string | null
  nationality: string | null
  date_of_birth: string | null
  languages_known: string | null
  visa_status: string | null
  linkedin_url: string | null
  current_location: string | null
  preferred_location: string | null
  total_experience_years: number | null
  current_company: string | null
  current_designation: string | null
  current_ctc: number | null
  expected_ctc: number | null
  notice_period: string | null
  resume_url: string | null
  candidate_status: string
  source: string | null
  created_by: string | null
  skills: Skill[]
  education_records: Education[]
  work_experiences: WorkExperience[]
}

// ── Mock data ─────────────────────────────────────────────────────────────────
const candidates = ref<Candidate[]>([
  {
    id: '1',
    first_name: 'Aisha',
    last_name: 'Nair',
    email: 'aisha.nair@email.com',
    phone: '+91 98765 43210',
    nationality: 'Indian',
    date_of_birth: '1995-04-12',
    languages_known: 'English, Malayalam, Hindi',
    visa_status: 'Citizen',
    linkedin_url: 'https://linkedin.com/in/aishanair',
    current_location: 'Bangalore, India',
    preferred_location: 'Bangalore, Hyderabad',
    total_experience_years: 6.5,
    current_company: 'Infosys',
    current_designation: 'Senior Software Engineer',
    current_ctc: 1800000,
    expected_ctc: 2400000,
    notice_period: '60 days',
    resume_url: '#',
    candidate_status: 'active',
    source: 'LinkedIn',
    created_by: 'hr@company.com',
    skills: [
      { name: 'React', years_experience: 4, proficiency_level: 'Expert' },
      { name: 'TypeScript', years_experience: 3, proficiency_level: 'Advanced' },
      { name: 'Node.js', years_experience: 3, proficiency_level: 'Intermediate' },
      { name: 'PostgreSQL', years_experience: 2, proficiency_level: 'Intermediate' },
    ],
    education_records: [
      { degree: 'B.Tech', specialization: 'Computer Science', institution: 'NIT Calicut', start_year: 2013, end_year: 2017, percentage: 82.4 },
    ],
    work_experiences: [
      { company_name: 'Infosys', designation: 'Senior Software Engineer', start_date: '2021-06-01', end_date: null, currently_working: true, job_description: 'Led a team of 5 engineers building internal React dashboards and REST APIs.' },
      { company_name: 'Wipro', designation: 'Software Engineer', start_date: '2017-08-01', end_date: '2021-05-31', currently_working: false, job_description: 'Full-stack development using Angular and Java Spring Boot.' },
    ],
  },
  {
    id: '2',
    first_name: 'Rahul',
    last_name: 'Menon',
    email: 'rahul.menon@email.com',
    phone: '+91 99887 76655',
    nationality: 'Indian',
    date_of_birth: '1992-11-30',
    languages_known: 'English, Malayalam',
    visa_status: 'Citizen',
    linkedin_url: null,
    current_location: 'Cochin, India',
    preferred_location: 'Remote',
    total_experience_years: 9,
    current_company: 'TCS',
    current_designation: 'Tech Lead',
    current_ctc: 2800000,
    expected_ctc: 3500000,
    notice_period: '90 days',
    resume_url: '#',
    candidate_status: 'interviewing',
    source: 'Referral',
    created_by: 'recruiter@company.com',
    skills: [
      { name: 'Java', years_experience: 9, proficiency_level: 'Expert' },
      { name: 'Spring Boot', years_experience: 7, proficiency_level: 'Expert' },
      { name: 'AWS', years_experience: 4, proficiency_level: 'Advanced' },
      { name: 'Kubernetes', years_experience: 2, proficiency_level: 'Intermediate' },
      { name: 'Kafka', years_experience: 3, proficiency_level: 'Advanced' },
    ],
    education_records: [
      { degree: 'M.Tech', specialization: 'Software Engineering', institution: 'CUSAT', start_year: 2013, end_year: 2015, percentage: 78 },
      { degree: 'B.Tech', specialization: 'Information Technology', institution: 'MG University', start_year: 2009, end_year: 2013, percentage: 74 },
    ],
    work_experiences: [
      { company_name: 'TCS', designation: 'Tech Lead', start_date: '2019-03-01', end_date: null, currently_working: true, job_description: 'Architecting microservices for a large banking client using Java and Kafka.' },
      { company_name: 'Cognizant', designation: 'Senior Developer', start_date: '2015-07-01', end_date: '2019-02-28', currently_working: false, job_description: 'Built REST APIs and batch processing pipelines.' },
    ],
  },
  {
    id: '3',
    first_name: 'Priya',
    last_name: 'Sharma',
    email: 'priya.sharma@gmail.com',
    phone: '+91 91234 56789',
    nationality: 'Indian',
    date_of_birth: '1998-07-22',
    languages_known: 'English, Hindi',
    visa_status: null,
    linkedin_url: 'https://linkedin.com/in/priyasharma',
    current_location: 'Mumbai, India',
    preferred_location: 'Mumbai, Pune',
    total_experience_years: 3.5,
    current_company: 'Accenture',
    current_designation: 'Data Analyst',
    current_ctc: 950000,
    expected_ctc: 1400000,
    notice_period: '30 days',
    resume_url: '#',
    candidate_status: 'offered',
    source: 'Naukri',
    created_by: 'hr@company.com',
    skills: [
      { name: 'Python', years_experience: 3, proficiency_level: 'Advanced' },
      { name: 'SQL', years_experience: 3.5, proficiency_level: 'Expert' },
      { name: 'Power BI', years_experience: 2, proficiency_level: 'Intermediate' },
      { name: 'Tableau', years_experience: 1, proficiency_level: 'Beginner' },
    ],
    education_records: [
      { degree: 'B.Sc', specialization: 'Statistics', institution: 'Mumbai University', start_year: 2016, end_year: 2019, percentage: 88 },
    ],
    work_experiences: [
      { company_name: 'Accenture', designation: 'Data Analyst', start_date: '2020-09-01', end_date: null, currently_working: true, job_description: 'Building dashboards and performing statistical analysis for FMCG clients.' },
    ],
  },
  {
    id: '4',
    first_name: 'Devika',
    last_name: 'Pillai',
    email: 'devika.pillai@email.com',
    phone: null,
    nationality: 'Indian',
    date_of_birth: '1990-03-08',
    languages_known: 'English, Malayalam, Tamil',
    visa_status: 'H-1B',
    linkedin_url: 'https://linkedin.com/in/devikapillai',
    current_location: 'San Francisco, USA',
    preferred_location: 'Remote / Bangalore',
    total_experience_years: 12,
    current_company: 'Google',
    current_designation: 'Staff Engineer',
    current_ctc: null,
    expected_ctc: null,
    notice_period: '90 days',
    resume_url: null,
    candidate_status: 'on_hold',
    source: 'Direct',
    created_by: 'director@company.com',
    skills: [
      { name: 'Go', years_experience: 5, proficiency_level: 'Expert' },
      { name: 'Distributed Systems', years_experience: 8, proficiency_level: 'Expert' },
      { name: 'gRPC', years_experience: 4, proficiency_level: 'Advanced' },
      { name: 'Spanner', years_experience: 3, proficiency_level: 'Advanced' },
    ],
    education_records: [
      { degree: 'M.S.', specialization: 'Computer Science', institution: 'Stanford University', start_year: 2013, end_year: 2015, percentage: null },
      { degree: 'B.Tech', specialization: 'Computer Science', institution: 'IIT Bombay', start_year: 2008, end_year: 2012, percentage: 91 },
    ],
    work_experiences: [
      { company_name: 'Google', designation: 'Staff Engineer', start_date: '2019-01-01', end_date: null, currently_working: true, job_description: 'Leading infra teams on large-scale distributed storage systems.' },
    ],
  },
])

// ── State ─────────────────────────────────────────────────────────────────────
const selected = ref<Candidate | null>(null)
const searchQuery = ref('')
const statusFilter = ref('all')
const showAddModal = ref(false)
const activeTab = ref<'overview' | 'experience' | 'education'>('overview')

// ── Computed ──────────────────────────────────────────────────────────────────
const filtered = computed(() => {
  return candidates.value.filter(c => {
    const q = searchQuery.value.toLowerCase()
    const matchesSearch =
      !q ||
      `${c.first_name} ${c.last_name}`.toLowerCase().includes(q) ||
      (c.current_designation ?? '').toLowerCase().includes(q) ||
      (c.current_company ?? '').toLowerCase().includes(q) ||
      c.skills.some(s => s.name.toLowerCase().includes(q))
    const matchesStatus =
      statusFilter.value === 'all' || c.candidate_status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

// ── Helpers ───────────────────────────────────────────────────────────────────
const statusMeta: Record<string, { label: string; color: string }> = {
  active:       { label: 'Active',       color: '#22c55e' },
  interviewing: { label: 'Interviewing', color: '#3b82f6' },
  offered:      { label: 'Offered',      color: '#a855f7' },
  on_hold:      { label: 'On Hold',      color: '#f59e0b' },
  rejected:     { label: 'Rejected',     color: '#ef4444' },
  hired:        { label: 'Hired',        color: '#14b8a6' },
}

const proficiencyMeta: Record<string, string> = {
  Beginner:     '#94a3b8',
  Intermediate: '#60a5fa',
  Advanced:     '#818cf8',
  Expert:       '#a78bfa',
}

const getStatus = (s: string) => statusMeta[s] ?? { label: s, color: '#94a3b8' }

const formatCtc = (v: number | null) => {
  if (v === null) return '—'
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`
  return `₹${v.toLocaleString('en-IN')}`
}

const formatDate = (d: string | null) => {
  if (!d) return 'Present'
  return new Date(d).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

const initials = (c: Candidate) =>
  `${c.first_name[0]}${c.last_name[0]}`.toUpperCase()

const avatarHue = (c: Candidate) => {
  let hash = 0
  for (const ch of c.id) hash = ch.charCodeAt(0) + ((hash << 5) - hash)
  return Math.abs(hash) % 360
}

const selectCandidate = (c: Candidate) => {
  selected.value = c
  activeTab.value = 'overview'
}

const closePanel = () => {
  selected.value = null
}

const statuses = ['all', 'active', 'interviewing', 'offered', 'on_hold', 'hired', 'rejected']
</script>

<template>
  <div class="candidates-root">

    <!-- ── Left: List pane ─────────────────────────────────────────────────── -->
    <div class="list-pane" :class="{ 'panel-open': selected }">

      <!-- Header -->
      <div class="list-header">
        <div class="list-header__top">
          <div>
            <h1 class="list-title">Candidates</h1>
            <span class="list-count">{{ filtered.length }} records</span>
          </div>
          <button class="btn-add" @click="showAddModal = true">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Add Candidate
          </button>
        </div>

        <!-- Search + Filter -->
        <div class="list-controls">
          <div class="search-wrap">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="7" cy="7" r="4.5" stroke="currentColor" stroke-width="1.5"/>
              <path d="M10.5 10.5L13 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <input
              v-model="searchQuery"
              class="search-input"
              placeholder="Search by name, role, skill…"
            />
          </div>
          <div class="status-tabs">
            <button
              v-for="s in statuses"
              :key="s"
              class="status-tab"
              :class="{ active: statusFilter === s }"
              @click="statusFilter = s"
            >
              {{ s === 'all' ? 'All' : getStatus(s).label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Cards -->
      <div class="card-list">
        <div
          v-for="c in filtered"
          :key="c.id"
          class="candidate-card"
          :class="{ selected: selected?.id === c.id }"
          @click="selectCandidate(c)"
        >
          <!-- Avatar -->
          <div
            class="avatar"
            :style="`--hue: ${avatarHue(c)}`"
          >{{ initials(c) }}</div>

          <!-- Main info -->
          <div class="card-body">
            <div class="card-name-row">
              <span class="card-name">{{ c.first_name }} {{ c.last_name }}</span>
              <span
                class="status-badge"
                :style="`--sc: ${getStatus(c.candidate_status).color}`"
              >{{ getStatus(c.candidate_status).label }}</span>
            </div>
            <div class="card-role">
              {{ c.current_designation ?? '—' }}
              <span v-if="c.current_company"> · {{ c.current_company }}</span>
            </div>
            <div class="card-meta">
              <span v-if="c.total_experience_years">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M6 3.5V6l1.5 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                {{ c.total_experience_years }}y exp
              </span>
              <span v-if="c.current_location">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1C4.067 1 2.5 2.567 2.5 4.5C2.5 7.125 6 11 6 11C6 11 9.5 7.125 9.5 4.5C9.5 2.567 7.933 1 6 1Z" stroke="currentColor" stroke-width="1.2"/>
                  <circle cx="6" cy="4.5" r="1" fill="currentColor"/>
                </svg>
                {{ c.current_location }}
              </span>
              <span v-if="c.notice_period">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <rect x="1" y="2" width="10" height="9" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M4 1v2M8 1v2M1 5h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                {{ c.notice_period }}
              </span>
            </div>
            <!-- Skills -->
            <div class="card-skills" v-if="c.skills.length">
              <span v-for="sk in c.skills.slice(0, 4)" :key="sk.name" class="skill-chip">
                {{ sk.name }}
              </span>
              <span v-if="c.skills.length > 4" class="skill-more">+{{ c.skills.length - 4 }}</span>
            </div>
          </div>

          <!-- CTC -->
          <div class="card-ctc">
            <div class="ctc-label">Current</div>
            <div class="ctc-value">{{ formatCtc(c.current_ctc) }}</div>
            <div class="ctc-label" style="margin-top: 8px">Expected</div>
            <div class="ctc-value expected">{{ formatCtc(c.expected_ctc) }}</div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="filtered.length === 0" class="empty-state">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="19" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3"/>
            <path d="M14 27c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="20" cy="16" r="3" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <p>No candidates match your filters.</p>
        </div>
      </div>
    </div>

    <!-- ── Right: Detail panel ─────────────────────────────────────────────── -->
    <Transition name="panel">
      <div v-if="selected" class="detail-panel">

        <!-- Panel header -->
        <div class="panel-header">
          <button class="panel-close" @click="closePanel">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>

          <div class="panel-hero">
            <div
              class="avatar avatar--lg"
              :style="`--hue: ${avatarHue(selected)}`"
            >{{ initials(selected) }}</div>
            <div>
              <h2 class="panel-name">{{ selected.first_name }} {{ selected.last_name }}</h2>
              <p class="panel-role">
                {{ selected.current_designation ?? 'No designation' }}
                <span v-if="selected.current_company"> · {{ selected.current_company }}</span>
              </p>
              <span
                class="status-badge status-badge--lg"
                :style="`--sc: ${getStatus(selected.candidate_status).color}`"
              >{{ getStatus(selected.candidate_status).label }}</span>
            </div>
          </div>

          <!-- Quick actions -->
          <div class="panel-actions">
            <a v-if="selected.resume_url" :href="selected.resume_url" class="action-btn action-btn--primary">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1v8M4 6l3 3 3-3M2 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Resume
            </a>
            <a v-if="selected.linkedin_url" :href="selected.linkedin_url" target="_blank" class="action-btn">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/>
                <path d="M4 6v4M4 4.5v.01M6.5 10V7.5c0-1 .5-1.5 1.5-1.5s1.5.5 1.5 1.5V10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              LinkedIn
            </a>
            <a :href="`mailto:${selected.email}`" class="action-btn">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
                <path d="M1 4.5l6 4 6-4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              Email
            </a>
          </div>
        </div>

        <!-- Tabs -->
        <div class="panel-tabs">
          <button
            class="panel-tab"
            :class="{ active: activeTab === 'overview' }"
            @click="activeTab = 'overview'"
          >Overview</button>
          <button
            class="panel-tab"
            :class="{ active: activeTab === 'experience' }"
            @click="activeTab = 'experience'"
          >Experience</button>
          <button
            class="panel-tab"
            :class="{ active: activeTab === 'education' }"
            @click="activeTab = 'education'"
          >Education</button>
        </div>

        <div class="panel-body">

          <!-- ── Overview tab ───────────────────────────────────────────────── -->
          <template v-if="activeTab === 'overview'">

            <!-- Contact & Personal -->
            <section class="info-section">
              <h3 class="section-title">Contact & Personal</h3>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Email</span>
                  <a :href="`mailto:${selected.email}`" class="info-value info-link">{{ selected.email }}</a>
                </div>
                <div class="info-item">
                  <span class="info-label">Phone</span>
                  <span class="info-value">{{ selected.phone ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Nationality</span>
                  <span class="info-value">{{ selected.nationality ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Date of Birth</span>
                  <span class="info-value">{{ selected.date_of_birth ? new Date(selected.date_of_birth).toLocaleDateString('en-IN') : '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Languages</span>
                  <span class="info-value">{{ selected.languages_known ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Visa Status</span>
                  <span class="info-value">{{ selected.visa_status ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Current Location</span>
                  <span class="info-value">{{ selected.current_location ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Preferred Location</span>
                  <span class="info-value">{{ selected.preferred_location ?? '—' }}</span>
                </div>
              </div>
            </section>

            <!-- Compensation & Availability -->
            <section class="info-section">
              <h3 class="section-title">Compensation & Availability</h3>
              <div class="ctc-cards">
                <div class="ctc-card">
                  <div class="ctc-card__label">Current CTC</div>
                  <div class="ctc-card__value">{{ formatCtc(selected.current_ctc) }}</div>
                </div>
                <div class="ctc-card ctc-card--accent">
                  <div class="ctc-card__label">Expected CTC</div>
                  <div class="ctc-card__value">{{ formatCtc(selected.expected_ctc) }}</div>
                </div>
                <div class="ctc-card">
                  <div class="ctc-card__label">Notice Period</div>
                  <div class="ctc-card__value">{{ selected.notice_period ?? '—' }}</div>
                </div>
              </div>
            </section>

            <!-- Skills -->
            <section class="info-section">
              <h3 class="section-title">Skills · {{ selected.skills.length }}</h3>
              <div class="skills-table" v-if="selected.skills.length">
                <div class="skills-table__row skills-table__row--header">
                  <span>Skill</span>
                  <span>Proficiency</span>
                  <span>Experience</span>
                </div>
                <div
                  v-for="sk in selected.skills"
                  :key="sk.name"
                  class="skills-table__row"
                >
                  <span class="skill-name">{{ sk.name }}</span>
                  <span
                    class="proficiency-chip"
                    :style="`--pc: ${proficiencyMeta[sk.proficiency_level ?? ''] ?? '#94a3b8'}`"
                  >{{ sk.proficiency_level ?? '—' }}</span>
                  <span class="skill-yrs">{{ sk.years_experience ? `${sk.years_experience}y` : '—' }}</span>
                </div>
              </div>
              <p v-else class="empty-inline">No skills recorded.</p>
            </section>

            <!-- Source & Meta -->
            <section class="info-section">
              <h3 class="section-title">Source & Meta</h3>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Source</span>
                  <span class="info-value">{{ selected.source ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Added by</span>
                  <span class="info-value">{{ selected.created_by ?? '—' }}</span>
                </div>
              </div>
            </section>
          </template>

          <!-- ── Experience tab ─────────────────────────────────────────────── -->
          <template v-else-if="activeTab === 'experience'">
            <section class="info-section">
              <h3 class="section-title">
                Work Experience
                <span class="section-badge">{{ selected.total_experience_years ? `${selected.total_experience_years}y total` : '' }}</span>
              </h3>
              <div class="timeline" v-if="selected.work_experiences.length">
                <div
                  v-for="(exp, i) in selected.work_experiences"
                  :key="i"
                  class="timeline-item"
                >
                  <div class="timeline-dot" :class="{ current: exp.currently_working }"></div>
                  <div class="timeline-content">
                    <div class="timeline-header">
                      <span class="timeline-company">{{ exp.company_name }}</span>
                      <span class="timeline-dates">
                        {{ formatDate(exp.start_date) }} – {{ exp.currently_working ? 'Present' : formatDate(exp.end_date) }}
                      </span>
                    </div>
                    <div class="timeline-role">{{ exp.designation ?? '—' }}</div>
                    <p v-if="exp.job_description" class="timeline-desc">{{ exp.job_description }}</p>
                  </div>
                </div>
              </div>
              <p v-else class="empty-inline">No work experience recorded.</p>
            </section>
          </template>

          <!-- ── Education tab ──────────────────────────────────────────────── -->
          <template v-else-if="activeTab === 'education'">
            <section class="info-section">
              <h3 class="section-title">Education</h3>
              <div class="edu-list" v-if="selected.education_records.length">
                <div
                  v-for="(ed, i) in selected.education_records"
                  :key="i"
                  class="edu-card"
                >
                  <div class="edu-card__degree">{{ ed.degree }}<span v-if="ed.specialization"> · {{ ed.specialization }}</span></div>
                  <div class="edu-card__inst">{{ ed.institution ?? '—' }}</div>
                  <div class="edu-card__meta">
                    <span v-if="ed.start_year || ed.end_year">{{ ed.start_year ?? '?' }} – {{ ed.end_year ?? 'Present' }}</span>
                    <span v-if="ed.percentage" class="edu-pct">{{ ed.percentage }}%</span>
                  </div>
                </div>
              </div>
              <p v-else class="empty-inline">No education records found.</p>
            </section>
          </template>

        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
/* ── Root layout ─────────────────────────────────────────────────────────────*/
.candidates-root {
  display: flex;
  height: 100%;
  min-height: 0;
  gap: 0;
  background: var(--hrms-bg, #f1f5f9);
  font-family: 'Inter', system-ui, sans-serif;
}

/* ── List pane ───────────────────────────────────────────────────────────────*/
.list-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  transition: flex 0.3s ease;
  overflow: hidden;
}
.list-pane.panel-open {
  flex: 0 0 55%;
}

.list-header {
  padding: 24px 24px 0;
  background: var(--hrms-bg, #f1f5f9);
  flex-shrink: 0;
}

.list-header__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.list-title {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--hrms-text-primary, #0f172a);
  letter-spacing: -0.02em;
  margin: 0 0 2px;
}

.list-count {
  font-size: 0.75rem;
  color: var(--hrms-text-muted, #94a3b8);
  font-weight: 500;
}

.btn-add {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #fff;
  background: var(--hrms-primary, #6366f1);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.btn-add:hover { background: var(--hrms-primary-dark, #4f46e5); }

/* Search */
.list-controls { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }

.search-wrap {
  position: relative;
}
.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--hrms-text-muted, #94a3b8);
}
.search-input {
  width: 100%;
  padding: 9px 12px 9px 36px;
  font-size: 0.8125rem;
  background: var(--hrms-surface, #fff);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 8px;
  color: var(--hrms-text-primary, #0f172a);
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.15s;
}
.search-input:focus { border-color: var(--hrms-primary, #6366f1); }
.search-input::placeholder { color: var(--hrms-text-muted, #94a3b8); }

/* Status tab strip */
.status-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.status-tab {
  padding: 5px 12px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 20px;
  background: transparent;
  color: var(--hrms-text-secondary, #64748b);
  cursor: pointer;
  transition: all 0.15s;
}
.status-tab:hover {
  background: var(--hrms-surface, #fff);
}
.status-tab.active {
  background: var(--hrms-primary, #6366f1);
  color: #fff;
  border-color: var(--hrms-primary, #6366f1);
}

/* ── Card list ───────────────────────────────────────────────────────────────*/
.card-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.candidate-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  background: var(--hrms-surface, #fff);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.candidate-card:hover {
  border-color: var(--hrms-primary, #6366f1);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--hrms-primary, #6366f1) 10%, transparent);
}
.candidate-card.selected {
  border-color: var(--hrms-primary, #6366f1);
  background: color-mix(in srgb, var(--hrms-primary, #6366f1) 4%, white);
}

/* Avatar */
.avatar {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: hsl(var(--hue, 250) 60% 88%);
  color: hsl(var(--hue, 250) 50% 35%);
  font-size: 0.875rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  letter-spacing: 0.02em;
}
.avatar--lg {
  width: 56px;
  height: 56px;
  font-size: 1.1rem;
  border-radius: 14px;
}

/* Card body */
.card-body { flex: 1; min-width: 0; }

.card-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 3px;
}
.card-name {
  font-size: 0.9rem;
  font-weight: 650;
  color: var(--hrms-text-primary, #0f172a);
}

.card-role {
  font-size: 0.78rem;
  color: var(--hrms-text-secondary, #64748b);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 8px;
}
.card-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--hrms-text-muted, #94a3b8);
}

.card-skills {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}
.skill-chip {
  padding: 2px 8px;
  font-size: 0.68rem;
  font-weight: 500;
  background: var(--hrms-surface-elevated, #f8fafc);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 4px;
  color: var(--hrms-text-secondary, #475569);
}
.skill-more {
  padding: 2px 8px;
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--hrms-primary, #6366f1);
  background: color-mix(in srgb, var(--hrms-primary, #6366f1) 8%, white);
  border-radius: 4px;
}

/* CTC */
.card-ctc {
  flex-shrink: 0;
  text-align: right;
}
.ctc-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--hrms-text-muted, #94a3b8);
  font-weight: 600;
}
.ctc-value {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--hrms-text-primary, #0f172a);
}
.ctc-value.expected {
  color: var(--hrms-primary, #6366f1);
}

/* Status badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 0.66rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 20px;
  color: var(--sc, #22c55e);
  background: color-mix(in srgb, var(--sc, #22c55e) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--sc, #22c55e) 25%, transparent);
}
.status-badge--lg {
  font-size: 0.72rem;
  padding: 3px 10px;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--hrms-text-muted, #94a3b8);
  font-size: 0.85rem;
}

/* ── Detail panel ────────────────────────────────────────────────────────────*/
.detail-panel {
  width: 45%;
  min-width: 380px;
  max-width: 520px;
  background: var(--hrms-surface, #fff);
  border-left: 1px solid var(--hrms-border, #e2e8f0);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-enter-active,
.panel-leave-active { transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s; }
.panel-enter-from,
.panel-leave-to { transform: translateX(32px); opacity: 0; }

.panel-header {
  padding: 20px 20px 0;
  background: var(--hrms-surface, #fff);
  border-bottom: 1px solid var(--hrms-border, #e2e8f0);
  flex-shrink: 0;
}

.panel-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: var(--hrms-surface-elevated, #f8fafc);
  border-radius: 6px;
  cursor: pointer;
  color: var(--hrms-text-muted, #94a3b8);
  margin-bottom: 16px;
  transition: background 0.15s;
}
.panel-close:hover { background: var(--hrms-border, #e2e8f0); }

.panel-hero {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.panel-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--hrms-text-primary, #0f172a);
  letter-spacing: -0.02em;
  margin: 0 0 4px;
}
.panel-role {
  font-size: 0.8rem;
  color: var(--hrms-text-secondary, #64748b);
  margin: 0 0 8px;
}

.panel-actions {
  display: flex;
  gap: 8px;
  padding-bottom: 16px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 6px;
  border: 1px solid var(--hrms-border, #e2e8f0);
  color: var(--hrms-text-secondary, #475569);
  background: var(--hrms-surface-elevated, #f8fafc);
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s;
}
.action-btn:hover { background: var(--hrms-border, #e2e8f0); }
.action-btn--primary {
  background: var(--hrms-primary, #6366f1);
  color: #fff;
  border-color: var(--hrms-primary, #6366f1);
}
.action-btn--primary:hover { background: var(--hrms-primary-dark, #4f46e5); }

/* Tabs */
.panel-tabs {
  display: flex;
  padding: 0 20px;
  background: var(--hrms-surface, #fff);
  border-bottom: 1px solid var(--hrms-border, #e2e8f0);
  flex-shrink: 0;
}
.panel-tab {
  padding: 12px 16px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--hrms-text-secondary, #64748b);
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
}
.panel-tab.active {
  color: var(--hrms-primary, #6366f1);
  border-bottom-color: var(--hrms-primary, #6366f1);
}

/* Panel body */
.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* Info sections */
.info-section { margin-bottom: 28px; }

.section-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--hrms-text-muted, #94a3b8);
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-badge {
  font-size: 0.68rem;
  font-weight: 600;
  background: color-mix(in srgb, var(--hrms-primary, #6366f1) 10%, transparent);
  color: var(--hrms-primary, #6366f1);
  padding: 1px 7px;
  border-radius: 10px;
  text-transform: none;
  letter-spacing: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.info-item { display: flex; flex-direction: column; gap: 3px; }
.info-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
  color: var(--hrms-text-muted, #94a3b8);
}
.info-value {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--hrms-text-primary, #0f172a);
}
.info-link { color: var(--hrms-primary, #6366f1); text-decoration: none; }
.info-link:hover { text-decoration: underline; }

/* CTC cards */
.ctc-cards { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }

.ctc-card {
  background: var(--hrms-surface-elevated, #f8fafc);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 10px;
  padding: 14px;
}
.ctc-card--accent {
  background: color-mix(in srgb, var(--hrms-primary, #6366f1) 6%, white);
  border-color: color-mix(in srgb, var(--hrms-primary, #6366f1) 20%, transparent);
}
.ctc-card--accent .ctc-card__value { color: var(--hrms-primary, #6366f1); }
.ctc-card__label {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
  color: var(--hrms-text-muted, #94a3b8);
  margin-bottom: 6px;
}
.ctc-card__value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--hrms-text-primary, #0f172a);
}

/* Skills table */
.skills-table { border: 1px solid var(--hrms-border, #e2e8f0); border-radius: 10px; overflow: hidden; }

.skills-table__row {
  display: grid;
  grid-template-columns: 1fr 120px 60px;
  padding: 10px 14px;
  align-items: center;
  border-bottom: 1px solid var(--hrms-border, #e2e8f0);
  font-size: 0.8rem;
}
.skills-table__row:last-child { border-bottom: none; }
.skills-table__row--header {
  font-size: 0.67rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--hrms-text-muted, #94a3b8);
  background: var(--hrms-surface-elevated, #f8fafc);
}

.skill-name { font-weight: 550; color: var(--hrms-text-primary, #0f172a); }
.skill-yrs { color: var(--hrms-text-secondary, #64748b); font-size: 0.77rem; }

.proficiency-chip {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 600;
  background: color-mix(in srgb, var(--pc, #94a3b8) 12%, transparent);
  color: color-mix(in srgb, var(--pc, #94a3b8) 80%, #000);
  border: 1px solid color-mix(in srgb, var(--pc, #94a3b8) 25%, transparent);
}

/* Timeline */
.timeline { display: flex; flex-direction: column; gap: 0; }
.timeline-item {
  display: flex;
  gap: 14px;
  position: relative;
}
.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 18px;
  bottom: -12px;
  width: 1px;
  background: var(--hrms-border, #e2e8f0);
}

.timeline-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--hrms-border, #e2e8f0);
  background: var(--hrms-surface, #fff);
  flex-shrink: 0;
  margin-top: 3px;
}
.timeline-dot.current {
  border-color: var(--hrms-primary, #6366f1);
  background: var(--hrms-primary, #6366f1);
}

.timeline-content {
  flex: 1;
  padding-bottom: 20px;
}
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 3px;
}
.timeline-company {
  font-size: 0.875rem;
  font-weight: 650;
  color: var(--hrms-text-primary, #0f172a);
}
.timeline-dates {
  font-size: 0.72rem;
  color: var(--hrms-text-muted, #94a3b8);
  white-space: nowrap;
}
.timeline-role {
  font-size: 0.78rem;
  color: var(--hrms-text-secondary, #64748b);
  margin-bottom: 6px;
}
.timeline-desc {
  font-size: 0.78rem;
  color: var(--hrms-text-secondary, #64748b);
  line-height: 1.55;
  margin: 0;
}

/* Education */
.edu-list { display: flex; flex-direction: column; gap: 10px; }
.edu-card {
  background: var(--hrms-surface-elevated, #f8fafc);
  border: 1px solid var(--hrms-border, #e2e8f0);
  border-radius: 10px;
  padding: 14px 16px;
}
.edu-card__degree {
  font-size: 0.875rem;
  font-weight: 650;
  color: var(--hrms-text-primary, #0f172a);
  margin-bottom: 4px;
}
.edu-card__inst {
  font-size: 0.8rem;
  color: var(--hrms-text-secondary, #64748b);
  margin-bottom: 8px;
}
.edu-card__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.75rem;
  color: var(--hrms-text-muted, #94a3b8);
}
.edu-pct {
  background: color-mix(in srgb, #22c55e 12%, transparent);
  color: #16a34a;
  padding: 1px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.72rem;
}

.empty-inline {
  font-size: 0.82rem;
  color: var(--hrms-text-muted, #94a3b8);
  margin: 0;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────────*/
.card-list::-webkit-scrollbar,
.panel-body::-webkit-scrollbar { width: 4px; }
.card-list::-webkit-scrollbar-track,
.panel-body::-webkit-scrollbar-track { background: transparent; }
.card-list::-webkit-scrollbar-thumb,
.panel-body::-webkit-scrollbar-thumb {
  background: var(--hrms-border, #e2e8f0);
  border-radius: 4px;
}
</style>
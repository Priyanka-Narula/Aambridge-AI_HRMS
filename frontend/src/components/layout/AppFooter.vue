<script setup lang="ts">
const currentYear = new Date().getFullYear()

withDefaults(
  defineProps<{
    variant?: 'default' | 'minimal'
  }>(),
  { variant: 'default' },
)
</script>

<template>
  <footer class="app-footer" :class="`app-footer--${variant}`">
    <div class="app-footer__inner">
      <p class="app-footer__copyright">
        &copy; {{ currentYear }} <strong>Aambridge AI HRMS</strong>. All rights reserved.
      </p>
      <nav v-if="variant === 'default'" class="app-footer__links" aria-label="Footer links">
        <a href="#">Privacy</a>
        <span class="app-footer__sep" aria-hidden="true">·</span>
        <a href="#">Terms</a>
        <span class="app-footer__sep" aria-hidden="true">·</span>
        <a href="#">Support</a>
      </nav>
      <p v-if="variant === 'default'" class="app-footer__tagline">
        Empowering women-led teams to hire with confidence
      </p>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  flex-shrink: 0;
  border-top: 1px solid var(--hrms-border);
  background: var(--hrms-surface-elevated);
}

.app-footer__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 24px;
  min-height: var(--hrms-footer-height);
  padding: 10px 24px;
}

.app-footer__copyright {
  margin: 0;
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
}

.app-footer__copyright strong {
  font-weight: 600;
  color: var(--hrms-primary);
}

.app-footer__links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-footer__links a {
  font-size: 0.8rem;
  color: var(--hrms-text-muted);
  transition: color var(--hrms-transition);
}

.app-footer__links a:hover {
  color: var(--hrms-primary);
}

.app-footer__sep {
  color: var(--hrms-border-strong);
}

.app-footer__tagline {
  margin: 0;
  width: 100%;
  font-size: 0.72rem;
  font-style: italic;
  color: var(--hrms-text-muted);
  text-align: center;
  opacity: 0.8;
}

.app-footer--minimal .app-footer__inner {
  justify-content: center;
}

@media (min-width: 768px) {
  .app-footer__tagline {
    width: auto;
    text-align: right;
    flex: 1;
  }
}
</style>

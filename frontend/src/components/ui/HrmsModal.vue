<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title: string
    size?: 'md' | 'lg' | 'xl'
  }>(),
  { size: 'md' },
)

const open = defineModel<boolean>({ required: true })

function close() {
  open.value = false
}

const sizeClass = computed(() => {
  if (props.size === 'xl') return 'hrms-modal--xl'
  if (props.size === 'lg') return 'hrms-modal--lg'
  return 'hrms-modal--md'
})
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="hrms-modal-overlay" @click.self="close">
      <div
        class="hrms-modal"
        :class="sizeClass"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <header class="hrms-modal__header">
          <h2 class="hrms-modal__title">{{ title }}</h2>
          <button type="button" class="hrms-modal__close" aria-label="Close" @click="close">
            x
          </button>
        </header>
        <div class="hrms-modal__body">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="hrms-modal__footer">
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>

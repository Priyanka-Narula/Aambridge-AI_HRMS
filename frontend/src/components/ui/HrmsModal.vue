<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    size?: 'md' | 'lg'
  }>(),
  { size: 'md' },
)

const open = defineModel<boolean>({ required: true })

function close() {
  open.value = false
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="hrms-modal-overlay" @click.self="close">
      <div
        class="hrms-modal"
        :class="size === 'lg' ? 'hrms-modal--lg' : 'hrms-modal--md'"
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

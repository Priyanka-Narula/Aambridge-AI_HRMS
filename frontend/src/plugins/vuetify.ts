import { designTokens } from '@/config/design-tokens'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const { colors } = designTokens

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'hrms',
    themes: {
      hrms: {
        dark: false,
        colors: {
          primary: colors.primary,
          secondary: colors.secondary,
          accent: colors.accent,
          error: colors.error,
          info: colors.textMuted,
          success: colors.success,
          warning: colors.accent,
          background: colors.surface,
          surface: colors.surfaceElevated,
        },
      },
    },
  },
})

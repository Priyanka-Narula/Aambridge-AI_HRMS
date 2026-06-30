import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'hrms',
    themes: {
      hrms: {
        dark: false,
        colors: {
          primary: '#7a3b68',
          secondary: '#f8f0f4',
          accent: '#c4a35a',
          error: '#9b3d5c',
          info: '#6b5f68',
          success: '#4a7c59',
          warning: '#c4a35a',
          background: '#fffbfa',
          surface: '#ffffff',
        },
      },
    },
  },
})

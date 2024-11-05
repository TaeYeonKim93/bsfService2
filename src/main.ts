import { createApp } from 'vue'
import App from './App.vue'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { createRouter, createWebHistory } from 'vue-router'
import Map from './components/Map.vue'
import MiniMap from './components/MiniMap.vue'
import RiskAnalysis from './components/RiskAnalysis.vue'
import '@mdi/font/css/materialdesignicons.css'

const vuetify = createVuetify({
  components,
  directives,
})

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Map
    },
    {
      path: '/map/mini',
      component: MiniMap
    },
    {
      path: '/risk',
      component: RiskAnalysis
    }
  ]
})

const app = createApp(App)
app.use(vuetify)
app.use(router)
app.mount('#app')

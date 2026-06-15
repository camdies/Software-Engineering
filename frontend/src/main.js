import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import axios from 'axios'

import App from './App.vue'
import router from './router'
import './styles/global.scss'

// DISABLE all network requests during initial render.
// The LoginView must NOT fire any API call on mount, and the router
// must NOT call useAuthStore() before Pinia is ready.
// Any Axios request that fires before the user clicks "Login" will
// block the JS thread (synchronous XMLHttpRequest), freeze the UI,
// and appear as "the login page is stuck and I can't type anything".
axios.defaults.baseURL = (typeof __API_BASE__ !== 'undefined') ? __API_BASE__ : '/api'

const app = createApp(App)

// Pinia MUST be installed before router, because the router's
// beforeEach guard calls useAuthStore() which depends on Pinia.
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// Global registration of Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')

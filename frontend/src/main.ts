import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router' // Import the router

import App from './App.vue'
import './assets/styles/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router) // Use the router

app.mount('#app')

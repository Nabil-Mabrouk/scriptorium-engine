import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from '@/router';
import App from '@/App.vue';
import BaseButton from '@/components/base/BaseButton.vue';
import '@/assets/styles/main.css';

const pinia = createPinia();
const app = createApp(App);

app.use(pinia);   // 1️⃣  FIRST
app.use(router);  // 2️⃣  SECOND

app.component('BaseButton', BaseButton); // now <BaseButton> works everywhere
app.mount('#app');


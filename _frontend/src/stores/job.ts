import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useJobStore = defineStore('job', () => {
  const status = ref<'queued' | 'running' | 'success' | 'error' | null>(null);
  return { status };
});
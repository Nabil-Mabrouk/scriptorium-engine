import { ref } from 'vue';
import api from '@/lib/api';

export function useJob() {
  const jobStatus = ref<'queued' | 'running' | 'success' | 'error'>('queued');

  const poll = async (jobId: string, interval = 2000) => {
    jobStatus.value = 'queued';
    const timer = setInterval(async () => {
      try {
        const { data } = await api.get(`/crew/status/${jobId}`); // endpoint you expose
        jobStatus.value = data.status;
        if (['success', 'error'].includes(data.status)) clearInterval(timer);
      } catch {
        jobStatus.value = 'error';
        clearInterval(timer);
      }
    }, interval);
  };

  return { jobStatus, poll };
}
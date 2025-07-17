// frontend/src/stores/task.ts

import { defineStore } from 'pinia';
import apiClient from '@/lib/api';
import { useProjectStore } from './project'; // We'll need this to refresh the project data

export const useTaskStore = defineStore('task', {
  state: () => ({
    // Using a Map to store interval IDs allows us to cancel them later
    activePolls: new Map<string, number>(),
  }),
  actions: {
    /**
     * Polls the job status endpoint until the job is complete or fails.
     * @param jobId The ID of the job to poll.
     * @param projectId The ID of the project to refresh upon completion.
     */

  pollJobStatus(jobId: string, projectId: string) {
    const projectStore = useProjectStore();

    const intervalId = window.setInterval(async () => {
      try {
        const response = await apiClient.get(`/crew/status/${jobId}`);
        const status = response.data.status;

        if (status === 'complete' || status === 'success') {
          clearInterval(intervalId);
          this.activePolls.delete(jobId);
          
          // On success, refresh the project and remove the processing ID
          projectStore.fetchProjectById(projectId);
          projectStore.processingIds.delete(projectId); // <-- ADD THIS LINE

        } else if (status === 'failed' || status === 'error') {
          clearInterval(intervalId);
          this.activePolls.delete(jobId);
          projectStore.processingIds.delete(projectId); // <-- ADD THIS LINE
          projectStore.error = `Job ${jobId} failed.`;
        }
      } catch (error) {
        clearInterval(intervalId);
        this.activePolls.delete(jobId);
        projectStore.processingIds.delete(projectId); // <-- ADD THIS LINE
      }
    }, 3000);

    this.activePolls.set(jobId, intervalId);
  },

  },
});
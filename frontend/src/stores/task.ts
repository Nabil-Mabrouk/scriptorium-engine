// frontend/src/stores/task.ts

import { defineStore } from 'pinia';
import apiClient from '@/lib/api';
import { useProjectStore } from './project'; // We'll need this to refresh the project data

// IMPORTER: Import TaskStatus from the auto-generated types.ts
import type { TaskStatus } from '@/lib/types';


export const useTaskStore = defineStore('task', {
  state: () => ({
    // Using a Map to store interval IDs allows us to cancel them later
    activePolls: new Map<string, number>(),
  }),
  actions: {
    /**
     * Polls the job status endpoint until the job is complete or fails.
     * @param jobId The ID of the job to poll.
     * @param entityIdToUpdateStatusFor The ID (project, part, or chapter) that was added to projectStore.processingIds.
     * @param projectIdToRefresh The ID of the overall project to refresh its data upon completion.
     */
    pollJobStatus(jobId: string, entityIdToUpdateStatusFor: string, projectIdToRefresh: string) {
      const projectStore = useProjectStore();

      const intervalId = window.setInterval(async () => {
        try {
          console.log(`Polling status for job: ${jobId}`);
          // Type the response data as TaskStatus
          const response = await apiClient.get<TaskStatus>(`/crew/status/${jobId}`);
          const status = response.data.status;

          if (status === 'complete' || status === 'success') {
            console.log(`Job ${jobId} completed successfully! Status: ${status}`);
            clearInterval(intervalId);
            this.activePolls.delete(jobId);
            
            // On success, refresh the project and remove the processing ID
            projectStore.fetchProjectById(projectIdToRefresh); // Refresh the entire project
            projectStore.processingIds.delete(entityIdToUpdateStatusFor); // Remove the specific entity ID

          } else if (status === 'failed' || status === 'error') {
            console.error(`Job ${jobId} failed. Status: ${status}`);
            clearInterval(intervalId);
            this.activePolls.delete(jobId);
            projectStore.processingIds.delete(entityIdToUpdateStatusFor); // Remove the specific entity ID
            projectStore.error = `Job ${jobId} failed. Error: ${response.data.error || 'Unknown error'}`; // Display error from backend if available
          }
        } catch (error: any) {
          console.error(`Error polling job ${jobId}:`, error);
          clearInterval(intervalId);
          this.activePolls.delete(jobId);
          projectStore.processingIds.delete(entityIdToUpdateStatusFor); // Clean up processing ID on polling error
          projectStore.error = error.message || `Failed to check status for job ${jobId}.`;
        }
      }, 3000); // Poll every 3 seconds

      this.activePolls.set(jobId, intervalId);
    },

    // Optionally, add a way to manually cancel a poll if needed
    cancelPoll(jobId: string) {
      const intervalId = this.activePolls.get(jobId);
      if (intervalId) {
        clearInterval(intervalId);
        this.activePolls.delete(jobId);
        console.log(`Polling for job ${jobId} cancelled manually.`);
      }
    }
  },
});
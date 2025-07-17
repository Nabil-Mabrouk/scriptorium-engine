import { defineStore } from 'pinia';
import apiClient from '@/lib/api'; // Use our centralized API client
import { useTaskStore } from './task'; // Import the new task store

// Define a type for our project - this should match your backend schema
interface Project {
  id: string;
  raw_blueprint: string;
  status: string;
  total_cost: string; // <-- FIX: Change from number to string
  // Add this field to match your backend data
  structured_outline?: { [key: string]: any } | null; 
}

// Add these types for clarity
interface Part {
  part_number: number;
  title: string;
  summary: string;
}

interface FinalizePartsPayload {
  parts: Part[];
}

// Add these new types for the chapter finalization payload
interface ChapterBrief {
  thesis_statement: string;
  narrative_arc: string;
  required_inclusions: string[];
  key_questions_to_answer: string[];
}
interface Chapter {
  chapter_number: number;
  title: string;
  brief: ChapterBrief;
  suggested_agent: string;
}
interface FinalizeChaptersPayload {
  chapters: Chapter[];
}

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [] as Project[],
    activeProject: null as Project | null, 
    isLoading: false,
    processingIds: new Set<string>(), // <-- It was declared here
    error: null as string | null,
    activePolls: new Map<string, number>(),
  }),
actions: {
       /**
     * Polls the job status endpoint until the job is complete or fails.
     * @param jobId The ID of the job to poll.
     * @param onComplete A callback function to run when the job is successful.
     */
    pollJobStatus(jobId: string, onComplete: () => void) {
      const intervalId = window.setInterval(async () => {
        try {
          console.log(`Polling status for job: ${jobId}`);
          const response = await apiClient.get(`/crew/status/${jobId}`);
          const status = response.data.status;

          if (status === 'complete' || status === 'success') {
            console.log(`Job ${jobId} completed successfully!`);
            clearInterval(intervalId);
            this.activePolls.delete(jobId);
            onComplete(); // Run the success callback
          } else if (status === 'failed' || status === 'error') {
            console.error(`Job ${jobId} failed.`);
            clearInterval(intervalId);
            this.activePolls.delete(jobId);
            // You can add error handling here, e.g., show a notification
          }
        } catch (error) {
          console.error(`Error polling job ${jobId}:`, error);
          clearInterval(intervalId);
          this.activePolls.delete(jobId);
        }
      }, 3000); // Poll every 3 seconds

      this.activePolls.set(jobId, intervalId);
    },

  // --- FETCH ACTIONS ---
  async fetchProjects() {
    this.isLoading = true;
    this.error = null;
    try {
      console.log(`➡️ [API Request] GET /projects`);
      const response = await apiClient.get('/projects');
      console.log(`✅ [API Response] Received ${response.data.length} projects.`);
      this.projects = response.data;
    } catch (err: any) {
      console.error(`❌ [API Error] Failed to fetch projects:`, err);
      this.error = err.message || 'Failed to fetch projects.';
    } finally {
      this.isLoading = false;
    }
  },

  async fetchProjectById(id: string) {
    this.isLoading = true;
    this.error = null;
    try {
      console.log(`➡️ [API Request] GET /projects/${id}`);
      const response = await apiClient.get(`/projects/${id}`);
      console.log(`✅ [API Response] Received project details:`, response.data);
      this.activeProject = response.data;
    } catch (err: any) {
      console.error(`❌ [API Error] Failed to fetch project ${id}:`, err);
      this.error = `Failed to fetch project ${id}.`;
    } finally {
      this.isLoading = false;
    }
  },

  // --- CREATE ACTION ---
  async createProject(blueprint: string) {
    this.isLoading = true;
    this.error = null;
    try {
      console.log(`➡️ [API Request] POST /projects with blueprint: "${blueprint.substring(0, 50)}..."`);
      await apiClient.post('/projects', { raw_blueprint: blueprint });
      console.log(`✅ [API Success] Project created. Refreshing project list...`);
      await this.fetchProjects(); 
    } catch (err: any) {
      console.error(`❌ [API Error] Failed to create project:`, err);
      this.error = err.message || 'Failed to create project.';
      throw err;
    } finally {
      this.isLoading = false;
    }
  },

  // --- GENERATION ACTIONS ---
  async generateParts(projectId: string) {
    this.processingIds.add(projectId); // Instantly mark as processing
    this.error = null;
    try {
      const response = await apiClient.post(`/crew/generate-parts/${projectId}`);
      const taskStore = useTaskStore();
      // Tell the task store to handle polling from here
      taskStore.pollJobStatus(response.data.job_id, projectId);
    } catch (err: any) {
      console.error(`❌ [API Error] Failed to start part generation for project ${projectId}:`, err);
      this.processingIds.delete(projectId); // Clean up on initial failure
    }
  },

  async generateChapters(partId: string) {
    const projectId = this.activeProject?.id;
    if (!projectId) return;

    this.processingIds.add(partId); // Mark part as processing
    this.error = null;
    try {
      const response = await apiClient.post(`/crew/generate-chapters/${partId}`);
      const taskStore = useTaskStore();
      taskStore.pollJobStatus(response.data.job_id, projectId);
    } catch (err: any) {
      console.error(`❌ [API Error] Failed to start chapter detailing for part ${partId}:`, err);
      this.processingIds.delete(partId);
    }
  },

  async generateChapterContent(chapterId: string) {
    const projectId = this.activeProject?.id;
    if (!projectId) return;

    this.processingIds.add(chapterId); // Mark chapter as processing
    this.error = null;
    try {
      const response = await apiClient.post(`/chapters/${chapterId}/generate`);
      const taskStore = useTaskStore();
      taskStore.pollJobStatus(response.data.job_id, projectId);
    } catch (err: any) {
      console.error(`❌ [API Error] Failed to generate content for chapter ${chapterId}:`, err);
      this.processingIds.delete(chapterId);
    }
  },

  // --- FINALIZE ACTIONS ---
  async finalizeParts(id: string, partsData: FinalizePartsPayload) {
    this.isLoading = true;
    try {
      console.log(`➡️ [API Request] PUT /projects/${id}/finalize-parts with payload:`, partsData);
      await apiClient.put(`/projects/${id}/finalize-parts`, partsData);
      console.log(`✅ [API Success] Parts finalized. Refreshing project data...`);
      await this.fetchProjectById(id);
    } catch (err: any) {
      console.error(`❌ [API Error] Failed to finalize parts for project ${id}:`, err);
      this.error = `Failed to finalize parts for project ${id}.`;
      throw err;
    } finally {
      this.isLoading = false;
    }
  },

  async finalizeChapters(partId: string, chaptersData: FinalizeChaptersPayload) {
    const projectId = this.activeProject?.id;
    if (!projectId) return;

    this.isLoading = true;
    try {
      console.log(`➡️ [API Request] PUT /parts/${partId}/finalize-chapters with payload:`, chaptersData);
      await apiClient.put(`/parts/${partId}/finalize-chapters`, chaptersData);
      console.log(`✅ [API Success] Chapters finalized for part ${partId}. Refreshing project data...`);
      await this.fetchProjectById(projectId);
    } catch (err: any) {
      this.error = `Failed to finalize chapters for part ${partId}.`;
      console.error(err);
      throw err;
    } finally {
      this.isLoading = false;
    }
  },
},
  getters: {
    projectCount: (state) => state.projects.length,
  },
});
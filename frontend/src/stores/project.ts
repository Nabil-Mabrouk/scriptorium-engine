import { defineStore } from 'pinia';
import apiClient from '@/lib/api'; // Use our centralized API client
import { useTaskStore } from './task'; // Import the new task store

// IMPORTER: Import all necessary types from the auto-generated types.ts
import type { 
  ProjectRead, 
  ProjectCreate, // For createProject payload
  ProjectDetailRead, // For activeProject
  PartRead, // Used in ProjectDetailRead's parts array
  ChapterRead, // Used in ProjectDetailRead's chapters array
  PartOnlyOutline, // Used for finalizeParts payload
  PartListOutline, // Used for finalizeParts payload
  ChapterOutline, // Used for finalizeChapters payload
  ChapterListOutline, // Used for finalizeChapters payload
  ChapterBrief, // Used within ChapterOutline
  TaskStatus // For API responses from task queuing
} from '@/lib/types';


export const useProjectStore = defineStore('project', {
  state: () => ({
    // Use ProjectRead for the projects list
    projects: [] as ProjectRead[],
    // Use ProjectDetailRead for the active project, as it contains nested parts and chapters
    activeProject: null as ProjectDetailRead | null, 
    isLoading: false,
    processingIds: new Set<string>(), 
    error: null as string | null,
    // REMOVED: activePolls is now managed solely by the task store
  }),
  actions: {
    // REMOVED: pollJobStatus action is now managed solely by the task store

    // --- FETCH ACTIONS ---
    async fetchProjects() {
      this.isLoading = true;
      this.error = null;
      try {
        console.log(`➡️ [API Request] GET /projects`);
        // Type the response data as an array of ProjectRead
        const response = await apiClient.get<ProjectRead[]>('/projects');
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
        // Type the response data as ProjectDetailRead
        const response = await apiClient.get<ProjectDetailRead>(`/projects/${id}`);
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
        // Payload type is ProjectCreate, response type is ProjectRead
        await apiClient.post<ProjectRead>('/projects', { raw_blueprint: blueprint } as ProjectCreate);
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
        // Response type is TaskStatus
        const response = await apiClient.post<TaskStatus>(`/crew/generate-parts/${projectId}`);
        const taskStore = useTaskStore();
        // Pass projectId for both entityIdToUpdateStatusFor and projectIdToRefresh
        taskStore.pollJobStatus(response.data.job_id, projectId, projectId);
      } catch (err: any) {
        console.error(`❌ [API Error] Failed to start part generation for project ${projectId}:`, err);
        this.processingIds.delete(projectId); // Clean up on initial failure
      }
    },

    async generateChapters(partId: string) {
      const projectId = this.activeProject?.id;
      if (!projectId) {
        console.warn('Cannot generate chapters: No active project found.');
        return;
      }

      this.processingIds.add(partId); // Mark part as processing
      this.error = null;
      try {
        // Response type is TaskStatus
        const response = await apiClient.post<TaskStatus>(`/crew/generate-chapters/${partId}`);
        const taskStore = useTaskStore();
        // Pass partId for entityIdToUpdateStatusFor, projectId for projectIdToRefresh
        taskStore.pollJobStatus(response.data.job_id, partId, projectId);
      } catch (err: any) {
        console.error(`❌ [API Error] Failed to start chapter detailing for part ${partId}:`, err);
        this.processingIds.delete(partId);
      }
    },

    async generateChapterContent(chapterId: string) {
      const projectId = this.activeProject?.id;
      if (!projectId) {
        console.warn('Cannot generate chapter content: No active project found.');
        return;
      }

      this.processingIds.add(chapterId); // Mark chapter as processing
      this.error = null;
      try {
        // Response type is TaskStatus
        const response = await apiClient.post<TaskStatus>(`/chapters/${chapterId}/generate`);
        const taskStore = useTaskStore();
        // Pass chapterId for entityIdToUpdateStatusFor, projectId for projectIdToRefresh
        taskStore.pollJobStatus(response.data.job_id, chapterId, projectId);
      } catch (err: any) {
        console.error(`❌ [API Error] Failed to generate content for chapter ${chapterId}:`, err);
        this.processingIds.delete(chapterId);
      }
    },

    // --- FINALIZE ACTIONS ---
    async finalizeParts(id: string, partsData: PartListOutline) {
      this.isLoading = true;
      try {
        console.log(`➡️ [API Request] PUT /projects/${id}/finalize-parts with payload:`, partsData);
        // Payload type is PartListOutline, response type is ProjectDetailRead
        await apiClient.put<ProjectDetailRead>(`/projects/${id}/finalize-parts`, partsData);
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

    async finalizeChapters(partId: string, chaptersData: ChapterListOutline) {
      const projectId = this.activeProject?.id;
      if (!projectId) {
        console.warn('Cannot finalize chapters: No active project found.');
        return;
      }

      this.isLoading = true;
      try {
        console.log(`➡️ [API Request] PUT /parts/${partId}/finalize-chapters with payload:`, chaptersData);
        // Payload type is ChapterListOutline, response type is PartReadWithChapters (implicitly handled by fetchProjectById)
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
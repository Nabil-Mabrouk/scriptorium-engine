import axios from 'axios';

// ----------  ADD THESE  ----------
export interface ProjectRead {
  id: string;
  raw_blueprint: string;
  status: string;
  structured_outline?: any;
  total_cost: number;
  parts?: any[];
}

export interface PartRead {
  id: string;
  part_number: number;
  title: string;
  summary?: string;
  chapters?: any[];
}

export interface ChapterRead {
  id: string;
  chapter_number: number;
  title: string;
  status: string;
  brief?: any;
  suggested_agent?: string;
}

// ----------  AXIOS INSTANCE  ----------
const api = axios.create({
  baseURL: import .meta.env.VITE_API_URL,
});

export default api;
export { api };

// ----------  API METHODS  ----------
export const fetchProjects = () => api.get<ProjectRead[]>('/projects').then(r => r.data);
export const fetchProject = (id: string) => api.get<ProjectRead>(`/projects/${id}`).then(r => r.data);
export const createProject = (raw_blueprint: string) =>
  api.post<ProjectRead>('/projects', { raw_blueprint }).then(r => r.data);
export const queueParts = (id: string) =>
  api.post(`/crew/generate-parts/${id}`).then(r => r.data);

export const finalizeParts = (id: string, body: any) =>
  api.put(`/projects/${id}/finalize-parts`, body).then(r => r.data);
export const generateChapters = (partId: string) =>
  api.post(`/crew/generate-chapters/${partId}`).then(r => r.data);
export const finalizeChapters = (partId: string, body: any) =>
  api.put(`/parts/${partId}/finalize-chapters`, body).then(r => r.data);

export const generateChapter = (chapterId: string) =>
  api.post(`/chapters/${chapterId}/generate`).then(r => r.data);
export const analyzeTransition = (chapterId: string) =>
  api.post(`/chapters/${chapterId}/analyze-transition`).then(r => r.data);

export const finalizeBook = (projectId: string, taskType: 'introduction' | 'conclusion') =>
  api.post(`/projects/${projectId}/finalize`, { task_type: taskType }).then(r => r.data);

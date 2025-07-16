import { defineStore } from 'pinia';
import { fetchProjects } from '@/lib/api';

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [] as Awaited<ReturnType<typeof fetchProjects>>,
  }),
  actions: {
    async load() {
      this.projects = await fetchProjects();
    },
  },
});
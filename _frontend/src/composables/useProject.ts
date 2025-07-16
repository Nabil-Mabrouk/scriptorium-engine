import { ref } from 'vue';
import { fetchProjects, createProject, queueParts } from '@/lib/api';

export function useProject() {
  const projects = ref<Awaited<ReturnType<typeof fetchProjects>>>([]);

  const load = async () => (projects.value = await fetchProjects());
  const add = async (raw: string) => {
    const created = await createProject(raw);
    projects.value.unshift(created);
    return created;
  };
  const generateParts = (id: string) => queueParts(id);

  return { projects, load, add, generateParts };
}
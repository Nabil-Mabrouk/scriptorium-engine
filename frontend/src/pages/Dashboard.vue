<template>
  <AppLayout>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-teal-400">Projects Dashboard</h1>
      <button @click="isModalOpen = true" class="px-4 py-2 rounded-md font-semibold bg-teal-600 hover:bg-teal-500 transition-colors">
        + New Project
      </button>
    </div>
    
    <div v-if="projectStore.isLoading && projectStore.projects.length === 0" class="text-center text-slate-400">Loading projects...</div>
    <div v-else>
       <div v-if="projectStore.projects.length === 0" class="p-6 bg-slate-800 rounded-lg text-center">
        <p class="font-semibold">No projects found.</p>
        <button @click="isModalOpen = true" class="mt-4 px-4 py-2 rounded-md font-semibold bg-teal-600 hover:bg-teal-500 transition-colors">
          Create Your First Book
        </button>
      </div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <ProjectCard 
          v-for="project in projectStore.projects" 
          :key="project.id" 
          :project="project"
        />
      </div>
    </div>
  </AppLayout>

  <ProjectCreateModal :visible="isModalOpen" @close="isModalOpen = false" />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AppLayout from '@/components/layout/AppLayout.vue';
import ProjectCard from '@/components/features/projects/ProjectCard.vue';
import ProjectCreateModal from '@/components/features/projects/ProjectCreateModal.vue'; // Import the modal
import { useProjectStore } from '@/stores/project';

const projectStore = useProjectStore();
const isModalOpen = ref(false); // Add state to control the modal

onMounted(() => {
  projectStore.fetchProjects();
});
</script>
<template>
  <div v-if="visible" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
    <div class="bg-slate-800 rounded-lg shadow-xl w-full max-w-2xl p-6 border border-slate-700">
      <h2 class="text-2xl font-bold text-teal-400 mb-4">Create New Book Project</h2>
      <p class="text-slate-400 mb-6">
        Describe your book idea below. This "raw blueprint" will be used by the AI agents to structure your book.
      </p>
      
      <form @submit.prevent="handleSubmit">
        <textarea
          v-model="blueprint"
          rows="10"
          class="w-full p-3 bg-slate-900 border border-slate-600 rounded-md focus:ring-2 focus:ring-teal-500 focus:outline-none"
          placeholder="e.g., A science fiction novel about the first contact with an alien civilization that communicates through music..."
        ></textarea>

        <div class="mt-6 flex justify-end gap-4">
          <button 
            type="button" 
            @click="closeModal"
            class="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600 transition-colors"
          >
            Cancel
          </button>
          <button 
            type="submit"
            :disabled="isLoading || !blueprint.trim()"
            class="px-4 py-2 rounded-md font-semibold bg-teal-600 hover:bg-teal-500 disabled:bg-slate-500 disabled:cursor-not-allowed transition-colors"
          >
            {{ isLoading ? 'Creating...' : 'Create Project' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useProjectStore } from '@/stores/project';

// Props to control visibility from the parent
defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
});

// Emits to communicate back to the parent
const emit = defineEmits(['close']);

const projectStore = useProjectStore();
const blueprint = ref('');
const isLoading = ref(false);

const closeModal = () => {
  emit('close');
};

const handleSubmit = async () => {
  if (!blueprint.value.trim()) return;

  isLoading.value = true;
  try {
    await projectStore.createProject(blueprint.value);
    blueprint.value = ''; // Clear the textarea
    closeModal(); // Close the modal on success
  } catch (error) {
    // Error is already logged in the store, you could add a UI notification here
    alert('Failed to create project. Please check the console.');
  } finally {
    isLoading.value = false;
  }
};
</script>
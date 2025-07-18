<template>
  <BaseModal :visible="visible" @close="closeModal" max-width="2xl">
    <template #header>
      <h2 class="text-2xl font-bold text-teal-400">Create New Book Project</h2>
    </template>

    <p class="text-slate-400 mb-6">
      Describe your book idea below. This "raw blueprint" will be used by the AI agents to structure your book.
    </p>
    
    <form @submit.prevent="handleSubmit">
      <textarea
        v-model="blueprint"
        rows="10"
        class="w-full p-3 bg-slate-900 border border-slate-600 rounded-md focus:ring-2 focus:ring-teal-500 focus:outline-none text-slate-200"
        placeholder="e.g., A science fiction novel about the first contact with an alien civilization that communicates through music..."
      ></textarea>
      <!-- Optional: Add a hidden submit button if you want the Enter key to still submit the form -->
      <button type="submit" class="hidden"></button>
    </form>

    <template #footer>
      <button 
        type="button" 
        @click="closeModal"
        class="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600 transition-colors"
      >
        Cancel
      </button>
      <button 
        type="button"  
        @click="handleSubmit" 
        :disabled="isLoading || !blueprint.trim()"
        class="px-4 py-2 rounded-md font-semibold bg-teal-600 hover:bg-teal-500 disabled:bg-slate-500 disabled:cursor-not-allowed transition-colors"
      >
        {{ isLoading ? 'Creating...' : 'Create Project' }}
      </button>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useProjectStore } from '@/stores/project';
import { useUiStore } from '@/stores/ui'; 
import BaseModal from '@/components/base/BaseModal.vue';

defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
});

const emit = defineEmits(['close']);

const projectStore = useProjectStore();
const uiStore = useUiStore();

const blueprint = ref('');
const isLoading = ref(false);

const closeModal = () => {
  emit('close');
};

const handleSubmit = async () => {
  if (!blueprint.value.trim()) {
    uiStore.showWarningToast('Please provide a book blueprint.');
    return;
  }

  isLoading.value = true;
  try {
    await projectStore.createProject(blueprint.value);
    blueprint.value = '';
    closeModal();
    uiStore.showSuccessToast('Project created successfully!');
  } catch (error: any) { 
    uiStore.showErrorToast(error.message || 'Failed to create project.');
  } finally {
    isLoading.value = false;
  }
};
</script>
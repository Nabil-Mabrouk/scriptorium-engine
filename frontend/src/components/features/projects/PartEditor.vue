<template>
  <div>
    <div v-for="(part, index) in editableParts" :key="index" class="mb-6 p-4 bg-slate-900/50 rounded-lg border border-slate-700">
      <div class="flex justify-between items-center mb-3">
        <label class="font-semibold text-slate-300">Part {{ part.part_number }}</label>
        <button @click="removePart(index)" class="text-red-400 hover:text-red-300 text-sm">Remove</button>
      </div>
      <div class="space-y-3">
        <!-- Using BaseInput for consistency is a good future refactor -->
        <input type="text" v-model="part.title" placeholder="Part Title" class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md focus:ring-2 focus:ring-teal-500 focus:outline-none">
        <textarea v-model="part.summary" placeholder="Part Summary" rows="3" class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md focus:ring-2 focus:ring-teal-500 focus:outline-none"></textarea>
      </div>
    </div>
    
    <div class="flex justify-between mt-6">
      <button @click="addPart" class="px-4 py-2 rounded-md font-semibold border border-slate-600 hover:bg-slate-700 transition-colors">
        + Add Part
      </button>
      <button 
        @click="submitFinalization" 
        class="px-6 py-2 rounded-md font-semibold bg-teal-600 hover:bg-teal-500 transition-colors"
        :disabled="projectStore.isLoading"
      >
        {{ projectStore.isLoading ? 'Finalizing...' : 'Finalize Part Structure' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useProjectStore } from '@/stores/project';
import { useUiStore } from '@/stores/ui'; // NEW: Import the ui store

import type { PartOnlyOutline, PartListOutline } from '@/lib/types';

const props = defineProps<{
  projectId: string;
  draftParts: PartListOutline; 
}>();

const projectStore = useProjectStore();
const uiStore = useUiStore(); // NEW: Initialize the ui store

const editableParts = ref<PartOnlyOutline[]>([]);

watch(() => props.draftParts, (newDraft) => {
  editableParts.value = JSON.parse(JSON.stringify(newDraft.parts || []));
}, { immediate: true, deep: true });

const addPart = () => {
  const nextPartNumber = editableParts.value.length > 0
    ? Math.max(...editableParts.value.map(p => p.part_number)) + 1
    : 1;
  editableParts.value.push({
    part_number: nextPartNumber,
    title: '',
    summary: '',
  });
};

const removePart = (index: number) => {
  editableParts.value.splice(index, 1);
};

const submitFinalization = async () => {
  const finalParts: PartListOutline = { 
    parts: editableParts.value.map((part, index) => ({
      ...part,
      part_number: index + 1,
    })),
  };

  // NEW: Use the custom confirmation dialog
  const confirmed = await uiStore.showConfirmation(
    'Finalize Part Structure',
    'Are you sure you want to finalize this structure? This will replace any existing parts and chapters for this project.',
    'Yes, Finalize', // Custom confirm button text
    'No, Cancel'      // Custom cancel button text
  );

  if (confirmed) {
    try {
      await projectStore.finalizeParts(props.projectId, finalParts);
      uiStore.showSuccessToast('Part structure finalized successfully!'); // Success toast
    } catch (error: any) {
      uiStore.showErrorToast(error.message || 'Failed to finalize part structure.'); // Error toast
    }
  } else {
    uiStore.showInfoToast('Part finalization cancelled.'); // Info toast for cancellation
  }
};
</script>
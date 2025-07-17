<template>
  <router-link v-if="project" :to="`/projects/${project.id}`">
    <div class="bg-slate-800 rounded-lg border border-slate-700 p-5 transition-all hover:border-teal-500/80 cursor-pointer h-full">
      <div class="flex flex-col h-full">
        <p class="text-slate-300 text-sm leading-relaxed flex-grow">
          {{ truncatedBlueprint }}
        </p>
        
        <div class="mt-4 pt-4 border-t border-slate-700 flex justify-between items-center">
          <span class="inline-block px-3 py-1 text-xs font-semibold rounded-full bg-teal-500/10 text-teal-400">
            {{ project.status }}
          </span>
          <span class="text-sm font-mono text-slate-400">
            ${{ parseFloat(project.total_cost).toFixed(4) }}
          </span>
        </div>
      </div>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { defineProps, computed } from 'vue';
import type { PropType } from 'vue';
import { RouterLink } from 'vue-router';

// This should be the same, corrected interface from your store
interface Project {
  id: string;
  raw_blueprint: string;
  status: string;
  total_cost: string; // Correctly typed as string
  structured_outline?: { [key: string]: any } | null;
}

const props = defineProps({
  project: {
    type: Object as PropType<Project>,
    required: true,
  },
});

// A defensive computed property to prevent errors
const truncatedBlueprint = computed(() => {
  const blueprint = props.project?.raw_blueprint || '';
  if (blueprint.length > 150) {
    return `${blueprint.substring(0, 150)}...`;
  }
  return blueprint;
});
</script>
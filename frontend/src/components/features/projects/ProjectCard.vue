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
import { computed } from 'vue';
import type { PropType } from 'vue'; // Keep PropType if using it for type inference (though directly importing is often cleaner)
import { RouterLink } from 'vue-router';

// IMPORTER: Import ProjectRead from the auto-generated types.ts
import type { ProjectRead } from '@/lib/types';

const props = defineProps({
  // Use the imported ProjectRead type
  project: {
    type: Object as PropType<ProjectRead>,
    required: true,
  },
});

const truncatedBlueprint = computed(() => {
  const blueprint = props.project?.raw_blueprint || '';
  if (blueprint.length > 150) {
    return `${blueprint.substring(0, 150)}...`;
  }
  return blueprint;
});
</script>
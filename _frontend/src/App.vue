<template>
  <div>
    <RouterView />
    <!-- Global job banner -->
    <div
      v-if="jobStore.status && jobStore.status !== 'success'"
      class="fixed top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow z-50"
    >
      Job: {{ jobStore.status }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useJobStore } from '@/stores/job';
const jobStore = useJobStore();
</script>
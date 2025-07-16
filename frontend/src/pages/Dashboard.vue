<template>
  <AppLayout>
    <h2 class="text-2xl mb-4">Projects</h2>

    <form @submit.prevent="create" class="mb-6">
      <textarea
        v-model="raw"
        rows="3"
        placeholder="Paste your book idea..."
        class="border rounded w-full p-2 mb-2"
      />
      <BaseButton type="submit">Create Project</BaseButton>
    </form>

    <ul class="space-y-4">
      <li
        v-for="p in projects"
        :key="p.id"
        class="p-4 border rounded flex justify-between items-center"
      >
        <div>
          <strong>{{ p.raw_blueprint.slice(0, 60) }}...</strong>
          <span class="text-sm text-gray-500 ml-2">{{ p.status }}</span>
        </div>
        <div class="space-x-2">
          <RouterLink :to="`/projects/${p.id}`">
            <BaseButton variant="secondary" size="sm">View</BaseButton>
          </RouterLink>
          <BaseButton size="sm" @click="generateParts(p.id)">Generate Parts</BaseButton>
        </div>
      </li>
    </ul>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import AppLayout from '@/components/layout/AppLayout.vue';
import BaseButton from '@/components/base/BaseButton.vue';
import { useProject } from '@/composables/useProject';

const { projects, load, add, generateParts } = useProject();
const raw = ref('');

const create = async () => {
  if (!raw.value.trim()) return;
  await add(raw.value);
  raw.value = '';
};

onMounted(load);
</script>
<template>
  <div v-if="open" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
    <div class="bg-white rounded p-6 w-full max-w-2xl">
      <h3 class="text-lg font-bold mb-2">Validate Parts</h3>
      <pre class="text-sm max-h-96 overflow-auto mb-4">{{ parts }}</pre>
      <div class="flex justify-end space-x-2">
        <BaseButton @click="$emit('save', parts)">Save</BaseButton>
        <BaseButton variant="secondary" @click="$emit('close')">Cancel</BaseButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ open: boolean; parts: any }>();
defineEmits(['save', 'close']);
</script>
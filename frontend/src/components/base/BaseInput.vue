<template>
  <input
    :type="type"
    :value="modelValue"
    @input="updateValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :class="[
      'w-full p-2 rounded-md transition-colors',
      'bg-slate-800 border border-slate-600', // Default styling
      'focus:ring-2 focus:ring-teal-500 focus:outline-none', // Focus styling
      { 'cursor-not-allowed opacity-60': disabled }, // Disabled styling
      customClass // Allow custom classes to be passed in
    ]"
  >
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  modelValue: string | number; // For v-model binding
  type?: string; // input type (text, number, email, password, etc.)
  placeholder?: string;
  disabled?: boolean;
  customClass?: string; // Optional: for passing additional Tailwind classes
}>();

const emit = defineEmits(['update:modelValue']);

// Helper to emit the updated value for v-model
const updateValue = (event: Event) => {
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.value);
};

// You can add more complex logic here if needed, e.g., validation via computed properties
// const isValid = computed(() => {
//   // Implement validation logic based on props.type or other rules
//   return true; // placeholder
// });
</script>

<style scoped>
/* No specific scoped styles needed if only using Tailwind CSS */
</style>
<template>
  <Transition name="modal-fade">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div
        class="bg-slate-800 rounded-lg shadow-xl border border-slate-700 w-full"
        :class="maxWidthClass"
        @click.stop
      >
        <!-- Modal Header -->
        <div v-if="$slots.header" class="px-6 pt-6 pb-4 border-b border-slate-700">
          <slot name="header"></slot>
        </div>

        <!-- Modal Body -->
        <div class="p-6">
          <slot></slot> <!-- Default slot for modal content -->
        </div>

        <!-- Modal Footer -->
        <div v-if="$slots.footer" class="px-6 pt-4 pb-6 border-t border-slate-700 flex justify-end gap-4">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  visible: boolean;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl' | '7xl';
}>();

// Define emits for controlling visibility from parent
const emit = defineEmits(['close']);

// Computed property for dynamic max-width classes
const maxWidthClass = computed(() => {
  switch (props.maxWidth) {
    case 'sm': return 'max-w-sm';
    case 'md': return 'max-w-md';
    case 'lg': return 'max-w-lg';
    case 'xl': return 'max-w-xl';
    case '2xl': return 'max-w-2xl';
    case '3xl': return 'max-w-3xl';
    case '4xl': return 'max-w-4xl';
    case '5xl': return 'max-w-5xl';
    case '6xl': return 'max-w-6xl';
    case '7xl': return 'max-w-7xl';
    default: return 'max-w-2xl'; // Default to 2xl if not specified
  }
});

// Optional: Close modal on backdrop click (add to main div if desired)
// function handleBackdropClick() {
//   emit('close');
// }
</script>

<style scoped>
/* Basic fade transition for the modal */
.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.3s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}
</style>
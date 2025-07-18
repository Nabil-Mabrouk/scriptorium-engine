<template>
  <Transition name="slide-fade">
    <div
      v-if="isVisible"
      :class="[
        'p-4 rounded-lg shadow-lg flex items-center justify-between space-x-4 min-w-[280px]',
        variantClasses[notification.type],
      ]"
    >
      <div class="flex-grow text-sm font-medium">
        {{ notification.message }}
      </div>
      <button @click="closeNotification" class="text-white/70 hover:text-white transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-x">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { Notification } from '@/stores/ui'; // Import the Notification interface

const props = defineProps<{
  notification: Notification;
}>();

const emit = defineEmits(['close']);

const isVisible = ref(true); // Control the fade-out transition

const variantClasses = {
  success: 'bg-green-600 text-white',
  error: 'bg-red-600 text-white',
  info: 'bg-blue-600 text-white',
  warning: 'bg-yellow-600 text-white', // Adjusted for better visibility
};

const closeNotification = () => {
  isVisible.value = false; // Trigger fade-out
  // Wait for animation to complete before emitting close to allow parent to remove from DOM
  setTimeout(() => {
    emit('close', props.notification.id);
  }, 300); // Match transition duration
};

// Auto-hide after duration if specified
onMounted(() => {
  if (props.notification.duration && props.notification.duration > 0) {
    setTimeout(closeNotification, props.notification.duration);
  }
});
</script>

<style scoped>
/* Slide-fade transition for notifications */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
<template>
  <div class="fixed bottom-4 right-4 z-[100] flex flex-col space-y-3 pointer-events-none">
    <BaseNotification
      v-for="notification in uiStore.notifications"
      :key="notification.id"
      :notification="notification"
      @close="uiStore.removeNotification(notification.id)"
      class="pointer-events-auto"
    />
  </div>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/ui';
import BaseNotification from '@/components/base/BaseNotification.vue'; // Import the individual notification component

const uiStore = useUiStore();
</script>

<style scoped>
/* No specific scoped styles needed, Tailwind provides layout */
</style>